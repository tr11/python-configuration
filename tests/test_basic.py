from config import config_from_dict
import json

import pytest


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

RESERVED = {"keys": [1, 2, 3], "values": ["a", "b", "c"], "items": [1.1, 2.1, 3.1]}

NESTED = {
    "a1": {"b1": {"c1": 1, "C2": 2, "c3": 3}, "b2": {"c1": "a", "c2": True, "c3": 1.1}}
}

PROTECTED = {
    "important_password": "abc",
    "very_secret": "SeCReT",
    "clear_text": "abc",
    "url": "protocol://user:pass@hostname:port/path",
    "url2": "protocol://user@hostname:port/path",
}


def test_version_is_defined():  # type: ignore
    from config import __version__, __version_tuple__

    assert isinstance(__version__, str)
    assert isinstance(__version_tuple__, tuple)


def test_load_dict():  # type: ignore
    cfg = config_from_dict(DICT, lowercase_keys=True)
    assert cfg["a1.b1.c1"] == 1
    assert cfg["a1.b1"].as_dict() == {"c1": 1, "c2": 2, "c3": 3}
    assert cfg["a1.b2"].as_dict() == {"c1": "a", "c2": True, "c3": 1.1}


def test_load_nested():  # type: ignore
    cfg = config_from_dict(NESTED, lowercase_keys=True)
    assert cfg["a1.b1.c1"] == 1
    assert cfg["a1.b1"].as_dict() == {"c1": 1, "c2": 2, "c3": 3}
    assert cfg["a1.b2"].as_dict() == {"c1": "a", "c2": True, "c3": 1.1}


def test_gets():  # type: ignore
    cfg = config_from_dict(DICT)
    assert cfg["a1.b2"].get("r") is None
    assert cfg["a1.b2"].get("c3") == 1.1
    assert cfg["a1"].get_dict("b2") == {"c1": "a", "c2": True, "c3": 1.1}
    assert cfg.get_dict("a1") == {
        "B1.c1": 1,
        "b1.C2": 2,
        "b2.c1": "a",
        "b2.c2": True,
        "b2.c3": 1.1,
    }


def test_attr_gets():  # type: ignore
    cfg = config_from_dict(DICT)
    assert cfg.a1.b2.get("r") is None
    assert cfg.a1.b2.get("c3") == 1.1
    assert cfg.a1.get_dict("b2") == {"c1": "a", "c2": True, "c3": 1.1}


def test_base64():  # type: ignore
    cfg = config_from_dict(DICT)
    assert cfg.base64encode("a2.b2.c3") == b"YWJjZGVmZ2g="
    assert cfg.base64decode("a2.b2.c2") == b"abcdefgh"


def test_reserved():  # type: ignore
    cfg = config_from_dict(RESERVED)
    assert cfg["keys"] == [1, 2, 3]
    assert cfg["values"] == ["a", "b", "c"]
    assert cfg["items"] == [1.1, 2.1, 3.1]

    assert cfg.as_dict() == RESERVED
    with pytest.raises(TypeError):  # fails as the config has an entry for keys
        dict(cfg)


def test_fails():  # type: ignore
    cfg = config_from_dict(DICT)
    with pytest.raises(KeyError, match="a1.b2.c3.d4"):
        assert cfg["a1.b2.c3.d4"] is Exception

    with pytest.raises(AttributeError, match="c4"):
        assert cfg.a1.b2.c4 is Exception

    with pytest.raises(ValueError, match="Expected a valid True or False expression."):
        assert cfg["a1.b2"].get_bool("c3") is Exception


def test_type_conversions():  # type: ignore
    cfg = config_from_dict(DICT, lowercase_keys=True)
    assert cfg["a1.b2"].get_float("c3") == 1.1
    assert cfg["a1.b2"].get_int("c3") == 1
    assert cfg["a1.b2"].get_str("c3") == "1.1"
    assert cfg["a1.b2"].get_str("c3", "{:0.3f}") == "1.100"
    assert cfg.a1.b2.c3 == 1.1
    assert dict(cfg.a1.b2) == {"c1": "a", "c2": True, "c3": 1.1}

    assert cfg["a1.b2"].get_bool("c2") is True  # True
    assert cfg["a1.b1"].get_bool("c1") is True  # 1
    assert cfg["a2.b1"].get_bool("c3") is False  # None
    assert cfg["a2.b1"].get_bool("c2") is False  # False
    assert cfg["a2.b1"].get_bool("c1") is False  # 'f'


