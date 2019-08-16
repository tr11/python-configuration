from config import (
    config_from_dict,
    config_from_env,
    config_from_python,
    create_path_from_config,
    ConfigurationSet,
    config
)
from pytest import raises
import os
import json
try:
    import yaml
except ImportError:
    yaml = None  # type: ignore
try:
    import toml
except ImportError:
    toml = None  # type: ignore
import pytest


DICT1 = {
    "a1.B1.c1": 1,
    "a1.b1.C2": 2,
    "A1.b1.c3": 3,
    "a1.b2.c1": "a",
    "a1.b2.c2": True,
    "a1.b2.c3": 1.1,
}
DICT2_1 = {
    "a2.b1.c1": 'f',
    "a2.b1.c2": False,
    "a2.B1.c3": None,
}
DICT2_2 = {
    "a2.b2.c1": 10,
    "a2.b2.c2": 'YWJjZGVmZ2g=',
    "a2.b2.C3": "abcdefgh",
}
DICT3_1 = {
    "a2.b2.c1": 10,
    "a2.b2.c2": 'YWJjZGVmZ2g=',
    "a2.b2.C3": "abcdefgh",
    "z1": 100,
}
DICT3_2 = {
    "a2": 10,
    "z1.w2": 123,
    "z1.w3": "abc",
}
DICT3_3 = {
    "a2.g2": 10,
    "a2.w2": 123,
    "a2.w3": "abc",
}
DICT3 = {
    "a3.b1.c1": 'af',
    "a3.b1.c2": True,
    "a3.b1.c3": None,
    "a3.b2.c1": 104,
    "a3.b2.c2": 'YWJjZGVmZ2g=',
    "a3.b2.c3": "asdfdsbcdefgh",
}
JSON = json.dumps(DICT3)

if yaml:
    YAML = """
    z1:
        w1: 1
        w2: null
        w3: abc
    z2:
        w1: 1.1
        w2:
            - a
            - b
            - c
        w3:
            p1: 1
            p2: 5.4
    """

    DICT_YAML = {
        "z1.w1": 1,
        "z1.w2": None,
        "z1.w3": "abc",
        "z2.w1": 1.1,
        "z2.w2": ["a", "b", "c"],
        "z2.w3": {"p1": 1, "p2": 5.4},
    }

if toml:
    TOML = """
    [owner]
    name = "ABC"
    [database]
    server = "192.168.1.1"
    ports = [ 8001, 8001, 8002,]
    connection_max = 5000
    enabled = true
    [clients]
    data = [ [ "gamma", "delta",], [ 1, 2,],]
    hosts = [ "alpha", "omega",]
    [servers.alpha]
    ip = "10.0.0.1"
    dc = "eqdc10"
    [servers.beta]
    ip = "10.0.0.2"
    dc = "eqdc10"
    """

    DICT_TOML = {'owner': {'name': 'ABC'},
                 'database': {'server': '192.168.1.1',
                              'ports': [8001, 8001, 8002],
                              'connection_max': 5000,
                              'enabled': True},
                 'clients': {'data': [['gamma', 'delta'], [1, 2]],
                             'hosts': ['alpha', 'omega']},
                 'servers': {'alpha': {'ip': '10.0.0.1', 'dc': 'eqdc10'},
                             'beta': {'ip': '10.0.0.2', 'dc': 'eqdc10'}}}

INI = """
[section1]
key1 = True

[section2]
key1 = abc
key2 = def
key3 = 1.1

[section3]
key1 = 1
key2 = 0
"""

DICT_INI = {
    "section1.key1": 'True',
    "section2.key1": "abc",
    "section2.key2": "def",
    "section2.key3": '1.1',
    "section3.key1": '1',
    "section3.key2": '0',
}

PATH_DICT = {
    "sdf.dsfsfd": 1,
    "sdjf.wquwe": "sdfsd",
    "sdjf.wquwe43": None,
    "sdjf.wquwse43": True
}

PREFIX = 'CONFIG'

os.environ.update(
    (PREFIX + '__' + k.replace('.', '__').upper(), str(v))
    for k, v in DICT1.items()
)


