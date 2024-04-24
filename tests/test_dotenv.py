import pytest
from config import config, config_from_dotenv, config_from_dict
import tempfile

DOTENV = """
KEY1 = abc
KEY2 = def
KEY3 = 1.1
"""

DOTENV_WITH_PREFIXES = """
PREFIX__KEY1 = abc
PREFIX__KEY2 = def
PREFIX__KEY3 = 1.1
NOTPREFIX__KEY = 2
PREFIX__KEY4__A = 1
PREFIX__KEY4__B = 2
PREFIX__KEY4__C = 3
"""

DOTENV_WITH_COMMENTS = """
# key 1
KEY1 = abc
# key 2
KEY2 = def
# key 3
KEY3 = 1.1
"""

DICT = {
    "key1": "abc",
    "key2": "def",
    "key3": "1.1",
}

DICT_WITH_PREFIXES = {
    "key1": "abc",
    "key2": "def",
    "key3": "1.1",
    "key4": {
        "a": "1",
        "b": "2",
        "c": "3",
    },
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


def test_load_dotenv_config():  # type: ignore
    with tempfile.NamedTemporaryFile(suffix='.env') as f:
        f.file.write(DOTENV_WITH_PREFIXES.encode())
        f.file.flush()
        cfg = config(f.name, lowercase_keys=True, prefix="PREFIX")

    print(cfg)
    print(config_from_dict(DICT_WITH_PREFIXES))
    assert cfg == config_from_dict(DICT_WITH_PREFIXES)



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


def test_load_dotenv():  # type: ignore
    cfg = config_from_dotenv(DOTENV_WITH_PREFIXES, lowercase_keys=True, prefix="PREFIX")
    print(cfg.as_dict())
    assert cfg == config_from_dict(DICT_WITH_PREFIXES)


def test_load_dotenv_comments():  # type: ignore
    cfg = config_from_dotenv(DOTENV_WITH_COMMENTS, lowercase_keys=True)
    assert cfg == config_from_dict(dict((k, str(v)) for k, v in DICT.items()))


def test_load_dotenv_comments_invalid():  # type: ignore
    invalid = """
# key 1
VALID=1
## key2
INVALID
"""
    with pytest.raises(ValueError) as err:
        config_from_dotenv(invalid, lowercase_keys=True)
    assert 'Invalid line INVALID' in str(err)

