from config import config, config_from_dict
from config.helpers import AttributeDict

from pytest import raises


def test_list_1():  # type: ignore
    definitions = {"my.var": ["hello"], "var": ["1", "2"]}

    cfg = config_from_dict(definitions, interpolate=True)
    cfg.var.insert(0, "0")
    assert cfg.var == ["1", "2"]
    cfg.my.var.insert(0, "hello again")
    assert cfg.my.var == ["hello"]


def test_list_2():  # type: ignore
    definitions = {"var": ["1", "2"]}
    definitions2 = {"my.var": ["hello"]}

    cfg = config(definitions, definitions2, interpolate=True)
    cfg.var.insert(0, "0")
    assert cfg.var == ["1", "2"]
    cfg.my.var.insert(0, "hello again")
    assert cfg.my.var == ["hello"]


def test_list_3():  # type: ignore
    definitions = {"my.var": ["hello"], "var": ["1", "2"]}

    cfg = config_from_dict(definitions, interpolate=True)
    assert cfg.my.as_dict() == {"var": ["hello"]}
    cfg.my.as_dict()["var"].insert(0, "hello again")
    assert cfg.my.as_dict() == {"var": ["hello"]}


def test_attribute_dict_1():  # type: ignore
    definitions = {
        "my.var": ["hello"],
        "var": ["1", "2"],
        "var2": {"a": {"c": 1, "d": 10}, "b": 2},
    }

    cfg = config_from_dict(definitions, interpolate=True)
    d = cfg.as_attrdict()

    assert isinstance(d, dict)
    assert isinstance(d, AttributeDict)
    assert d.var == ["1", "2"]
    assert d.my.var == ["hello"]
    assert d.var2.a == {"c": 1, "d": 10}

    with raises(AttributeError):
        assert d.var3

    d.var3 = "abc"
    assert d.var3 == "abc"


def test_tuple():  # type: ignore
    DICT = {"a1": (1, 2)}
    cfg = config_from_dict(DICT, interpolate=True)
    assert cfg["a1"] == (1, 2)