def test_load_env():  # type: ignore
    cfg = ConfigurationSet(
        config_from_dict(DICT2_1, lowercase_keys=True),
        config_from_dict(DICT2_2, lowercase_keys=True),
        config_from_env(prefix=PREFIX, lowercase_keys=True)
    )
    # from env
    assert cfg["a1.b1.c1"] == '1'
    assert cfg["a1.b1"].get_int('c1') == 1
    assert cfg["a1.b1"].as_dict() == {"c1": '1', "c2": '2', "c3": '3'}
    assert cfg["a1.b2"].as_dict() == {"c1": "a", "c2": 'True', "c3": '1.1'}
    # from dict
    assert cfg["a2.b1.c1"] == 'f'
    assert cfg["a2.b2"].as_dict() == {'c1': 10, 'c2': 'YWJjZGVmZ2g=', 'c3': 'abcdefgh'}


def test_fails():  # type: ignore
    cfg = ConfigurationSet(
        config_from_dict(DICT2_1, lowercase_keys=True),
        config_from_dict(DICT2_2, lowercase_keys=True),
        config_from_env(prefix=PREFIX, lowercase_keys=True)
    )

    with raises(KeyError):
        assert cfg["a1.b2.c3.d4"] is Exception
        pytest.fail("a1.b2.c3.d4")

    with raises(KeyError):
        assert cfg.a1.b2.c4 is Exception
        pytest.fail("'c4'")

    with raises(ValueError):
        assert cfg["a1.b2"].get_bool("c3") is Exception
        pytest.fail("Expected a valid True or False expression.")


def test_get():  # type: ignore
    cfg = ConfigurationSet(
        config_from_dict(DICT2_1, lowercase_keys=True),
        config_from_dict(DICT2_2, lowercase_keys=True),
        config_from_env(prefix=PREFIX, lowercase_keys=True)
    )

    assert cfg.get("a2.b2") == config_from_dict({'c1': 10, 'c2': 'YWJjZGVmZ2g=', 'c3': 'abcdefgh'})
    assert cfg.get("a2.b5", "1") == "1"


def test_get_dict():  # type: ignore
    cfg = ConfigurationSet(
        config_from_dict(DICT2_1, lowercase_keys=True),
        config_from_dict(DICT2_2, lowercase_keys=True),
        config_from_env(prefix=PREFIX, lowercase_keys=True)
    )

    assert cfg.get_dict("a2") == {'b1.c1': 'f', 'b1.c2': False, 'b1.c3': None, 'b2.c1': 10,
                                  'b2.c2': 'YWJjZGVmZ2g=', 'b2.c3': 'abcdefgh'}
    assert cfg.a2.as_dict() == {'b1.c1': 'f', 'b1.c2': False, 'b1.c3': None, 'b2.c1': 10,
                                'b2.c2': 'YWJjZGVmZ2g=', 'b2.c3': 'abcdefgh'}
    assert dict(cfg.a2) == {'b1.c1': 'f', 'b1.c2': False, 'b1.c3': None, 'b2.c1': 10,
                            'b2.c2': 'YWJjZGVmZ2g=', 'b2.c3': 'abcdefgh'}
    with raises(KeyError):
        assert cfg.get_dict("a3") is Exception

    assert set(cfg.a2.values()) == {'f', False, None, 10, 'YWJjZGVmZ2g=', 'abcdefgh'}
    assert dict(cfg.a2) == dict(cfg.a2.items())


def test_get_dict_different_types():  # type: ignore
    cfg = ConfigurationSet(
        config_from_dict(DICT3_1, lowercase_keys=True),
        config_from_dict(DICT3_2, lowercase_keys=True),  # a2 is ignored here
        config_from_dict(DICT3_3, lowercase_keys=True),
    )

    assert cfg.get_dict("a2") == {'b2.c1': 10, 'b2.c2': 'YWJjZGVmZ2g=', 'b2.c3': 'abcdefgh',
                                  'g2': 10, 'w2': 123, 'w3': 'abc'}
    assert cfg.a2.as_dict() == {'b2.c1': 10, 'b2.c2': 'YWJjZGVmZ2g=', 'b2.c3': 'abcdefgh',
                                'g2': 10, 'w2': 123, 'w3': 'abc'}
    assert dict(cfg.a2) == {'b2.c1': 10, 'b2.c2': 'YWJjZGVmZ2g=', 'b2.c3': 'abcdefgh',
                            'g2': 10, 'w2': 123, 'w3': 'abc'}

    with raises(TypeError):  # the first configuration overrides the type
        assert cfg.get_dict("z1") is Exception
    assert cfg.z1 == 100


