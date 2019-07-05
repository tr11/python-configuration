from config import config_from_dict
from pytest import raises
import pytest


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
}

RESERVED = {
    "keys": [1, 2, 3],
    "values": ["a", "b", "c"],
    "items": [1.1, 2.1, 3.1],
}

NESTED = {
    'a1': {
        'b1': {
            "c1": 1,
            "C2": 2,
            "c3": 3,
        },
        'b2': {
            "c1": "a",
            "c2": True,
            "c3": 1.1,
        }
    }
}


def test_load_dict():  # type: ignore
    cfg = config_from_dict(DICT)
    assert cfg["a1.b1.c1"] == 1
    assert cfg["a1.b1"].as_dict() == {"c1": 1, "c2": 2, "c3": 3}
    assert cfg["a1.b2"].as_dict() == {"c1": "a", "c2": True, "c3": 1.1}


def test_load_nested():  # type: ignore
    cfg = config_from_dict(NESTED)
    assert cfg["a1.b1.c1"] == 1
    assert cfg["a1.b1"].as_dict() == {"c1": 1, "c2": 2, "c3": 3}
    assert cfg["a1.b2"].as_dict() == {"c1": "a", "c2": True, "c3": 1.1}


def test_gets():  # type: ignore
    cfg = config_from_dict(DICT)
    assert cfg["a1.b2"].get("r") is None
    assert cfg["a1.b2"].get("c3") == 1.1
    assert cfg["a1"].get_dict("b2") == {"c1": "a", "c2": True, "c3": 1.1}


def test_attr_gets():  # type: ignore
    cfg = config_from_dict(DICT)
    assert cfg.a1.b2.get("r") is None
    assert cfg.a1.b2.get("c3") == 1.1
    assert cfg.a1.get_dict("b2") == {"c1": "a", "c2": True, "c3": 1.1}


def test_base64():  # type: ignore
    cfg = config_from_dict(DICT)
    assert cfg.base64encode("a2.b2.c3") == b'YWJjZGVmZ2g='
    assert cfg.base64decode("a2.b2.c2") == b'abcdefgh'


def test_reserved():  # type: ignore
    cfg = config_from_dict(RESERVED)
    assert cfg['keys'] == [1, 2, 3]
    assert cfg["values"] == ["a", "b", "c"]
    assert cfg["items"] == [1.1, 2.1, 3.1]

    assert cfg.as_dict() == RESERVED
    with raises(TypeError):     # fails as the config has an entry for keys
        dict(cfg)


def test_fails():  # type: ignore
    cfg = config_from_dict(DICT)
    with raises(KeyError):
        assert cfg["a1.b2.c3.d4"] is Exception
        pytest.fail("a1.b2.c3.d4")

    with raises(KeyError):
        assert cfg.a1.b2.c4 is Exception
        pytest.fail("'c4'")

    with raises(ValueError):
        assert cfg["a1.b2"].get_bool("c3") is Exception
        pytest.fail("Expected a valid True or False expression.")


def test_type_conversions():  # type: ignore
    cfg = config_from_dict(DICT)
    assert cfg["a1.b2"].get_float("c3") == 1.1
    assert cfg["a1.b2"].get_int("c3") == 1
    assert cfg["a1.b2"].get_str("c3") == "1.1"
    assert cfg["a1.b2"].get_str("c3", '{:0.3f}') == "1.100"
    assert cfg.a1.b2.c3 == 1.1
    assert dict(cfg.a1.b2) == {'c1': 'a', 'c2': True, 'c3': 1.1}

    assert cfg["a1.b2"].get_bool("c2") is True  # True
    assert cfg["a1.b1"].get_bool("c1") is True  # 1
    assert cfg["a2.b1"].get_bool("c3") is False  # None
    assert cfg["a2.b1"].get_bool("c2") is False  # False
    assert cfg["a2.b1"].get_bool("c1") is False  # 'f'


def test_repr():  # type: ignore
    cfg = config_from_dict(DICT)
    assert str(dict((k.lower(), v) for k, v in DICT.items())) in repr(cfg)
