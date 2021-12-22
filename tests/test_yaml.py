import pytest
from config import config_from_dict
from pytest import raises
import tempfile

try:
    import yaml
    from config import config_from_yaml
except ImportError:
    yaml = None
    config_from_yaml = None  # type: ignore


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

if yaml:
    YAML = yaml.dump(DICT)

    YAML2 = """
# Employee records
martin:
    name: Martin D'vloper
    job: Developer
    skills:
      - python
      - perl
      - pascal
tabitha:
    name: Tabitha Bitumen
    job: Developer
    skills:
      - lisp
      - fortran
      - erlang
"""

    YAML3 = """
- test:
    a: b
    c: d
- test2:
    a: b
    c: d
"""


@pytest.mark.skipif("yaml is None")
def test_load_yaml():  # type: ignore
    cfg = config_from_yaml(YAML)
    assert cfg["a1.b1.c1"] == 1
    assert cfg["a1.b1"].as_dict() == {"c1": 1, "c2": 2, "c3": 3}
    assert cfg["a1.b2"].as_dict() == {"c1": "a", "c2": True, "c3": 1.1}


@pytest.mark.skipif("yaml is None")
def test_load_yaml_2():  # type: ignore
    cfg = config_from_yaml(YAML2)
    assert cfg["martin.name"] == "Martin D'vloper"
    assert cfg["martin"].as_dict() == {
        "job": "Developer",
        "name": "Martin D'vloper",
        "skills": ["python", "perl", "pascal"],
    }
    assert cfg["martin.skills"] == ["python", "perl", "pascal"]


@pytest.mark.skipif("yaml is None")
def test_fails():  # type: ignore
    with raises(ValueError):
        config_from_yaml(YAML3)


@pytest.mark.skipif("yaml is None")
def test_load_yaml_file():  # type: ignore
    with tempfile.NamedTemporaryFile() as f:
        f.file.write(YAML.encode())
        f.file.flush()
        cfg = config_from_yaml(open(f.name, "rt"), read_from_file=True)
    assert cfg["a1.b1.c1"] == 1
    assert cfg["a1.b1"].as_dict() == {"c1": 1, "c2": 2, "c3": 3}
    assert cfg["a1.b2"].as_dict() == {"c1": "a", "c2": True, "c3": 1.1}
    assert cfg == config_from_dict(DICT)


@pytest.mark.skipif("yaml is None")
def test_load_yaml_filename():  # type: ignore
    with tempfile.NamedTemporaryFile() as f:
        f.file.write(YAML.encode())
        f.file.flush()
        cfg = config_from_yaml(f.name, read_from_file=True)
    assert cfg["a1.b1.c1"] == 1
    assert cfg["a1.b1"].as_dict() == {"c1": 1, "c2": 2, "c3": 3}
    assert cfg["a1.b2"].as_dict() == {"c1": "a", "c2": True, "c3": 1.1}
    assert cfg == config_from_dict(DICT)


@pytest.mark.skipif("yaml is None")
def test_equality():  # type: ignore
    cfg = config_from_yaml(YAML)
    assert cfg == config_from_dict(DICT)


@pytest.mark.skipif("yaml is None")
def test_reload_yaml():  # type: ignore
    with tempfile.NamedTemporaryFile() as f:
        f.file.write(YAML.encode())
        f.file.flush()
        cfg = config_from_yaml(f.name, read_from_file=True)
        assert cfg == config_from_dict(DICT)

        f.file.seek(0)
        f.file.truncate(0)
        f.file.write(YAML2.encode())
        f.file.flush()
        cfg.reload()
        assert cfg == config_from_yaml(YAML2)
