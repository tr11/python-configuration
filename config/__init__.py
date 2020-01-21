"""python-configuration module."""

import json
import os
from importlib.abc import InspectLoader
from types import ModuleType
from typing import IO, Iterable, Union, cast

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore
try:
    import toml
except ImportError:  # pragma: no cover
    toml = None  # type: ignore


from .configuration import Configuration
from .configuration_set import ConfigurationSet


def config(
    *configs: Iterable,
    prefix: str = "",
    remove_level: int = 1,
    lowercase_keys: bool = False,
    ignore_missing_paths: bool = False
) -> ConfigurationSet:
    """
    Create a :class:`ConfigurationSet` instance from an iterable of configs.

    :param configs: iterable of configurations
    :param prefix: prefix to filter environment variables with
    :param remove_level: how many levels to remove from the resulting config
    :param lowercase_keys: whether to convert every key to lower case.
    :param ignore_missing_paths: whether to ignore failures from missing files/folders.
    """
    instances = []
    for config_ in configs:
        if isinstance(config_, dict):
            instances.append(config_from_dict(config_, lowercase_keys=lowercase_keys))
            continue
        elif isinstance(config_, str):
            if config_.endswith(".py"):
                config_ = ("python", config_, prefix)
            elif config_.endswith(".json"):
                config_ = ("json", config_, True)
            elif yaml and config_.endswith(".yaml"):
                config_ = ("yaml", config_, True)
            elif toml and config_.endswith(".toml"):
                config_ = ("toml", config_, True)
            elif config_.endswith(".ini"):
                config_ = ("ini", config_, True)
            elif os.path.isdir(config_):
                config_ = ("path", config_, remove_level)
            elif config_ in ("env", "environment"):
                config_ = ("env", prefix)
            elif all(s and s.isidentifier() for s in config_.split(".")):
                config_ = ("python", config_, prefix)
            else:
                raise ValueError('Cannot determine config type from "%s"' % config_)

        if not isinstance(config_, (tuple, list)) or len(config_) == 0:
            raise ValueError(
                "configuration parameters must be a list of dictionaries,"
                " strings, or non-empty tuples/lists"
            )
        type_ = config_[0]
        if type_ == "dict":
            instances.append(
                config_from_dict(*config_[1:], lowercase_keys=lowercase_keys)
            )
        elif type_ in ("env", "environment"):
            params = config_[1:] if len(config_) > 1 else [prefix]
            instances.append(config_from_env(*params, lowercase_keys=lowercase_keys))
        elif type_ == "python":
            if len(config_) < 2:
                raise ValueError("No path specified for python module")
            params = config_[1:] if len(config_) > 2 else [config_[1], prefix]
            instances.append(config_from_python(*params, lowercase_keys=lowercase_keys))
        elif type_ == "json":
            try:
                instances.append(
                    config_from_json(*config_[1:], lowercase_keys=lowercase_keys)
                )
            except FileNotFoundError:
                if not ignore_missing_paths:
                    raise
        elif yaml and type_ == "yaml":
            try:
                instances.append(
                    config_from_yaml(*config_[1:], lowercase_keys=lowercase_keys)
                )
            except FileNotFoundError:
                if not ignore_missing_paths:
                    raise
        elif toml and type_ == "toml":
            try:
                instances.append(
                    config_from_toml(*config_[1:], lowercase_keys=lowercase_keys)
                )
            except FileNotFoundError:
                if not ignore_missing_paths:
                    raise
        elif type_ == "ini":
            try:
                instances.append(
                    config_from_ini(*config_[1:], lowercase_keys=lowercase_keys)
                )
            except FileNotFoundError:
                if not ignore_missing_paths:
                    raise
        elif type_ == "path":
            try:
                instances.append(
                    config_from_path(*config_[1:], lowercase_keys=lowercase_keys)
                )
            except FileNotFoundError:
                if not ignore_missing_paths:
                    raise
        else:
            raise ValueError('Unknown configuration type "%s"' % type_)

    return ConfigurationSet(*instances)


class EnvConfiguration(Configuration):
    """Configuration from Environment variables."""

    def __init__(
        self, prefix: str, separator: str = "__", *, lowercase_keys: bool = False
    ):
        """
        Constructor.

        :param prefix: prefix to filter environment variables with
        :param separator: separator to replace by dots
        :param lowercase_keys: whether to convert every key to lower case.
        """
        self._prefix = prefix
        self._separator = separator
        super().__init__({}, lowercase_keys=lowercase_keys)
        self.reload()

    def reload(self) -> None:
        """Reload the environment values."""
        result = {}
        for key, value in os.environ.items():
            if not key.startswith(self._prefix + self._separator):
                continue
            result[
                key[len(self._prefix) :].replace(self._separator, ".").strip(".")
            ] = value
        super().__init__(result, lowercase_keys=self._lowercase)


