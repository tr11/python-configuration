"""python-configuration module."""

import base64
import json
import os
from importlib.abc import InspectLoader
from types import ModuleType
from typing import Any, Dict, IO, ItemsView, Iterable, KeysView, List, Mapping, Union, ValuesView, cast

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore
try:
    import toml
except ImportError:  # pragma: no cover
    toml = None  # type: ignore


TRUTH_TEXT = frozenset(('t', 'true', 'y', 'yes', 'on', '1'))
FALSE_TEXT = frozenset(('f', 'false', 'n', 'no', 'off', '0', ''))


def as_bool(s: Any) -> bool:
    """
    Boolean value from an object.

    Return the boolean value ``True`` if the case-lowered value of string
    input ``s`` is a `truthy string`. If ``s`` is already one of the
    boolean values ``True`` or ``False``, return it.
    """
    if s is None:
        return False
    if isinstance(s, bool):
        return s
    s = str(s).strip().lower()
    if s not in TRUTH_TEXT and s not in FALSE_TEXT:
        raise ValueError("Expected a valid True or False expression.")
    return s in TRUTH_TEXT


class Configuration:
    """
    Configuration class.

    The Configuration class takes a dictionary input with keys such as

        - ``a1.b1.c1``
        - ``a1.b1.c2``
        - ``a1.b2.c1``
        - ``a1.b2.c2``
        - ``a2.b1.c1``
        - ``a2.b1.c2``
        - ``a2.b2.c1``
        - ``a2.b2.c2``
    """

    def __init__(self, config_: Mapping[str, Any]):
        """
        Constructor.

        :param config_: a mapping of configuration values. Keys need to be strings.
        """
        self._config: Dict[str, Any] = self._flatten_dict(config_)

    def __eq__(self, other):  # type: ignore
        """Equality operator."""
        return self.as_dict() == other.as_dict()

    def _filter_dict(self, d: Dict[str, Any], prefix: str) -> Dict[str, Any]:
        """
        Filter a dictionary and return the items that are prefixed by :attr:`prefix`.

        :param d: dictionary
        :param prefix: prefix to filter on
        """
        return {k[(len(prefix) + 1):].lower(): v for k, v in d.items() if k.startswith(prefix + '.')}

    def _flatten_dict(self, d: Mapping[str, Any]) -> Dict[str, Any]:
        """
        Flatten one level of a dictionary.

        :param d: dict
        :return: a flattened dict
        """
        nested = {k for k, v in d.items() if isinstance(v, dict)}
        result = {k.lower() + '.' + ki: vi
                  for k in nested
                  for ki, vi in self._flatten_dict(d[k]).items()}
        result.update((k.lower(), v) for k, v in d.items() if not isinstance(v, dict))
        return result

    def _get_subset(self, prefix: str) -> Union[Dict[str, Any], Any]:
        """
        Return the subset of the config dictionary whose keys start with :attr:`prefix`.

        :param prefix: string
        :return: dict
        """
        d = {k[(len(prefix) + 1):]: v for k, v in self._config.items() if k.startswith(prefix + '.')}
        if not d:
            prefixes = prefix.split('.')
            if len(prefixes) == 1:
                return self._config.get(prefix, {})
            d = self._config
            while prefixes:  # pragma: no branches
                p = prefixes[0]
                new_d = self._filter_dict(d, p)
                if new_d == {}:
                    return d.get(p, {}) if len(prefixes) == 1 else {}
                d = new_d
                prefixes = prefixes[1:]
        return d

    def __getitem__(self, item: str) -> Union['Configuration', Any]:                                        # noqa: D105
        v = self._get_subset(item)
        if v == {}:
            raise KeyError(item)
        return Configuration(v) if isinstance(v, dict) else v

    def __getattr__(self, item: str) -> Any:                                                                # noqa: D105
        v = self._get_subset(item)
        if v == {}:
            raise KeyError(item)
        return Configuration(v) if isinstance(v, dict) else v

    def get(self, key: str, default: Any = None) -> Union[dict, Any]:
        """
        Get the configuration values corresponding to :attr:`key`.

        :param key: key to retrieve
        :param default: default value in case the key is missing
        :return: the value found or a default
        """
        return self.as_dict().get(key, default)

    def as_dict(self) -> dict:
        """Return the representation as a dictionary."""
        return self._config

    def get_bool(self, item: str) -> bool:
        """
        Get the item value as a bool.

        :param item: key
        """
        return as_bool(self[item])

    def get_str(self, item: str, fmt: str = '{}') -> str:
        """
        Get the item value as an int.

        :param item: key
        :param fmt: format to use
        """
        return fmt.format(self[item])

    def get_int(self, item: str) -> int:
        """
        Get the item value as an int.

        :param item: key
        """
        return int(self[item])

    def get_float(self, item: str) -> float:
        """
        Get the item value as a float.

        :param item: key
        """
        return float(self[item])

    def get_dict(self, item: str) -> dict:
        """
        Get the item values as a dictionary.

        :param item: key
        """
        return dict(self._get_subset(item))

    def base64encode(self, item: str) -> bytes:
        """
        Get the item value as a Base64 encoded bytes instance.

        :param item: key
        """
        b = self[item]
        b = b if isinstance(b, bytes) else b.encode()
        return base64.b64encode(b)

    def base64decode(self, item: str) -> bytes:
        """
        Get the item value as a Base64 decoded bytes instance.

        :param item: key
        """
        b = self[item]
        b = b if isinstance(b, bytes) else b.encode()
        return base64.b64decode(b, validate=True)

    def keys(self) -> Union['Configuration', Any, KeysView[str]]:
        """Return a set-like object providing a view on the configuration keys."""
        try:
            return self['keys']
        except KeyError:
            return self.as_dict().keys()

    def values(self) -> Union['Configuration', Any, ValuesView[Any]]:
        """Return a set-like object providing a view on the configuration values."""
        try:
            return self['values']
        except KeyError:
            return self.as_dict().values()

    def items(self) -> Union['Configuration', Any, ItemsView[str, Any]]:
        """Return a set-like object providing a view on the configuration items."""
        try:
            return self['items']
        except KeyError:
            return self.as_dict().items()

    def __repr__(self) -> str:                                                                              # noqa: D105
        return "<Configuration: %r>" % self._config


