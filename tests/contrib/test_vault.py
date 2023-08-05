from collections import namedtuple
import pytest
from pytest import raises

from config import config_from_dict

try:
    import hvac
    from config.contrib.vault import HashicorpVaultConfiguration
except ImportError:  # pragma: no cover
    hvac = None

DICT = {
    "foo": "foo_val",
    "bar": "bar_val",
    "with_underscore": "works",
    "password": "some passwd",
}

DICT2 = {"a": "b", "c": "d"}

FakeKeySecret = namedtuple("FakeKeySecret", ["key", "value"])


class FakeSecretClient:
    def __init__(self, engine, dct: dict):  # type: ignore
        self._engine = engine
        self._dict = dct

    @property
    def kv(self):  # type: ignore
        return self

    @property
    def v2(self):  # type: ignore
        return self

    def read_secret(self, secret, mount_point):  # type: ignore
        if mount_point == self._engine:
            return {"data": {"data": config_from_dict(self._dict[secret]).as_dict()}}
        else:
            raise KeyError

    def list(self, path):  # type: ignore
        return {"data": {"keys": list(self._dict.keys())}}


@pytest.mark.skipif("hvac is None")
def test_load_dict():  # type: ignore
    cfg = HashicorpVaultConfiguration("engine")
    cfg._client = FakeSecretClient("engine", {"k": DICT})

    assert cfg["k"]["foo"] == "foo_val"
    assert cfg["k"]["with_underscore"] == "works"
    assert cfg.get("k.foo", "default") == "foo_val"


@pytest.mark.skipif("hvac is None")
def test_expiration(mocker):  # type: ignore
    # with cache
    cfg = HashicorpVaultConfiguration("engine")
    cfg._client = FakeSecretClient("engine", {"k": DICT})

    spy = mocker.spy(cfg._client, "read_secret")
    assert cfg["k"]["foo"] == "foo_val"
    assert cfg["k"]["foo"] == "foo_val"
    assert spy.call_count == 1

    # without cache
    cfg = HashicorpVaultConfiguration("engine", cache_expiration=0)
    cfg._client = FakeSecretClient("engine", {"k": DICT})

    spy = mocker.spy(cfg._client, "read_secret")
    assert cfg["k"]["foo"] == "foo_val"
    assert cfg["k"]["foo"] == "foo_val"  # this will ignore the cache
    assert spy.call_count == 2


@pytest.mark.skipif("hvac is None")
def test_deletion():  # type: ignore
    cfg = HashicorpVaultConfiguration("engine", cache_expiration=0)
    d = DICT.copy()
    dd = {"k": d, "a": d}
    cfg._client = FakeSecretClient("engine", dd)

    assert cfg.k["foo"] == "foo_val"
    assert "k" in cfg._cache
    del dd["k"]

    with raises(KeyError):
        assert cfg["k"] is KeyError


@pytest.mark.skipif("hvac is None")
def test_missing_key():  # type: ignore
    cfg = HashicorpVaultConfiguration("engine")
    d = DICT.copy()
    cfg._client = FakeSecretClient("engine", {"k": d})

    with raises(KeyError):
        assert cfg["not-k"] is KeyError

    with raises(KeyError):
        assert cfg["k"]["foo-missing"] is KeyError

    assert cfg.get("k.foo-missing", "default") == "default"


@pytest.mark.skipif("hvac is None")
def test_get_attr():  # type: ignore
    cfg = HashicorpVaultConfiguration("engine")
    d = DICT.copy()
    cfg._client = FakeSecretClient("engine", {"k": d})

    assert cfg.k.foo == "foo_val"

    with raises(AttributeError):
        assert cfg.notk is AttributeError

    with raises(AttributeError):
        assert cfg.k.foo_missing is AttributeError


@pytest.mark.skipif("hvac is None")
def test_dict():  # type: ignore
    cfg = HashicorpVaultConfiguration("engine")
    d = DICT.copy()
    cfg._client = FakeSecretClient("engine", {"k": d, "a": d})

    assert sorted(cfg.keys()) == sorted({"k": d, "a": d}.keys())
    assert list(cfg.values()) == [d, d]
    assert sorted(cfg.items()) == sorted({"k": d, "a": d}.items())


@pytest.mark.skipif("hvac is None")
def test_repr():  # type: ignore
    cfg = HashicorpVaultConfiguration("engine")
    d = DICT.copy()
    cfg._client = FakeSecretClient("engine", {"k": d})

    assert repr(cfg) == "<HashicorpVaultConfiguration: 'engine'>"


@pytest.mark.skipif("hvac is None")
def test_str():  # type: ignore
    cfg = HashicorpVaultConfiguration("engine")
    d = DICT.copy()
    cfg._client = FakeSecretClient("engine", {"k": d})

    # str
    assert (
        str(cfg)
        == "{'k.bar': 'bar_val', 'k.foo': 'foo_val', 'k.password': '******', 'k.with_underscore': 'works'}"
    )
    assert cfg["k.password"] == "some passwd"


@pytest.mark.skipif("hvac is None")
def test_reload():  # type: ignore
    cfg = HashicorpVaultConfiguration("engine")
    d = DICT.copy()
    cfg._client = FakeSecretClient("engine", {"k": d})
    assert cfg == config_from_dict({"k": DICT})

    cfg._client = FakeSecretClient("engine", {"k": DICT2})
    cfg.reload()
    assert cfg == config_from_dict({"k": DICT2})
