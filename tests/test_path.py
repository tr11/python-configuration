from config import config_from_path, config_from_dict, create_path_from_config
import tempfile


DICT = {
    "a1.b1.c1": 1,
    "a1.b1.c2": 2,
    "a1.b1.c3": 3,
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


def _config_from_temp_path(dic, remove_level=0):  # type: ignore
    import os
    with tempfile.TemporaryDirectory() as folder:
        lvl = remove_level
        subfolder = folder
        while lvl > 0:
            subfolder += '/sub'
            os.makedirs(subfolder)
            lvl -= 1
        create_path_from_config(subfolder, config_from_dict(dic),
                                remove_level=remove_level)
        cfg = config_from_path(folder, remove_level=remove_level)
        walk = list(os.walk(folder))
    return cfg, folder, walk


def _config_from_temp_path_with_trailing_slash(dic, remove_level=0):  # type: ignore
    import os
    with tempfile.TemporaryDirectory() as folder:
        lvl = remove_level
        subfolder = folder
        while lvl > 0:
            subfolder += '/sub'
            os.makedirs(subfolder)
            lvl -= 1
        create_path_from_config(subfolder, config_from_dict(dic),
                                remove_level=remove_level)
        folder += '/'
        cfg = config_from_path(folder, remove_level=remove_level)
        walk = list(os.walk(folder))
    return cfg, folder, walk


def test_load_path():  # type: ignore
    cfg, folder, walk = _config_from_temp_path(DICT, remove_level=0)
    assert set(walk[0][2]) == set(DICT.keys())
    assert cfg["a1.b1"].get_int("c1") == 1
    assert cfg["a1.b1"].as_dict() == {"c1": '1', "c2": '2', "c3": '3'}
    assert cfg["a1.b2"].as_dict() == {"c1": "a", "c2": 'True', "c3": '1.1'}


def test_load_path_with_trailing_slash():
    cfg, folder, walk = _config_from_temp_path_with_trailing_slash(DICT, remove_level=0)
    assert set(walk[0][2]) == set(DICT.keys())
    assert cfg["a1.b1"].get_int("c1") == 1
    assert cfg["a1.b1"].as_dict() == {"c1": '1', "c2": '2', "c3": '3'}
    assert cfg["a1.b2"].as_dict() == {"c1": "a", "c2": 'True', "c3": '1.1'}


def test_equality():  # type: ignore
    cfg, folder, walk = _config_from_temp_path(DICT, remove_level=0)
    assert cfg == config_from_dict(dict((k, str(v)) for k, v in DICT.items()))


def test_load_path_level():  # type: ignore
    cfg, folder, walk = _config_from_temp_path(DICT, remove_level=1)
    assert walk[0][0] == folder
    assert walk[0][2] == []
    assert set(walk[1][2]) == set(DICT.keys())
    assert cfg["a1.b1"].get_int("c1") == 1
    assert cfg["a1.b1"].as_dict() == {"c1": '1', "c2": '2', "c3": '3'}
    assert cfg["a1.b2"].as_dict() == {"c1": "a", "c2": 'True', "c3": '1.1'}


def test_load_path_level_2():  # type: ignore
    cfg, folder, walk = _config_from_temp_path(DICT, remove_level=2)
    assert walk[0][0] == folder
    assert walk[0][2] == []
    assert walk[1][0] == folder + '/sub'
    assert walk[1][2] == []
    assert set(walk[2][2]) == set(DICT.keys())
    assert cfg["a1.b1"].get_int("c1") == 1
    assert cfg["a1.b1"].as_dict() == {"c1": '1', "c2": '2', "c3": '3'}
    assert cfg["a1.b2"].as_dict() == {"c1": "a", "c2": 'True', "c3": '1.1'}