def config_from_env(
    prefix: str, separator: str = "__", *, lowercase_keys: bool = False
) -> Configuration:
    """
    Create a :class:`EnvConfiguration` instance from environment variables.

    :param prefix: prefix to filter environment variables with
    :param separator: separator to replace by dots
    :param lowercase_keys: whether to convert every key to lower case.
    :return: a :class:`Configuration` instance
    """
    return EnvConfiguration(prefix, separator, lowercase_keys=lowercase_keys)


class PathConfiguration(Configuration):
    """Configuration from a filessytem path."""

    def __init__(
        self, path: str, remove_level: int = 1, *, lowercase_keys: bool = False
    ):
        """
        Constructor.

        :param path: path to read from
        :param remove_level: how many levels to remove from the resulting config
        :param lowercase_keys: whether to convert every key to lower case.
        """
        self._path = path
        self._remove_level = remove_level
        super().__init__({}, lowercase_keys=lowercase_keys)
        self.reload()

    def reload(self) -> None:
        """Reload the path."""
        path = os.path.normpath(self._path)
        if not os.path.exists(path) or not os.path.isdir(path):
            raise FileNotFoundError()

        dotted_path_levels = len(path.split("/"))
        files_keys = (
            (
                os.path.join(x[0], y),
                ".".join(
                    (x[0].split("/") + [y])[(dotted_path_levels + self._remove_level) :]
                ),
            )
            for x in os.walk(path)
            for y in x[2]
            if not x[0].split("/")[-1].startswith("..")
        )

        result = {}
        for filename, key in files_keys:
            result[key] = open(filename).read()

        super().__init__(result, lowercase_keys=self._lowercase)


def config_from_path(
    path: str, remove_level: int = 1, *, lowercase_keys: bool = False
) -> Configuration:
    """
    Create a :class:`Configuration` instance from filesystem path.

    :param path: path to read from
    :param remove_level: how many levels to remove from the resulting config
    :param lowercase_keys: whether to convert every key to lower case.
    :return: a :class:`Configuration` instance
    """
    return PathConfiguration(path, remove_level, lowercase_keys=lowercase_keys)


class FileConfiguration(Configuration):
    """Configuration from a file input."""

    def __init__(
        self,
        data: Union[str, IO[str]],
        read_from_file: bool = False,
        *,
        lowercase_keys: bool = False
    ):
        """
        Constructor.

        :param data: path to a JSON file or contents
        :param read_from_file: whether to read from a file path or to interpret
               the :attr:`data` as the contents of the file.
        :param lowercase_keys: whether to convert every key to lower case.
        """
        super().__init__({}, lowercase_keys=lowercase_keys)
        self._reload(data, read_from_file)
        self._data = data if read_from_file and isinstance(data, str) else None

    def _reload(
        self, data: Union[str, IO[str]], read_from_file: bool = False
    ) -> None:  # pragma: no cover
        raise NotImplementedError()

    def reload(self) -> None:
        """Reload the configuration."""
        if self._data:  # pragma: no branch
            self._reload(self._data, True)


class JSONConfiguration(FileConfiguration):
    """Configuration from a JSON input."""

    def _reload(self, data: Union[str, IO[str]], read_from_file: bool = False) -> None:
        """Reload the JSON data."""
        if read_from_file:
            if isinstance(data, str):
                result = json.load(open(data, "rt"))
            else:
                result = json.load(data)
        else:
            result = json.loads(cast(str, data))
        self._config = self._flatten_dict(result)


def config_from_json(
    data: Union[str, IO[str]],
    read_from_file: bool = False,
    *,
    lowercase_keys: bool = False
) -> Configuration:
    """
    Create a :class:`Configuration` instance from a JSON file.

    :param data: path to a JSON file or contents
    :param read_from_file: whether to read from a file path or to interpret
           the :attr:`data` as the contents of the JSON file.
    :param lowercase_keys: whether to convert every key to lower case.
    :return: a :class:`Configuration` instance
    """
    return JSONConfiguration(data, read_from_file, lowercase_keys=lowercase_keys)


class INIConfiguration(FileConfiguration):
    """Configuration from an INI file input."""

    def _reload(self, data: Union[str, IO[str]], read_from_file: bool = False) -> None:
        """Reload the INI data."""
        import configparser

        if read_from_file:
            if isinstance(data, str):
                data = open(data, "rt").read()
            else:
                data = data.read()
        data = cast(str, data)
        cfg = configparser.RawConfigParser()
        cfg.read_string(data)
        result = {
            section + "." + k: v
            for section, values in cfg.items()
            for k, v in values.items()
        }
        self._config = self._flatten_dict(result)


def config_from_ini(
    data: Union[str, IO[str]],
    read_from_file: bool = False,
    *,
    lowercase_keys: bool = False
) -> Configuration:
    """
    Create a :class:`Configuration` instance from an INI file.

    :param data: path to an INI file or contents
    :param read_from_file: whether to read from a file path or to interpret
           the :attr:`data` as the contents of the INI file.
    :param lowercase_keys: whether to convert every key to lower case.
    :return: a :class:`Configuration` instance
    """
    return INIConfiguration(data, read_from_file, lowercase_keys=lowercase_keys)


