import tempfile

import pytest

from config import config_from_dict

try:
    import toml

    from config import config_from_toml
except ImportError:
    toml = None
    config_from_toml = None  # type: ignore


DICT = {
    "a1.b1.c1": 1,
    "a1.b1.c2": 2,
    "a1.b1.c3": 3,
    "a1.b2.c1": "a",
    "a1.b2.c2": True,
    "a1.b2.c3": 1.1,
    "a2.b1.c1": "f",
    "a2.b1.c2": False,
    "a2.b1.c3": "",
    "a2.b2.c1": 10,
    "a2.b2.c2": "YWJjZGVmZ2g=",
    "a2.b2.c3": "abcdefgh",
}

if toml:
    TOML = toml.dumps(DICT)

    TOML2 = """
[owner]
name = "ABC"
dob = 1979-05-27T07:32:00Z
[database]
server = "192.168.1.1"
ports = [ 8001, 8001, 8002,]
connection_max = 5000
enabled = true
[clients]
data = [ [ "gamma", "delta",], [ 1, 2,],]
hosts = [ "alpha", "omega",]
[servers.alpha]
ip = "10.0.0.1"
dc = "eqdc10"
[servers.beta]
ip = "10.0.0.2"
dc = "eqdc10"
"""


@pytest.mark.skipif("toml is None")
def test_load_toml():  # type: ignore
    cfg = config_from_toml(TOML)
    assert cfg["a1.b1.c1"] == 1
    assert cfg["a1.b1"].as_dict() == {"c1": 1, "c2": 2, "c3": 3}
    assert cfg["a1.b2"].as_dict() == {"c1": "a", "c2": True, "c3": 1.1}


@pytest.mark.skipif("toml is None")
def test_load_toml_2():  # type: ignore
    cfg = config_from_toml(TOML2)
    assert cfg["owner.name"] == "ABC"
    assert cfg["servers"].as_dict() == {
        "alpha.dc": "eqdc10",
        "alpha.ip": "10.0.0.1",
        "beta.dc": "eqdc10",
        "beta.ip": "10.0.0.2",
    }
    assert cfg["clients.data"] == [["gamma", "delta"], [1, 2]]


@pytest.mark.skipif("toml is None")
def test_load_toml_file():  # type: ignore
    with tempfile.NamedTemporaryFile() as f:
        f.file.write(TOML.encode())
        f.file.flush()
        cfg = config_from_toml(open(f.name, "rb"), read_from_file=True)
    assert cfg["a1.b1.c1"] == 1
    assert cfg["a1.b1"].as_dict() == {"c1": 1, "c2": 2, "c3": 3}
    assert cfg["a1.b2"].as_dict() == {"c1": "a", "c2": True, "c3": 1.1}
    assert cfg == config_from_dict(DICT)


@pytest.mark.skipif("toml is None")
def test_load_toml_filename():  # type: ignore
    with tempfile.NamedTemporaryFile() as f:
        f.file.write(TOML.encode())
        f.file.flush()
        cfg = config_from_toml(f.name, read_from_file=True)
    assert cfg["a1.b1.c1"] == 1
    assert cfg["a1.b1"].as_dict() == {"c1": 1, "c2": 2, "c3": 3}
    assert cfg["a1.b2"].as_dict() == {"c1": "a", "c2": True, "c3": 1.1}
    assert cfg == config_from_dict(DICT)


@pytest.mark.skipif("toml is None")
def test_equality():  # type: ignore
    cfg = config_from_toml(TOML)
    assert cfg == config_from_dict(DICT)


@pytest.mark.skipif("toml is None")
def test_reload_toml():  # type: ignore
    with tempfile.NamedTemporaryFile() as f:
        f.file.write(TOML.encode())
        f.file.flush()
        cfg = config_from_toml(f.name, read_from_file=True)
        assert cfg == config_from_dict(DICT)

        f.file.seek(0)
        f.file.truncate(0)
        f.file.write(b'[owner]\nname = "ABC"\n')
        f.file.flush()
        cfg.reload()
        assert cfg == config_from_dict({"owner.name": "ABC"})


@pytest.mark.skipif("toml is None")
def test_reload_toml_with_section_prefix():  # type: ignore
    with tempfile.NamedTemporaryFile() as f:
        toml_input = """
[tool.coverage.run]
branch = false
parallel = false
[database]
server = "192.168.1.1"
ports = [ 8001, 8001, 8002,]
"""

        f.file.write(toml_input.encode())
        f.file.flush()

        cfg = config_from_toml(
            f.name,
            section_prefix="tool.coverage.",
            read_from_file=True,
        )
        expected = config_from_dict(
            {
                "run.branch": False,
                "run.parallel": False,
            },
        )

        assert cfg == expected

        f.file.seek(0)
        f.file.truncate(0)
        f.file.write(b"[tool.coverage.report]\nignore_errors = false\n")
        f.file.flush()
        cfg.reload()
        expected = config_from_dict(
            {
                "report.ignore_errors": False,
            },
        )
        assert cfg == expected
