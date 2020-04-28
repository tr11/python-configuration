from config import config, config_from_dict

from pytest import raises


VALUES = {"var1": "This {var2}", "var2": "is a {var3}", "var3": "test"}
FAILS = {"var1": "This will fail {var2}", "var2": "{var3}", "var3": "{var1}"}
MULTI = {"var1": "This is a {var2} {var3}", "var2": "repeat {var3}", "var3": "test"}
ARRAY = {
    "var1": ["This is a {var2} {var3}", "{var2}", "{var3}"],
    "var2": "repeat {var3}",
    "var3": "test",
    "var4": ["{var3}", ["{var2}"], 1],
}
SET1 = {"var1": "This {var2}", "var2": "is a {var3}"}
SET2 = {"var3": "test"}


def test_no_interpolation():  # type: ignore
    cfg = config_from_dict(VALUES, lowercase_keys=True)

    assert cfg["var3"] == "test"
    assert cfg["var2"] == "is a {var3}"
    assert cfg["var1"] == "This {var2}"


def test_interpolation():  # type: ignore
    cfg = config_from_dict(VALUES, lowercase_keys=True, interpolate=True)

    assert cfg["var3"] == "test"
    assert cfg["var2"] == "is a test"
    assert cfg["var1"] == "This is a test"
    assert cfg.var1 == "This is a test"


def test_raise_on_interpolation_cycle():  # type: ignore
    cfg = config_from_dict(FAILS, lowercase_keys=True, interpolate=True)
    with raises(ValueError, match="Cycle detected"):
        assert cfg["var1"]


def test_multiple_interpolation():  # type: ignore
    cfg = config_from_dict(MULTI, lowercase_keys=True, interpolate=True)

    assert cfg["var3"] == "test"
    assert cfg["var2"] == "repeat test"
    assert cfg["var1"] == "This is a repeat test test"
    assert cfg.var1 == "This is a repeat test test"


def test_list():  # type: ignore
    cfg = config_from_dict(ARRAY, lowercase_keys=True, interpolate=True)

    assert cfg["var3"] == "test"
    assert cfg["var2"] == "repeat test"
    assert cfg["var1"] == ["This is a repeat test test", "repeat test", "test"]
    assert cfg["var4"] == ["test", ["repeat test"], 1]

    assert cfg.get_list("var1") == ["This is a repeat test test", "repeat test", "test"]


def test_interpolation_on_set():  # type: ignore
    cfg = config(SET1, SET2, lowercase_keys=True, interpolate=True)

    assert cfg["var3"] == "test"
    assert cfg["var2"] == "is a test"
    assert cfg["var1"] == "This is a test"
    assert cfg.var1 == "This is a test"
