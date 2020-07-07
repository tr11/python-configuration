from config import config_from_dict, ConfigurationSet
from pytest import raises
import pytest
import json


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
}

NESTED = {
    "a1": {
        "b1": {"c1": 10, "C2": 20, "c3": 30},
        "b2": {"c1": "a0", "c2": False, "c3": 10.1},
    }
}

PROTECTED = {
    "important_password": "abc",
    "very_secret": "SeCReT",
    "clear_text": "abc",
    "url": "protocol://user:pass@hostname:port/path",
    "url2": "protocol://user@hostname:port/path",
}


def test_list():  # type: ignore
    cfg = config_from_dict(DICT, lowercase_keys=False)
    assert sorted(cfg) == ["A1", "a1", "a2"]
    assert list(cfg) == list(reversed(cfg))[::-1]

    with cfg.dotted_iter():
        assert sorted(cfg) == sorted(DICT.keys())
        assert list(cfg) == list(reversed(cfg))[::-1]


def test_len():  # type: ignore
    cfg = config_from_dict(DICT, lowercase_keys=False)
    assert len(cfg) == 3
    with cfg.dotted_iter():
        assert len(cfg) == len(DICT)


def test_setitem():  # type: ignore
    cfg = config_from_dict(DICT, lowercase_keys=True)

    assert len(cfg) == 2
    assert cfg["a1.b2.c1"] == "a"

    cfg["a1.b2.c1"] = 89
    assert len(cfg) == 2
    assert cfg["a1.b2.c1"] == 89

    cfg["a1.b2.c4"] = True
    assert len(cfg) == 2
    assert cfg["a1.b2.c1"] == 89
    assert cfg["a1.b2.c4"] is True

    cfg["a3"] = {"b1": 10, "b2": "test"}
    assert len(cfg) == 3
    assert cfg["a3.b1"] == 10
    assert cfg["a3.b2"] == "test"

    cfg = config_from_dict(DICT, lowercase_keys=True)

    with cfg.dotted_iter():
        assert len(cfg) == 12
        assert cfg["a1.b2.c1"] == "a"

        cfg["a1.b2.c1"] = 89
        assert len(cfg) == 12
        assert cfg["a1.b2.c1"] == 89

        cfg["a1.b2.c4"] = True
        assert len(cfg) == 13
        assert cfg["a1.b2.c1"] == 89
        assert cfg["a1.b2.c4"] is True

        cfg["a3"] = {"b1": 10, "b2": "test"}
        assert len(cfg) == 15
        assert cfg["a3.b1"] == 10
        assert cfg["a3.b2"] == "test"


def test_update():  # type: ignore
    cfg = config_from_dict(DICT, lowercase_keys=True)

    assert len(cfg) == 2
    assert cfg["a1.b2.c1"] == "a"

    cfg.update(PROTECTED)
    assert len(cfg) == 7

    cfg.update(NESTED)

    assert len(cfg) == 7
    assert cfg["a1.b2.c1"] == "a0"

    cfg = config_from_dict(DICT, lowercase_keys=True)

    with cfg.dotted_iter():
        assert len(cfg) == 12
        assert cfg["a1.b2.c1"] == "a"

        cfg.update(PROTECTED)
        assert len(cfg) == 17

        cfg.update(NESTED)

        assert len(cfg) == 17
        assert cfg["a1.b2.c1"] == "a0"


def test_delitem():  # type: ignore
    cfg = config_from_dict(DICT, lowercase_keys=True)

    assert len(cfg) == 2

    del cfg["a1.b1"]
    assert len(cfg) == 2

    with raises(KeyError):
        del cfg["z"]

    cfg = config_from_dict(DICT, lowercase_keys=True)

    with cfg.dotted_iter():
        assert len(cfg) == 12

        del cfg["a1.b1"]
        assert len(cfg) == 9

        with raises(KeyError):
            del cfg["z"]