class ConfigurationSet(Configuration):
    """
    Configuration Sets.

    A class that combines multiple :class:`Configuration` instances in a hierarchical manner.
    """

    def __init__(self, *configs: Configuration):                                                            # noqa: D107
        try:
            self._configs: List[Configuration] = list(configs)
        except Exception:  # pragma: no cover
            raise ValueError('configs should be a non-empty iterable of Configuration objects')
        if not self._configs:  # pragma: no cover
            raise ValueError('configs should be a non-empty iterable of Configuration objects')
        if not all(isinstance(x, Configuration) for x in self._configs):   # pragma: no cover
            raise ValueError('configs should be a non-empty iterable of Configuration objects')

    def _from_configs(self, attr: str, *args: Any, **kwargs: dict) -> Any:
        last_err = Exception()
        values = []
        for config_ in self._configs:
            try:
                values.append(getattr(config_, attr)(*args, **kwargs))
            except Exception as err:
                last_err = err
                continue
        if not values:
            # raise the last error
            raise last_err
        if all(isinstance(v, Configuration) for v in values):
            result: dict = {}
            for v in values[::-1]:
                result.update(v)
            return Configuration(result)
        elif isinstance(values[0], Configuration):
            result = {}
            for v in values[::-1]:
                if not isinstance(v, Configuration):
                    continue
                result.update(v)
            return Configuration(result)
        else:
            return values[0]

    def __getitem__(self, item: str) -> Union[Configuration, Any]:                                          # noqa: D105
        return self._from_configs('__getitem__', item)

    def __getattr__(self, item: str) -> Union[Configuration, Any]:                                          # noqa: D105
        return self._from_configs('__getattr__', item)

    def get(self, key: str, default: Any = None) -> Union[dict, Any]:
        """
        Get the configuration values corresponding to :attr:`key`.

        :param key: key to retrieve
        :param default: default value in case the key is missing
        :return: the value found or a default
        """
        try:
            return self[key]
        except Exception:
            return default

    def as_dict(self) -> dict:
        """Return the representation as a dictionary."""
        result = {}
        for config_ in self._configs[::-1]:
            result.update(config_.as_dict())
        return result

    def get_dict(self, item: str) -> dict:
        """
        Get the item values as a dictionary.

        :param item: key
        """
        return dict(self[item])

    def __repr__(self) -> str:                                                                              # noqa: D105
        return "<ConfigurationSet %r>" % self.as_dict()


