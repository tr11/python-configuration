from config import config_from_dict, config


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
    "a1": {"b1": {"c1": 1, "C2": 2, "c3": 3}, "b2": {"c1": "a", "c2": True, "c3": 1.1}}
}


def test_load_from_config():  # type: ignore
    cfg1 = config_from_dict(DICT, lowercase_keys=True)
    cfg2 = config_from_dict(NESTED, lowercase_keys=True)

    assert config(DICT, NESTED, lowercase_keys=True ) == config(cfg1, NESTED, lowercase_keys=True )
    assert config(DICT, NESTED, lowercase_keys=True ) == config(DICT, cfg2, lowercase_keys=True )
    assert config(DICT, NESTED, lowercase_keys=True ) == config(cfg1, cfg2, lowercase_keys=True )