def test_in():  # type: ignore
    cfg = config_from_dict(DICT, lowercase_keys=True)

    assert "x" not in cfg
    assert "a1" in cfg
    assert "a1.b2" in cfg
    assert "a1.b2.c3" in cfg


def test_clear():  # type: ignore
    cfg = config_from_dict(DICT, lowercase_keys=True)
    assert len(cfg) == 2
    with cfg.dotted_iter():
        assert len(cfg) == 12

    cfg.clear()
    assert len(cfg) == 0
    with cfg.dotted_iter():
        assert len(cfg) == 0


def test_copy():  # type: ignore
    cfg = config_from_dict(DICT, lowercase_keys=True)
    assert len(cfg) == 2
    with cfg.dotted_iter():
        assert len(cfg) == 12

    cfg2 = cfg.copy()

    assert cfg == cfg2


def test_pop():  # type: ignore
    cfg = config_from_dict(DICT, lowercase_keys=True)
    assert len(cfg) == 2
    with cfg.dotted_iter():
        assert len(cfg) == 12

    assert cfg.pop("a2.b1.c1") == "f"
    assert cfg.pop("a2.b1.c1", "something") == "something"
    with raises(KeyError):
        cfg.pop("a2.b1.c1")


def test_setdefault():  # type: ignore
    cfg = config_from_dict(DICT, lowercase_keys=False)

    # no changes
    assert cfg.setdefault("a2.b1.c1") == "f"
    assert len(cfg) == 3
    assert sorted(cfg) == sorted(["A1", "a1", "a2"])

    # add key
    assert cfg.setdefault("a2.b1.c7") is None
    assert len(cfg) == 3

    # add key with default
    assert cfg.setdefault("a2.b1.c8", "some value") == "some value"
    assert len(cfg) == 3
    assert cfg["a2.b1.c8"] == "some value"

    cfg = config_from_dict(DICT, lowercase_keys=False)

    with cfg.dotted_iter():
        # no changes
        assert cfg.setdefault("a2.b1.c1") == "f"
        assert len(cfg) == 12
        assert sorted(cfg) == sorted(DICT.keys())

        # add key
        assert cfg.setdefault("a2.b1.c7") is None
        assert len(cfg) == 13

        # add key with default
        assert cfg.setdefault("a2.b1.c8", "some value") == "some value"
        assert len(cfg) == 14
        assert cfg["a2.b1.c8"] == "some value"


def test_configset_list():  # type: ignore
    cfg = ConfigurationSet(
        config_from_dict(DICT, lowercase_keys=False),
        config_from_dict(PROTECTED, lowercase_keys=False),
    )

    assert sorted(cfg) == sorted(["A1", "a1", "a2"] + list(PROTECTED.keys()))
    with cfg.dotted_iter():
        assert sorted(cfg) == sorted(list(DICT.keys()) + list(PROTECTED.keys()))
    assert list(cfg) == list(reversed(cfg))[::-1]


def test_configset_len():  # type: ignore
    cfg = ConfigurationSet(
        config_from_dict(DICT, lowercase_keys=False),
        config_from_dict(PROTECTED, lowercase_keys=False),
    )
    assert len(cfg) == 8
    with cfg.dotted_iter():
        assert len(cfg) == len(DICT) + len(PROTECTED)


def test_configset_setitem():  # type: ignore
    cfg = ConfigurationSet(
        config_from_dict(DICT, lowercase_keys=False),
        config_from_dict(PROTECTED, lowercase_keys=False),
    )

    with cfg.dotted_iter():
        assert len(cfg) == 17
    assert cfg["a1.b2.c1"] == "a"

    cfg["a1.b2.c1"] = 89
    with cfg.dotted_iter():
        assert len(cfg) == 17
    assert cfg["a1.b2.c1"] == 89

    cfg["a1.b2.c4"] = True
    with cfg.dotted_iter():
        assert len(cfg) == 18
    assert cfg["a1.b2.c1"] == 89
    assert cfg["a1.b2.c4"] is True

    cfg["a3"] = {"b1": 10, "b2": "test"}
    with cfg.dotted_iter():
        assert len(cfg) == 20
    assert cfg["a3.b1"] == 10
    assert cfg["a3.b2"] == "test"