class PythonConfiguration(Configuration):
    """Configuration from a python module."""

    def __init__(
        self,
        module: Union[str, ModuleType],
        prefix: str = "",
        separator: str = "_",
        *,
        lowercase_keys: bool = False
    ):
        """
        Constructor.

        :param module: a module or path string
        :param prefix: prefix to use to filter object names
        :param separator: separator to replace by dots
        :param lowercase_keys: whether to convert every key to lower case.
        """
        if isinstance(module, str):
            if module.endswith(".py"):
                import importlib.util

                spec = importlib.util.spec_from_file_location(module, module)
                module = importlib.util.module_from_spec(spec)
                spec.loader = cast(InspectLoader, spec.loader)
                spec.loader.exec_module(module)
            else:
                import importlib

                module = importlib.import_module(module)
        self._module = module
        self._prefix = prefix
        self._separator = separator
        super().__init__({}, lowercase_keys=lowercase_keys)
        self.reload()

    def reload(self) -> None:
        """Reload the path."""
        variables = [
            x
            for x in dir(self._module)
            if not x.startswith("__") and x.startswith(self._prefix)
        ]
        result = {
            k[len(self._prefix) :]
            .replace(self._separator, ".")
            .strip("."): getattr(self._module, k)
            for k in variables
        }
        super().__init__(result, lowercase_keys=self._lowercase)


def config_from_python(
    module: Union[str, ModuleType],
    prefix: str = "",
    separator: str = "_",
    *,
    lowercase_keys: bool = False
) -> Configuration:
    """
    Create a :class:`Configuration` instance from the objects in a Python module.

    :param module: a module or path string
    :param prefix: prefix to use to filter object names
    :param separator: separator to replace by dots
    :param lowercase_keys: whether to convert every key to lower case.
    :return: a :class:`Configuration` instance
    """
    return PythonConfiguration(module, prefix, separator, lowercase_keys=lowercase_keys)


def config_from_dict(data: dict, *, lowercase_keys: bool = False) -> Configuration:
    """
    Create a :class:`Configuration` instance from a dictionary.

    :param data: dictionary with string keys
    :param lowercase_keys: whether to convert every key to lower case.
    :return: a :class:`Configuration` instance
    """
    return Configuration(data, lowercase_keys=lowercase_keys)


def create_path_from_config(
    path: str, cfg: Configuration, remove_level: int = 1
) -> Configuration:
    """
    Output a path configuration from a :class:`Configuration` instance.

    :param path: path to create the config files in
    :param cfg: :class:`Configuration` instance
    :param remove_level: how many levels to remove
    """
    import os.path

    assert os.path.isdir(path)

    d = cfg.as_dict()
    for k, v in d.items():
        with open(os.path.join(path, k), "wb") as f:
            f.write(str(v).encode())

        cfg = config_from_path(path, remove_level=remove_level)
    return cfg


if yaml is not None:  # pragma: no branch

    class YAMLConfiguration(FileConfiguration):
        """Configuration from a YAML input."""

        def _reload(
            self, data: Union[str, IO[str]], read_from_file: bool = False
        ) -> None:
            """Reload the YAML data."""
            if read_from_file and isinstance(data, str):
                loaded = yaml.load(open(data, "rt"), Loader=yaml.FullLoader)
            else:
                loaded = yaml.load(data, Loader=yaml.FullLoader)
            if not isinstance(loaded, dict):
                raise ValueError("Data should be a dictionary")
            self._config = self._flatten_dict(loaded)

    def config_from_yaml(
        data: Union[str, IO[str]],
        read_from_file: bool = False,
        *,
        lowercase_keys: bool = False
    ) -> Configuration:
        """
        Return a Configuration instance from YAML files.

        :param data: string or file
        :param read_from_file: whether `data` is a file or a YAML formatted string
        :param lowercase_keys: whether to convert every key to lower case.
        :return: a Configuration instance
        """
        return YAMLConfiguration(data, read_from_file, lowercase_keys=lowercase_keys)


if toml is not None:  # pragma: no branch

    class TOMLConfiguration(FileConfiguration):
        """Configuration from a TOML input."""

        def _reload(
            self, data: Union[str, IO[str]], read_from_file: bool = False
        ) -> None:
            """Reload the TOML data."""
            if read_from_file:
                if isinstance(data, str):
                    loaded = toml.load(open(data, "rt"))
                else:
                    loaded = toml.load(data)
            else:
                data = cast(str, data)
                loaded = toml.loads(data)
            loaded = cast(dict, loaded)
            self._config = self._flatten_dict(loaded)

    def config_from_toml(
        data: Union[str, IO[str]],
        read_from_file: bool = False,
        *,
        lowercase_keys: bool = False
    ) -> Configuration:
        """
        Return a Configuration instance from TOML files.

        :param data: string or file
        :param read_from_file: whether `data` is a file or a TOML formatted string
        :param lowercase_keys: whether to convert every key to lower case.
        :return: a Configuration instance
        """
        return TOMLConfiguration(data, read_from_file, lowercase_keys=lowercase_keys)