def config(*configs: Iterable, prefix: str = '', remove_level: int = 1) -> ConfigurationSet:
    """
    Create a :class:`ConfigurationSet` instance from an iterable of configs.

    :param configs: iterable of configurations
    :param prefix: prefix to filter environment variables with
    :param remove_level: how many levels to remove from the resulting config
    """
    instances = []
    for config_ in configs:
        if isinstance(config_, dict):
            instances.append(config_from_dict(config_))
            continue
        elif isinstance(config_, str):
            if config_.endswith('.py'):
                config_ = ('python', config_, prefix)
            elif config_.endswith('.json'):
                config_ = ('json', config_, True)
            elif yaml and config_.endswith('.yaml'):
                config_ = ('yaml', config_, True)
            elif toml and config_.endswith('.toml'):
                config_ = ('toml', config_, True)
            elif config_.endswith('.ini'):
                config_ = ('ini', config_, True)
            elif os.path.isdir(config_):
                config_ = ('path', config_, remove_level)
            elif config_ in ('env', 'environment'):
                config_ = ('env', prefix)
            elif all(s and s.isidentifier() for s in config_.split('.')):
                config_ = ('python', config_, prefix)
            else:
                raise ValueError('Cannot determine config type from "%s"' % config_)

        if not isinstance(config_, (tuple, list)) or len(config_) == 0:
            raise ValueError(
                'configuration parameters must be a list of dictionaries, strings, or non-empty tuples/lists'
            )
        type_ = config_[0]
        if type_ == 'dict':
            instances.append(config_from_dict(*config_[1:]))
        elif type_ in ('env', 'environment'):
            params = config_[1:] if len(config_) > 1 else [prefix]
            instances.append(config_from_env(*params))
        elif type_ == 'python':
            if len(config_) < 2:
                raise ValueError("No path specified for python module")
            params = config_[1:] if len(config_) > 2 else [config_[1], prefix]
            instances.append(config_from_python(*params))
        elif type_ == 'json':
            instances.append(config_from_json(*config_[1:]))
        elif yaml and type_ == 'yaml':
            instances.append(config_from_yaml(*config_[1:]))
        elif toml and type_ == 'toml':
            instances.append(config_from_toml(*config_[1:]))
        elif type_ == 'ini':
            instances.append(config_from_ini(*config_[1:]))
        elif type_ == 'path':
            instances.append(config_from_path(*config_[1:]))
        else:
            raise ValueError('Unknown configuration type "%s"' % type_)

    return ConfigurationSet(*instances)


def config_from_env(prefix: str, separator: str = '__') -> Configuration:
    """
    Create a :class:`Configuration` instance from environment variables.

    :param prefix: prefix to filter environment variables with
    :param separator: separator to replace by dots
    :return: a :class:`Configuration` instance
    """
    result = {}
    for key, value in os.environ.items():
        if not key.startswith(prefix + separator):
            continue
        result[key[len(prefix):].replace(separator, '.').strip('.')] = value

    return Configuration(result)


def config_from_path(path: str, remove_level: int = 1) -> Configuration:
    """
    Create a :class:`Configuration` instance from filesystem path.

    :param path: path to read from
    :param remove_level: how many levels to remove from the resulting config
    :return: a :class:`Configuration` instance
    """
    path = os.path.normpath(path)
    dotted_path_levels = len(path.split('/'))
    files_keys = (
        (os.path.join(x[0], y), '.'.join((x[0].split('/') + [y])[(dotted_path_levels + remove_level):]))
        for x in os.walk(path)
        for y in x[2]
        if not x[0].split('/')[-1].startswith('..'))

    result = {}
    for filename, key in files_keys:
        result[key] = open(filename).read()

    return Configuration(result)


