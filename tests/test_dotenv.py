from config import config_from_dotenv, config_from_dict
import tempfile

DOTENV = """
KEY1 = abc
KEY2 = def
KEY3 = 1.1
"""

DICT = {
    "key1": "abc",
    "key2": "def",
    "key3": "1.1",
}


def test_load_dotenv():  # type: ignore
    cfg = config_from_dotenv(DOTENV, lowercase_keys=True)
    assert cfg == config_from_dict(dict((k, str(v)) for k, v in DICT.items()))


def test_load_dotenv_file():  # type: ignore
    with tempfile.NamedTemporaryFile() as f:
        f.file.write(DOTENV.encode())
        f.file.flush()
        cfg = config_from_dotenv(
            open(f.name, "rt"), read_from_file=True, lowercase_keys=True
        )
    assert cfg == config_from_dict(dict((k, str(v)) for k, v in DICT.items()))


def test_load_dotenv_filename():  # type: ignore
    with tempfile.NamedTemporaryFile() as f:
        f.file.write(DOTENV.encode())
        f.file.flush()
        cfg = config_from_dotenv(f.name, read_from_file=True, lowercase_keys=True)
    assert cfg == config_from_dict(dict((k, str(v)) for k, v in DICT.items()))


def test_reload():  # type: ignore
    with tempfile.NamedTemporaryFile() as f:
        f.file.write(DOTENV.encode())
        f.file.flush()
        cfg = config_from_dotenv(
            open(f.name, "rt"), read_from_file=True, lowercase_keys=True
        )

        assert cfg == config_from_dict(dict((k, str(v)) for k, v in DICT.items()))

        f.file.write(b"\nkey10 = 1\n")
        f.file.flush()
        cfg = config_from_dotenv(
            open(f.name, "rt"), read_from_file=True, lowercase_keys=True
        )
        cfg2 = config_from_dict(dict((k, str(v)) for k, v in DICT.items()))
        cfg2["key10"] = "1"
        assert cfg == cfg2