def test_repr_and_str():  # type: ignore
    cfg = config_from_dict(DICT, lowercase_keys=True)

    # repr
    assert hex(id(cfg)) in repr(cfg)

    # str
    assert (
        str(cfg)
        == "{'a1.b1.c1': 1, 'a1.b1.c2': 2, 'a1.b1.c3': 3, 'a1.b2.c1': 'a', 'a1.b2.c2': True,"
        " 'a1.b2.c3': 1.1, 'a2.b1.c1': 'f', 'a2.b1.c2': False, 'a2.b1.c3': None,"
        " 'a2.b2.c1': 10, 'a2.b2.c2': 'YWJjZGVmZ2g=', 'a2.b2.c3': 'abcdefgh'}"
    )

    # protected
    cfg = config_from_dict(PROTECTED, lowercase_keys=True)
    assert (
        str(cfg) == "{'clear_text': 'abc', 'important_password': '******', "
        "'url': 'protocol://user:******@hostname/path', 'url2': 'protocol://user@hostname:port/path', "
        "'very_secret': '******'}"
    )


def test_dict_methods_keys():  # type: ignore
    cfg = config_from_dict(DICT, lowercase_keys=True)

    assert set(cfg.keys()) == {
        "a1",
        "a2",
    }
    with cfg.dotted_iter() as cfg_:
        assert set(cfg_.keys()) == {
            "a1.b2.c3",
            "a2.b1.c3",
            "a2.b2.c2",
            "a2.b2.c3",
            "a1.b2.c2",
            "a2.b1.c2",
            "a1.b2.c1",
            "a1.b1.c3",
            "a2.b1.c1",
            "a1.b1.c1",
            "a1.b1.c2",
            "a2.b2.c1",
        }
    assert set(cfg.keys(levels=1)) == {"a1", "a2"}
    assert set(cfg.keys(levels=2)) == {"a1.b2", "a2.b2", "a2.b1", "a1.b1"}
    assert set(cfg.keys(levels=3)) == {
        "a1.b2.c3",
        "a2.b1.c3",
        "a2.b2.c2",
        "a2.b2.c3",
        "a1.b2.c2",
        "a2.b1.c2",
        "a1.b2.c1",
        "a1.b1.c3",
        "a2.b1.c1",
        "a1.b1.c1",
        "a1.b1.c2",
        "a2.b2.c1",
    }
    assert set(cfg.keys(levels=100)) == {
        "a1.b2.c3",
        "a2.b1.c3",
        "a2.b2.c2",
        "a2.b2.c3",
        "a1.b2.c2",
        "a2.b1.c2",
        "a1.b2.c1",
        "a1.b1.c3",
        "a2.b1.c1",
        "a1.b1.c1",
        "a1.b1.c2",
        "a2.b2.c1",
    }

    with pytest.raises(AssertionError):
        set(cfg.keys(levels=0))


def test_dict_methods_items():  # type: ignore
    cfg = config_from_dict(DICT, lowercase_keys=True)

    assert dict(cfg.items()) == {
        "a1": {
            "b1.c1": 1,
            "b1.c2": 2,
            "b1.c3": 3,
            "b2.c1": "a",
            "b2.c2": True,
            "b2.c3": 1.1,
        },
        "a2": {
            "b1.c1": "f",
            "b1.c2": False,
            "b1.c3": None,
            "b2.c1": 10,
            "b2.c2": "YWJjZGVmZ2g=",
            "b2.c3": "abcdefgh",
        },
    }
    with cfg.dotted_iter() as cfg_:
        assert set(cfg_.items()) == {
            ("a1.b1.c3", 3),
            ("a2.b1.c3", None),
            ("a1.b2.c1", "a"),
            ("a2.b2.c2", "YWJjZGVmZ2g="),
            ("a2.b1.c1", "f"),
            ("a1.b1.c1", 1),
            ("a2.b2.c3", "abcdefgh"),
            ("a1.b2.c2", True),
            ("a1.b2.c3", 1.1),
            ("a2.b2.c1", 10),
            ("a1.b1.c2", 2),
            ("a2.b1.c2", False),
        }
    assert dict(cfg.items(levels=1)) == {
        "a1": {
            "b1.c1": 1,
            "b1.c2": 2,
            "b1.c3": 3,
            "b2.c1": "a",
            "b2.c2": True,
            "b2.c3": 1.1,
        },
        "a2": {
            "b1.c1": "f",
            "b1.c2": False,
            "b1.c3": None,
            "b2.c1": 10,
            "b2.c2": "YWJjZGVmZ2g=",
            "b2.c3": "abcdefgh",
        },
    }
    assert dict(cfg.items(levels=2)) == {
        "a1.b1": {"c1": 1, "c2": 2, "c3": 3},
        "a1.b2": {"c1": "a", "c2": True, "c3": 1.1},
        "a2.b1": {"c1": "f", "c2": False, "c3": None},
        "a2.b2": {"c1": 10, "c2": "YWJjZGVmZ2g=", "c3": "abcdefgh"},
    }
    assert set(cfg.items(levels=3)) == {
        ("a1.b1.c3", 3),
        ("a2.b1.c3", None),
        ("a1.b2.c1", "a"),
        ("a2.b2.c2", "YWJjZGVmZ2g="),
        ("a2.b1.c1", "f"),
        ("a1.b1.c1", 1),
        ("a2.b2.c3", "abcdefgh"),
        ("a1.b2.c2", True),
        ("a1.b2.c3", 1.1),
        ("a2.b2.c1", 10),
        ("a1.b1.c2", 2),
        ("a2.b1.c2", False),
    }
    assert set(cfg.items(levels=100)) == {
        ("a1.b1.c3", 3),
        ("a2.b1.c3", None),
        ("a1.b2.c1", "a"),
        ("a2.b2.c2", "YWJjZGVmZ2g="),
        ("a2.b1.c1", "f"),
        ("a1.b1.c1", 1),
        ("a2.b2.c3", "abcdefgh"),
        ("a1.b2.c2", True),
        ("a1.b2.c3", 1.1),
        ("a2.b2.c1", 10),
        ("a1.b1.c2", 2),
        ("a2.b1.c2", False),
    }
    with pytest.raises(AssertionError):
        set(cfg.items(levels=0))