def config_from_json(data: Union[str, IO[str]], read_from_file: bool = False) -> Configuration:
    """
    Create a :class:`Configuration` instance from a JSON file.

    :param data: path to a JSON file or contents
    :param read_from_file: whether to read from a file path or to interpret the :attr:`data` as the contents of the
           INI file.
    :return: a :class:`Configuration` instance
    """
    if read_from_file:
        if isinstance(data, str):
            return Configuration(json.load(open(data, 'rt')))
        else:
            return Configuration(json.load(data))
    else:
        data = cast(str, data)
        return Configuration(json.loads(data))


def config_from_ini(data: Union[str, IO[str]], read_from_file: bool = False) -> Configuration:
    """
    Create a :class:`Configuration` instance from an INI file.

    :param data: path to an INI file or contents
    :param read_from_file: whether to read from a file path or to interpret the :attr:`data` as the contents of the
           INI file.
    :return: a :class:`Configuration` instance
    """
    import configparser
    if read_from_file:
        if isinstance(data, str):
            data = open(data, 'rt').read()
        else:
            data = data.read()
    data = cast(str, data)
    cfg = configparser.RawConfigParser()
    cfg.read_string(data)
    d = {section + "." + k: v for section, values in cfg.items() for k, v in values.items()}
    return Configuration(d)


def config_from_python(module: Union[str, ModuleType], prefix: str = '', separator: str = '_') -> Configuration:
    """
    Create a :class:`Configuration` instance from the objects in a Python module.

    :param module: a module or path string
    :param prefix: prefix to use to filter object names
    :param separator: separator to replace by dots
    :return: a :class:`Configuration` instance
    """
    if isinstance(module, str):
        if module.endswith('.py'):
            import importlib.util
            spec = importlib.util.spec_from_file_location(module, module)
            module = importlib.util.module_from_spec(spec)
            spec.loader = cast(InspectLoader, spec.loader)
            spec.loader.exec_module(module)
        else:
            import importlib
            module = importlib.import_module(module)

    variables = [x for x in dir(module) if not x.startswith('__') and x.startswith(prefix)]
    dict_ = {
        k[len(prefix):].replace(separator, '.').strip('.'): getattr(module, k)
        for k in variables
    }
    return Configuration(dict_)


def config_from_dict(data: dict) -> Configuration:
    """
    Create a :class:`Configuration` instance from a dictionary.

    :param data: dictionary with string keys
    :return: a :class:`Configuration` instance
    """
    return Configuration(data)


def create_path_from_config(path: str, cfg: Configuration, remove_level: int = 1) -> Configuration:
    """
    Auxiliary method to output a path configuration from a :class:`Configuration` instance.

    :param path: path to create the config files in
    :param cfg: :class:`Configuration` instance
    :param remove_level: how many levels to remove
    """
    import os.path
    assert os.path.isdir(path)

    d = cfg.as_dict()
    for k, v in d.items():
        with open(os.path.join(path, k), 'wb') as f:
            f.write(str(v).encode())

        cfg = config_from_path(path, remove_level=remove_level)
    return cfg


if yaml is not None:  # pragma: no branch
    def config_from_yaml(data: Union[str, IO[str]], read_from_file: bool = False) -> Configuration:
        """
        Return a Configuration instance from YAML files.

        :param data: string or file
        :param read_from_file: whether `data` is a file or a YAML formatted string
        :return: a Configuration instance
        """
        if read_from_file and isinstance(data, str):
            loaded = yaml.load(open(data, 'rt'), Loader=yaml.FullLoader)
        else:
            loaded = yaml.load(data, Loader=yaml.FullLoader)
        if not isinstance(loaded, dict):
            raise ValueError('Data should be a dictionary')
        return Configuration(loaded)


if toml is not None:  # pragma: no branch
    def config_from_toml(data: Union[str, IO[str]], read_from_file: bool = False) -> Configuration:
        """
        Return a Configuration instance from TOML files.

        :param data: string or file
        :param read_from_file: whether `data` is a file or a TOML formatted string
        :return: a Configuration instance
        """
        if read_from_file:
            if isinstance(data, str):
                loaded = toml.load(open(data, 'rt'))
            else:
                loaded = toml.load(data)
        else:
            data = cast(str, data)
            loaded = toml.loads(data)
        loaded = cast(dict, loaded)
        return Configuration(loaded)
