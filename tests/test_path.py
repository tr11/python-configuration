from config import config_from_path, config_from_dict, create_path_from_config
import tempfile


DICT = {
    "a1.b1.c1": 1,
    "a1.b1.c2": 2,
    "a1.b1.c3": 3,
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


def _config_from_temp_path(dic, remove_level=0, trailing_slash=False):  # type: ignore
    import os

    with tempfile.TemporaryDirectory() as folder:
        lvl = remove_level
        subfolder = folder
        while lvl > 0:
            subfolder += "/sub"
            os.makedirs(subfolder)
            lvl -= 1
        create_path_from_config(
            subfolder, config_from_dict(dic), remove_level=remove_level
        )
        if trailing_slash:
            folder += "/"
        cfg = config_from_path(folder, remove_level=remove_level)
        cfg2 = config_from_path(folder, remove_level=remove_level)
        walk = list(os.walk(folder))

        # add an extra element to test reloads
        d = dic.copy()
        d["extra.value"] = 1
        create_path_from_config(
            subfolder, config_from_dict(d), remove_level=remove_level
        )
        cfg2.reload()

    return cfg, folder, walk, cfg2


def test_load_path():  # type: ignore
    cfg, folder, walk, _ = _config_from_temp_path(DICT, remove_level=0)
    assert set(walk[0][2]) == set(DICT.keys())
    assert cfg["a1.b1"].get_int("c1") == 1
    assert cfg["a1.b1"].as_dict() == {"c1": "1", "c2": "2", "c3": "3"}
    assert cfg["a1.b2"].as_dict() == {"c1": "a", "c2": "True", "c3": "1.1"}


def test_load_path_with_trailing_slash():  # type: ignore
    cfg, folder, walk, _ = _config_from_temp_path(
        DICT, remove_level=0, trailing_slash=True
    )
    assert set(walk[0][2]) == set(DICT.keys())
    assert cfg["a1.b1"].get_int("c1") == 1
    assert cfg["a1.b1"].as_dict() == {"c1": "1", "c2": "2", "c3": "3"}
    assert cfg["a1.b2"].as_dict() == {"c1": "a", "c2": "True", "c3": "1.1"}


def test_equality():  # type: ignore
    cfg, folder, walk, _ = _config_from_temp_path(DICT, remove_level=0)
    assert cfg == config_from_dict(dict((k, str(v)) for k, v in DICT.items()))


def test_load_path_level():  # type: ignore
    cfg, folder, walk, _ = _config_from_temp_path(DICT, remove_level=1)
    assert walk[0][0] == folder
    assert walk[0][2] == []
    assert set(walk[1][2]) == set(DICT.keys())
    assert cfg["a1.b1"].get_int("c1") == 1
    assert cfg["a1.b1"].as_dict() == {"c1": "1", "c2": "2", "c3": "3"}
    assert cfg["a1.b2"].as_dict() == {"c1": "a", "c2": "True", "c3": "1.1"}


def test_load_path_level_2():  # type: ignore
    cfg, folder, walk, _ = _config_from_temp_path(DICT, remove_level=2)
    assert walk[0][0] == folder
    assert walk[0][2] == []
    assert walk[1][0] == folder + "/sub"
    assert walk[1][2] == []
    assert set(walk[2][2]) == set(DICT.keys())
    assert cfg["a1.b1"].get_int("c1") == 1
    assert cfg["a1.b1"].as_dict() == {"c1": "1", "c2": "2", "c3": "3"}
    assert cfg["a1.b2"].as_dict() == {"c1": "a", "c2": "True", "c3": "1.1"}


def test_reload():  # type: ignore
    cfg, folder, walk, cfg2 = _config_from_temp_path(DICT, remove_level=0)
    assert cfg == config_from_dict(dict((k, str(v)) for k, v in DICT.items()))
    cfg["extra.value"] = "1"
    assert cfg2 == cfg
