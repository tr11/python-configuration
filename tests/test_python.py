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
    "a2.b1.c1": "f",
    "a2.b1.c2": False,
    "a2.b1.c3": None,
    "a2.b2.c1": 10,
    "a2.b2.c2": "YWJjZGVmZ2g=",
    "a2.b2.c3": "abcdefgh",
    "sys.version": sys.hexversion,
}


def test_load_from_module():  # type: ignore
    from . import python_config

    cfg = config_from_python(python_config, prefix="CONFIG", lowercase_keys=True)
    assert cfg["a1.b2"].as_dict() == {"c1": "a", "c2": True, "c3": 1.1}
    assert cfg["sys.version"] == sys.hexversion


def test_load_from_path():  # type: ignore
    path = os.path.join(os.path.dirname(__file__), "python_config.py")
    cfg = config_from_python(path, prefix="CONFIG", lowercase_keys=True)
    assert cfg["a1.b2"].as_dict() == {"c1": "a", "c2": True, "c3": 1.1}
    assert cfg["sys.version"] == sys.hexversion


def test_load_from_module_string():  # type: ignore
    path = "tests.python_config"
    cfg = config_from_python(path, prefix="CONFIG", lowercase_keys=True)
    assert cfg["a1.b2"].as_dict() == {"c1": "a", "c2": True, "c3": 1.1}
    assert cfg["sys.version"] == sys.hexversion


def test_equality():  # type: ignore
    from . import python_config

    cfg = config_from_python(python_config, prefix="CONFIG", lowercase_keys=True)
    assert cfg == config_from_dict(DICT, lowercase_keys=True)


def test_equality_from_path():  # type: ignore
    path = os.path.join(os.path.dirname(__file__), "python_config.py")
    cfg = config_from_python(path, prefix="CONFIG", lowercase_keys=True)
    assert cfg == config_from_dict(DICT, lowercase_keys=True)


def test_reload():  # type: ignore
    from . import python_config

    cfg = config_from_python(python_config, prefix="CONFIG", lowercase_keys=True)
    assert cfg == config_from_dict(DICT, lowercase_keys=True)

    python_config.CONFIG_A10_B10 = "a"
    cfg.reload()
    cfg2 = config_from_dict(DICT, lowercase_keys=True)
    cfg2["a10.b10"] = "a"
    assert cfg == cfg2


def test_separator():  # type: ignore
    from . import python_config_2

    cfg = config_from_python(
        python_config_2, prefix="CONFIG", separator="__", lowercase_keys=True
    )
    assert cfg == config_from_dict(DICT, lowercase_keys=True)
