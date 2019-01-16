from config import config_from_dict, config_from_env
import os


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

PREFIX = 'PYTHONCONFIG'

os.environ.update(
    (PREFIX + '__' + k.replace('.', '__').upper(), str(v))
    for k, v in DICT.items()
)


def test_load_env():  # type: ignore
    cfg = config_from_env(PREFIX)
    assert cfg["a1.b1.c1"] == '1'
    assert cfg["a1.b1"].get_int('c1') == 1
    assert cfg["a1.b1"].as_dict() == {"c1": '1', "c2": '2', "c3": '3'}
    assert cfg["a1.b2"].as_dict() == {"c1": "a", "c2": 'True', "c3": '1.1'}


def test_equality():  # type: ignore
    cfg = config_from_env(PREFIX)
    assert cfg == config_from_dict(dict((k, str(v)) for k, v in DICT.items()))