def test_configset_update():  # type: ignore
    cfg = ConfigurationSet(
        config_from_dict(DICT, lowercase_keys=True),
        config_from_dict(PROTECTED, lowercase_keys=True),
    )

    with cfg.dotted_iter():
        assert len(cfg) == 17
    assert cfg["a1.b2.c1"] == "a"

    cfg.update(NESTED)
    with cfg.dotted_iter():
        assert len(cfg) == 17
    assert cfg["a1.b2.c1"] == "a0"

    cfg.update({"important_password_2": "abc"})
    with cfg.dotted_iter():
        assert len(cfg) == 18


def test_configset_delitem():  # type: ignore
    cfg = ConfigurationSet(
        config_from_dict(DICT, lowercase_keys=True),
        config_from_dict(PROTECTED, lowercase_keys=True),
    )

    with cfg.dotted_iter():
        assert len(cfg) == 17

    del cfg["a1.b1"]
    with cfg.dotted_iter():
        assert len(cfg) == 14

    with raises(KeyError):
        del cfg["z"]


def test_configset_in():  # type: ignore
    cfg = ConfigurationSet(
        config_from_dict(DICT, lowercase_keys=False),
        config_from_dict(PROTECTED, lowercase_keys=False),
    )

    assert "x" not in cfg
    assert "a1" in cfg
    assert "a1.b2" in cfg
    assert "a1.b2.c3" in cfg


def test_configset_clear():  # type: ignore
    cfg = ConfigurationSet(
        config_from_dict(DICT, lowercase_keys=False),
        config_from_dict(PROTECTED, lowercase_keys=False),
    )
    with cfg.dotted_iter():
        assert len(cfg) == 17

    cfg.clear()
    assert len(cfg) == 0
    with cfg.dotted_iter():
        assert len(cfg) == 0


def test_configset_copy():  # type: ignore
    cfg = ConfigurationSet(
        config_from_dict(DICT, lowercase_keys=True),
        config_from_dict(PROTECTED, lowercase_keys=True),
    )
    with cfg.dotted_iter():
        assert len(cfg) == 17

    cfg2 = cfg.copy()
    assert cfg == cfg2


def test_configset_pop():  # type: ignore
    cfg = ConfigurationSet(
        config_from_dict(DICT, lowercase_keys=True),
        config_from_dict(PROTECTED, lowercase_keys=True),
    )

    with cfg.dotted_iter():
        assert len(cfg) == 17

    assert cfg.pop("a2.b1.c1") == "f"
    assert cfg.pop("a2.b1.c1", "something") == "something"
    with raises(KeyError):
        cfg.pop("a2.b1.c1")

    with cfg.dotted_iter():
        assert len(cfg) == 16


def test_configset_setdefault():  # type: ignore
    cfg = ConfigurationSet(
        config_from_dict(DICT, lowercase_keys=False),
        config_from_dict(PROTECTED, lowercase_keys=False),
    )

    # no changes
    assert cfg.setdefault("a2.b1.c1") == "f"
    assert len(cfg) == 8
    with cfg.dotted_iter():
        assert len(cfg) == 17
        assert sorted(cfg) == sorted(list(DICT.keys()) + list(PROTECTED.keys()))

    # add key
    assert cfg.setdefault("a2.b1.c7") is None
    assert len(cfg) == 8
    with cfg.dotted_iter():
        assert len(cfg) == 18

    # add key with default
    assert cfg.setdefault("a2.b1.c8", "some value") == "some value"
    assert len(cfg) == 8
    with cfg.dotted_iter():
        assert len(cfg) == 19
    assert cfg["a2.b1.c8"] == "some value"
