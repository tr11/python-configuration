from config import config_from_dict, config_from_python
import sys
import os


DICT = {
    "a1.B1.c1": 1,
    "a1.b1.C2": 2,
    "A1.b1.c3": 3,
    "a1.b2.c1": "a",
    "a1.b2.c2": True,
    "a1.b2.c3": 1.1,
    "a2.b1.c1": 'f',
    "a2.b1.c2": False,
    "a2.b1.c3": None,
    "a2.b2.c1": 10,
    "a2.b2.c2": 'YWJjZGVmZ2g=',
    "a2.b2.c3": "abcdefgh",
    'sys.version': sys.hexversion
}


def test_load_from_module():  # type: ignore
    import python_config
    cfg = config_from_python(python_config, prefix='CONFIG', lowercase_keys=True)
    assert cfg["a1.b2"].as_dict() == {"c1": "a", "c2": True, "c3": 1.1}
    assert cfg['sys.version'] == sys.hexversion


def test_load_from_path():  # type: ignore
    path = os.path.join(os.path.dirname(__file__), 'python_config.py')
    cfg = config_from_python(path, prefix='CONFIG', lowercase_keys=True)
    assert cfg["a1.b2"].as_dict() == {"c1": "a", "c2": True, "c3": 1.1}
    assert cfg['sys.version'] == sys.hexversion


def test_load_from_module_string():  # type: ignore
    path = 'tests.python_config'
    cfg = config_from_python(path, prefix='CONFIG', lowercase_keys=True)
    assert cfg["a1.b2"].as_dict() == {"c1": "a", "c2": True, "c3": 1.1}
    assert cfg['sys.version'] == sys.hexversion


def test_equality():  # type: ignore
    import python_config
    cfg = config_from_python(python_config, prefix='CONFIG', lowercase_keys=True)
    assert cfg == config_from_dict(DICT, lowercase_keys=True)


def test_equality_from_path():  # type: ignore
    path = os.path.join(os.path.dirname(__file__), 'python_config.py')
    cfg = config_from_python(path, prefix='CONFIG', lowercase_keys=True)
    assert cfg == config_from_dict(DICT, lowercase_keys=True)
