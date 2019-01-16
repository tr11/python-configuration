import os
import json
import base64
from importlib.abc import InspectLoader
from types import ModuleType
from typing import Any, IO, Union, List, Iterable, cast, KeysView, ItemsView, ValuesView

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
    """ Return the boolean value ``True`` if the case-lowered value of string
    input ``s`` is a :term:`truthy string`. If ``s`` is already one of the
    boolean values ``True`` or ``False``, return it."""
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
    The Configuration class takes a dictionary input with keys such as
    a1.b1.c1
    a1.b1.c2
    a1.b2.c1
    a1.b2.c2
    a2.b1.c1
    a2.b1.c2
    a2.b2.c1
    a2.b2.c2
    """

    def __init__(self, config_: dict):
        self._config: dict = self._flatten_dict(config_)

    def __eq__(self, other):  # type: ignore
        return self.as_dict() == other.as_dict()

    def _merge_dict(self, d: dict, prefix: str) -> dict:
        result: dict = {}
        d = dict((k.lower(), v) for k, v in d.items())
        inner = dict((k[(len(prefix) + 1):].lower(), v) for k, v in d.items() if k.startswith(prefix + '.'))
        result.update(inner)
        return result

    def _flatten_dict(self, d: dict) -> dict:
        nested = set(k for k, v in d.items() if isinstance(v, dict))
        result = dict((k.lower() + '.' + ki, vi)
                      for k in nested
                      for ki, vi in self._flatten_dict(d[k]).items())
        result.update((k.lower(), v) for k, v in d.items() if not isinstance(v, dict))
        return result

    def _get_subset(self, prefix: str) -> Union[dict, Any]:
        """
        Returns the subset of the config dictionary whose keys start with :prefix:
        :param prefix: string
        :return: dict
        """
        d = dict((k[(len(prefix) + 1):], v) for k, v in self._config.items() if k.startswith(prefix + '.'))
        if not d:
            prefixes = prefix.split('.')
            if len(prefixes) == 1:
                return self._config.get(prefix, {})
            d = self._config
            while prefixes:  # pragma: no branches
                p = prefixes[0]
                new_d = self._merge_dict(d, p)
                if new_d == {}:
                    return d.get(p, {}) if len(prefixes) == 1 else {}
                d = new_d
                prefixes = prefixes[1:]
        return d

    def __getitem__(self, item: str) -> Union['Configuration', Any]:
        v = self._get_subset(item)
        if v == {}:
            raise KeyError(item)
        return Configuration(v) if isinstance(v, dict) else v

    def __getattr__(self, item: str) -> Any:
        v = self._get_subset(item)
        if v == {}:
            raise KeyError(item)
        return Configuration(v) if isinstance(v, dict) else v

    def get(self, key: str, default: Any = None) -> Union[dict, Any]:
        return self.as_dict().get(key, default)

    def as_dict(self) -> dict:
        return self._config

    def get_bool(self, item: str) -> bool:
        return as_bool(self[item])

    def get_str(self, item: str, fmt: str = '{}') -> str:
        return fmt.format(self[item])

    def get_int(self, item: str) -> int:
        return int(self[item])

    def get_float(self, item: str) -> float:
        return float(self[item])

    def get_dict(self, item: str) -> dict:
        return dict(self._get_subset(item))

    def base64encode(self, item: str) -> bytes:
        b = self[item]
        b = b if isinstance(b, bytes) else b.encode()
        return base64.b64encode(b)

    def base64decode(self, item: str) -> bytes:
        b = self[item]
        b = b if isinstance(b, bytes) else b.encode()
        return base64.b64decode(b, validate=True)

    def keys(self) -> Union['Configuration', Any, KeysView[str]]:
        try:
            return self['keys']
        except KeyError:
            return self.as_dict().keys()

    def values(self) -> Union['Configuration', Any, ValuesView[Any]]:
        try:
            return self['values']
        except KeyError:
            return self.as_dict().values()

    def items(self) -> Union['Configuration', Any, ItemsView[str, Any]]:
        try:
            return self['items']
        except KeyError:
            return self.as_dict().items()

    def __repr__(self) -> str:
        return "<Configuration: %r>" % self._config


class ConfigurationSet(Configuration):
    def __init__(self, *configs: Configuration):
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

    def __getitem__(self, item: str)-> Union[Configuration, Any]:
        return self._from_configs('__getitem__', item)

    def __getattr__(self, item: str)-> Union[Configuration, Any]:
        return self._from_configs('__getattr__', item)

    def get(self, key: str, default: Any = None) -> Union[dict, Any]:
        try:
            return self[key]
        except Exception:
            return default

    def as_dict(self) -> dict:
        result = {}
        for config_ in self._configs[::-1]:
            result.update(config_.as_dict())
        return result

    def get_dict(self, item: str) -> dict:
        return dict(self[item])

    def __repr__(self) -> str:
        return "<ConfigurationSet %r>" % self.as_dict()


def config(*configs: Iterable, prefix: str = '') -> ConfigurationSet:
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
                config_ = ('path', config_)
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
    result = {}
    for key, value in os.environ.items():
        if not key.startswith(prefix + separator):
            continue
        result[key[len(prefix):].replace(separator, '.').strip('.')] = value

    return Configuration(result)


def config_from_path(path: str, remove_level: int = 1) -> Configuration:
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
    if read_from_file:
        if isinstance(data, str):
            return Configuration(json.load(open(data, 'rt')))
        else:
            return Configuration(json.load(data))
    else:
        data = cast(str, data)
        return Configuration(json.loads(data))


def config_from_ini(data: Union[str, IO[str]], read_from_file: bool = False) -> Configuration:
    import configparser
    if read_from_file:
        if isinstance(data, str):
            data = open(data, 'rt').read()
        else:
            data = data.read()
    data = cast(str, data)
    cfg = configparser.RawConfigParser()
    cfg.read_string(data)
    d = dict((section + "." + k, v) for section, values in cfg.items() for k, v in values.items())
    return Configuration(d)


def config_from_python(module: Union[str, ModuleType], prefix: str = '', separator: str = '_') -> Configuration:
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

    variables = list(x for x in dir(module) if not x.startswith('__') and x.startswith(prefix))
    dict_ = dict(
        (k[len(prefix):].replace(separator, '.').strip('.'), getattr(module, k))
        for k in variables
    )
    return Configuration(dict_)


def config_from_dict(data: dict) -> Configuration:
    return Configuration(data)


def create_path_from_config(path: str, cfg: Configuration, remove_level: int = 1) -> Configuration:
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
        if read_from_file and isinstance(data, str):
            loaded = yaml.load(open(data, 'rt'))
        else:
            loaded = yaml.load(data)
        if not isinstance(loaded, dict):
            raise ValueError('Data should be a dictionary')
        return Configuration(loaded)


if toml is not None:  # pragma: no branch
    def config_from_toml(data: Union[str, IO[str]], read_from_file: bool = False) -> Configuration:
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
