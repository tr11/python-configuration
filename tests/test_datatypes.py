from config import config, config_from_dict


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