def test_repr():  # type: ignore
    import sys
    path = os.path.join(os.path.dirname(__file__), 'python_config.py')
    cfg = ConfigurationSet(
        config_from_dict(DICT2_1, lowercase_keys=True),
        config_from_dict(DICT2_2, lowercase_keys=True),
        config_from_env(prefix=PREFIX, lowercase_keys=True),
        config_from_python(path, prefix='CONFIG', lowercase_keys=True)
    )

    joined_dicts = dict((k, str(v)) for k, v in DICT1.items())
    joined_dicts.update(DICT2_1)
    joined_dicts.update(DICT2_2)
    joined_dicts['sys.version'] = sys.hexversion
    assert str(dict((k.lower(), v) for k, v in joined_dicts.items())) in repr(cfg)


def test_alternate_set_loader():  # type: ignore
    import sys
    path = os.path.join(os.path.dirname(__file__), 'python_config.py')

    import tempfile
    with tempfile.TemporaryDirectory() as folder:
        create_path_from_config(folder, config_from_dict(PATH_DICT), remove_level=0)
        entries = [
            DICT2_1,  # assumes dict
            ('dict', DICT2_2),
            ('env', PREFIX),
            ('python', path, 'CONFIG'),
            ('json', JSON),
            ('ini', INI),
            ('path', folder, 0),
        ]
        if yaml:
            entries.append(('yaml', YAML))
        if toml:
            entries.append(('toml', TOML))
        cfg = config(*entries, lowercase_keys=True)

    joined_dicts = dict((k, str(v)) for k, v in DICT1.items())
    joined_dicts.update(DICT2_1)
    joined_dicts.update(DICT2_2)
    joined_dicts.update(DICT3)
    joined_dicts.update(DICT_INI)
    if yaml:
        joined_dicts.update(DICT_YAML)
    if toml:
        joined_dicts.update(DICT_TOML)
    joined_dicts.update((k, str(v)) for k, v in PATH_DICT.items())
    joined_dicts['sys.version'] = sys.hexversion
    assert config_from_dict(joined_dicts, lowercase_keys=True).as_dict() == cfg.as_dict()
    assert config_from_dict(joined_dicts, lowercase_keys=True) == cfg


def test_alternate_set_loader_prefix():  # type: ignore
    import sys
    path = os.path.join(os.path.dirname(__file__), 'python_config.py')

    import tempfile
    with tempfile.TemporaryDirectory() as folder:
        create_path_from_config(folder, config_from_dict(PATH_DICT), remove_level=0)
        cfg = config(
            DICT2_1,  # assumes dict
            ('dict', DICT2_2),
            ('env', ),
            ('python', path),
            ('json', JSON),
            ('ini', INI),
            ('path', folder, 0),
            prefix='CONFIG',
            lowercase_keys=True
        )

    joined_dicts = dict((k, str(v)) for k, v in DICT1.items())
    joined_dicts.update(DICT2_1)
    joined_dicts.update(DICT2_2)
    joined_dicts.update(DICT3)
    joined_dicts.update(DICT_INI)
    joined_dicts.update((k, str(v)) for k, v in PATH_DICT.items())
    joined_dicts['sys.version'] = sys.hexversion
    assert config_from_dict(joined_dicts, lowercase_keys=True).as_dict() == cfg.as_dict()
    assert config_from_dict(joined_dicts, lowercase_keys=True) == cfg


