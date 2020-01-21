from config import config_from_dict, config_from_json
import tempfile
import json


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
JSON = json.dumps(DICT)


def test_load_json():  # type: ignore
    cfg = config_from_json(JSON)
    assert cfg["a1.b1.c1"] == 1
    assert cfg["a1.b1"].as_dict() == {"c1": 1, "c2": 2, "c3": 3}
    assert cfg["a1.b2"].as_dict() == {"c1": "a", "c2": True, "c3": 1.1}


def test_load_json_file():  # type: ignore
    with tempfile.NamedTemporaryFile() as f:
        f.file.write(JSON.encode())
        f.file.flush()
        cfg = config_from_json(open(f.name, "rt"), read_from_file=True)
    assert cfg["a1.b1.c1"] == 1
    assert cfg["a1.b1"].as_dict() == {"c1": 1, "c2": 2, "c3": 3}
    assert cfg["a1.b2"].as_dict() == {"c1": "a", "c2": True, "c3": 1.1}
    assert cfg == config_from_dict(DICT)


def test_load_json_filename():  # type: ignore
    with tempfile.NamedTemporaryFile() as f:
        f.file.write(JSON.encode())
        f.file.flush()
        cfg = config_from_json(f.name, read_from_file=True)
    assert cfg["a1.b1.c1"] == 1
    assert cfg["a1.b1"].as_dict() == {"c1": 1, "c2": 2, "c3": 3}
    assert cfg["a1.b2"].as_dict() == {"c1": "a", "c2": True, "c3": 1.1}
    assert cfg == config_from_dict(DICT)


def test_equality():  # type: ignore
    cfg = config_from_json(JSON)
    assert cfg == config_from_dict(DICT)


def test_reload_json():  # type: ignore
    with tempfile.NamedTemporaryFile() as f:
        f.file.write(JSON.encode())
        f.file.flush()
        cfg = config_from_json(f.name, read_from_file=True)
        assert cfg == config_from_dict(DICT)

        f.file.seek(0)
        f.file.truncate(0)
        f.file.write(b'{"test": 1}')
        f.file.flush()
        cfg.reload()
        assert cfg == config_from_dict({"test": 1})