def test_dict_methods_values():  # type: ignore
    cfg = config_from_dict(DICT, lowercase_keys=True)

    assert sorted(json.dumps(x, sort_keys=True) for x in cfg.values()) == sorted(
        [
            json.dumps(
                {
                    "b1.c1": "f",
                    "b1.c2": False,
                    "b1.c3": None,
                    "b2.c1": 10,
                    "b2.c2": "YWJjZGVmZ2g=",
                    "b2.c3": "abcdefgh",
                },
                sort_keys=True,
            ),
            json.dumps(
                {
                    "b1.c1": 1,
                    "b1.c2": 2,
                    "b1.c3": 3,
                    "b2.c1": "a",
                    "b2.c2": True,
                    "b2.c3": 1.1,
                },
                sort_keys=True,
            ),
        ]
    )

    with cfg.dotted_iter() as cfg_:
        assert set(cfg_.values()) == {
            False,
            True,
            2,
            3,
            "f",
            1.1,
            10,
            None,
            "abcdefgh",
            "a",
            "YWJjZGVmZ2g=",
        }

    assert sorted(
        json.dumps(x, sort_keys=True) for x in cfg.values(levels=1)
    ) == sorted(
        [
            json.dumps(
                {
                    "b1.c1": "f",
                    "b1.c2": False,
                    "b1.c3": None,
                    "b2.c1": 10,
                    "b2.c2": "YWJjZGVmZ2g=",
                    "b2.c3": "abcdefgh",
                },
                sort_keys=True,
            ),
            json.dumps(
                {
                    "b1.c1": 1,
                    "b1.c2": 2,
                    "b1.c3": 3,
                    "b2.c1": "a",
                    "b2.c2": True,
                    "b2.c3": 1.1,
                },
                sort_keys=True,
            ),
        ]
    )


def test_dict_methods_dict():  # type: ignore
    cfg = config_from_dict(DICT, lowercase_keys=True)

    a1 = {
        "b1.c1": 1,
        "b1.c2": 2,
        "b1.c3": 3,
        "b2.c1": "a",
        "b2.c2": True,
        "b2.c3": 1.1,
    }
    a2 = {
        "b1.c1": "f",
        "b1.c2": False,
        "b1.c3": None,
        "b2.c1": 10,
        "b2.c2": "YWJjZGVmZ2g=",
        "b2.c3": "abcdefgh",
    }

    # as_dict and get_dict always returns dotted keys
    assert cfg.as_dict() == {k.lower(): v for k, v in DICT.items()}
    assert cfg.get_dict("a1") == a1
    assert cfg.get_dict("a1.b2") == {"c1": "a", "c2": True, "c3": 1.1}
    # dict() uses the iterator methods and will return a nested dict by default
    assert dict(cfg) == {"a1": a1, "a2": a2}

    with cfg.dotted_iter():
        # as_dict and get_dict always returns dotted keys
        assert cfg.as_dict() == {k.lower(): v for k, v in DICT.items()}
        assert cfg.get_dict("a1") == a1
        assert cfg.get_dict("a1.b2") == {"c1": "a", "c2": True, "c3": 1.1}
        # in this case the iterators will return all the (dotted) keys, so dict() is the same as .as_dict()
        assert dict(cfg) == {k.lower(): v for k, v in DICT.items()}


def test_eq():  # type: ignore
    cfg = config_from_dict(DICT, lowercase_keys=True)

    nested = {
        "a1": {
            "b1": {"c1": 1, "c2": 2, "c3": 3},
            "b2": {"c1": "a", "c2": True, "c3": 1.1},
        },
        "a2": {
            "b1": {"c1": "f", "c2": False, "c3": None},
            "b2": {"c1": 10, "c2": "YWJjZGVmZ2g=", "c3": "abcdefgh"},
        },
    }

    # equality with dictionaries -- the second one fails as it's a dict comparison
    assert cfg.as_dict() == {k.lower(): v for k, v in DICT.items()}
    assert cfg.as_dict() != nested
    # equality with dictionaries  -- in this case the second one passes
    assert cfg == {k.lower(): v for k, v in DICT.items()}
    assert cfg == nested