def test_alternate_set_loader_strings():  # type: ignore
    import sys
    path = str(os.path.join(os.path.dirname(__file__), 'python_config.py'))

    import tempfile
    with tempfile.TemporaryDirectory() as folder, \
            tempfile.NamedTemporaryFile(suffix='.json') as f1, \
            tempfile.NamedTemporaryFile(suffix='.ini') as f2, \
            tempfile.NamedTemporaryFile(suffix='.yaml') as f3, \
            tempfile.NamedTemporaryFile(suffix='.toml') as f4:
        # path
        subfolder = folder + '/sub'
        os.makedirs(subfolder)
        create_path_from_config(subfolder, config_from_dict(PATH_DICT), remove_level=1)
        # json
        f1.file.write(JSON.encode())
        f1.file.flush()
        # ini
        f2.file.write(INI.encode())
        f2.file.flush()

        entries = [
            DICT2_1,  # dict
            DICT2_2,
            'env',
            path,  # python
            f1.name,  # json
            f2.name,  # ini
            folder,  # path
        ]
        if yaml:
            f3.file.write(YAML.encode())
            f3.file.flush()
            entries.append(
                f3.name  # yaml
            )
        if toml:
            f4.file.write(TOML.encode())
            f4.file.flush()
            entries.append(
                f4.name  # toml
            )

        cfg = config(
            *entries,
            prefix='CONFIG',
            lowercase_keys=True
        )

    joined_dicts = dict((k, str(v)) for k, v in DICT1.items())
    joined_dicts.update(DICT2_1)
    joined_dicts.update(DICT2_2)
    joined_dicts.update(DICT3)
    joined_dicts.update(DICT_INI)
    if yaml:
        joined_dicts.update(DICT_YAML)
    if toml:
        joined_dicts.update(DICT_TOML)
    joined_dicts.update((k, str(v)) for k, v in PATH_DICT.items())
    joined_dicts['sys.version'] = sys.hexversion
    assert config_from_dict(joined_dicts, lowercase_keys=True).as_dict() == cfg.as_dict()
    assert config_from_dict(joined_dicts, lowercase_keys=True) == cfg


def test_alternate_set_loader_strings_python_module():  # type: ignore
    import sys
    module = 'tests.python_config'

    import tempfile
    with tempfile.TemporaryDirectory() as folder, \
            tempfile.NamedTemporaryFile(suffix='.json') as f1, \
            tempfile.NamedTemporaryFile(suffix='.ini') as f2, \
            tempfile.NamedTemporaryFile(suffix='.yaml') as f3, \
            tempfile.NamedTemporaryFile(suffix='.toml') as f4:
        # path
        subfolder = folder + '/sub'
        os.makedirs(subfolder)
        create_path_from_config(subfolder, config_from_dict(PATH_DICT), remove_level=1)
        # json
        f1.file.write(JSON.encode())
        f1.file.flush()
        # ini
        f2.file.write(INI.encode())
        f2.file.flush()

        entries = [
            DICT2_1,  # dict
            DICT2_2,
            'env',
            module,  # python
            f1.name,  # json
            f2.name,  # ini
            folder,  # path
        ]

        if yaml:
            f3.file.write(YAML.encode())
            f3.file.flush()
            entries.append(f3.name)
        if toml:
            f4.file.write(TOML.encode())
            f4.file.flush()
            entries.append(
                f4.name  # toml
            )

        cfg = config(
            *entries,
            prefix='CONFIG',
            lowercase_keys=True
        )

    joined_dicts = dict((k, str(v)) for k, v in DICT1.items())
    joined_dicts.update(DICT2_1)
    joined_dicts.update(DICT2_2)
    joined_dicts.update(DICT3)
    joined_dicts.update(DICT_INI)
    if yaml:
        joined_dicts.update(DICT_YAML)
    if toml:
        joined_dicts.update(DICT_TOML)
    joined_dicts.update((k, str(v)) for k, v in PATH_DICT.items())
    joined_dicts['sys.version'] = sys.hexversion
    assert config_from_dict(joined_dicts, lowercase_keys=True).as_dict() == cfg.as_dict()
    assert config_from_dict(joined_dicts, lowercase_keys=True) == cfg


def test_alternate_set_loader_fails():  # type: ignore
    with raises(ValueError):
        assert config() is Exception
        pytest.fail("configs should be a non-empty iterable of Configuration objects")

    with raises(ValueError):
        assert config(('no type', '')) is Exception

    with raises(ValueError):
        assert config('no type') is Exception

    with raises(ValueError):
        assert config([]) is Exception

    with raises(ValueError):
        assert config(('python', )) is Exception
