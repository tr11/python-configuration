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


def config_from_env(
    prefix: str, separator: str = "__", *, lowercase_keys: bool = False
) -> Configuration:
    """
    Create a :class:`Configuration` instance from environment variables.

    :param prefix: prefix to filter environment variables with
    :param separator: separator to replace by dots
    :param lowercase_keys: whether to convert every key to lower case.
    :return: a :class:`Configuration` instance
    """
    result = {}
    for key, value in os.environ.items():
        if not key.startswith(prefix + separator):
            continue
        result[key[len(prefix) :].replace(separator, ".").strip(".")] = value

    return Configuration(result, lowercase_keys=lowercase_keys)


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
    path = os.path.normpath(path)
    if not os.path.exists(path) or not os.path.isdir(path):
        raise FileNotFoundError()

    dotted_path_levels = len(path.split("/"))
    files_keys = (
        (
            os.path.join(x[0], y),
            ".".join((x[0].split("/") + [y])[(dotted_path_levels + remove_level) :]),
        )
        for x in os.walk(path)
        for y in x[2]
        if not x[0].split("/")[-1].startswith("..")
    )

    result = {}
    for filename, key in files_keys:
        result[key] = open(filename).read()

    return Configuration(result, lowercase_keys=lowercase_keys)


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
           the :attr:`data` as the contents of the INI file.
    :param lowercase_keys: whether to convert every key to lower case.
    :return: a :class:`Configuration` instance
    """
    if read_from_file:
        if isinstance(data, str):
            return Configuration(json.load(open(data, "rt")))
        else:
            return Configuration(json.load(data), lowercase_keys=lowercase_keys)
    else:
        data = cast(str, data)
        return Configuration(json.loads(data), lowercase_keys=lowercase_keys)


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
    import configparser

    if read_from_file:
        if isinstance(data, str):
            data = open(data, "rt").read()
        else:
            data = data.read()
    data = cast(str, data)
    cfg = configparser.RawConfigParser()
    cfg.read_string(data)
    d = {
        section + "." + k: v
        for section, values in cfg.items()
        for k, v in values.items()
    }
    return Configuration(d, lowercase_keys=lowercase_keys)


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

    variables = [
        x for x in dir(module) if not x.startswith("__") and x.startswith(prefix)
    ]
    dict_ = {
        k[len(prefix) :].replace(separator, ".").strip("."): getattr(module, k)
        for k in variables
    }
    return Configuration(dict_, lowercase_keys=lowercase_keys)


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
        if read_from_file and isinstance(data, str):
            loaded = yaml.load(open(data, "rt"), Loader=yaml.FullLoader)
        else:
            loaded = yaml.load(data, Loader=yaml.FullLoader)
        if not isinstance(loaded, dict):
            raise ValueError("Data should be a dictionary")
        return Configuration(loaded, lowercase_keys=lowercase_keys)


if toml is not None:  # pragma: no branch

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
        if read_from_file:
            if isinstance(data, str):
                loaded = toml.load(open(data, "rt"))
            else:
                loaded = toml.load(data)
        else:
            data = cast(str, data)
            loaded = toml.loads(data)
        loaded = cast(dict, loaded)
        return Configuration(loaded, lowercase_keys=lowercase_keys)
