from collections import namedtuple
from typing import Any, Dict
import pytest
from pytest import raises

from config import config_from_dict

try:
    from google.cloud import secretmanager_v1
    from google.api_core.exceptions import NotFound
    from config.contrib.gcp import GCPSecretManagerConfiguration
except ImportError:  # pragma: no cover
    secretmanager_v1 = None  # type: ignore


DICT = {
    "foo": "foo_val",
    "bar": "bar_val",
    "with_underscore": "works",
    "password": "some passwd",
}

DICT2 = {"a": "b", "c": "d"}

Payload = namedtuple("Payload", ["data"])


class Secret:
    def __init__(self, name: str, value: str):
        self.name = name
        self.payload = Payload(value.encode())


class FakeSecretClient:
    def __init__(self, dct: dict):
        self._dict = dct

    def list_secrets(self, request: Dict[str, str]) -> list:
        return [Secret(f"prefix/{x}", "") for x in self._dict.keys()]

    def access_secret_version(self, request: Dict[str, str]) -> Secret:
        name = request["name"]
        try:
            return Secret(name, self._dict[name.split("/")[3]])
        except KeyError:
            raise NotFound("")  # type: ignore


def fake_client(val: dict) -> Any:
    def call(*args: list, **kwargs: dict) -> FakeSecretClient:
        return FakeSecretClient(val)

    return call


@pytest.mark.skipif("secretmanager_v1 is None")
def test_load_dict():  # type: ignore
    secretmanager_v1.SecretManagerServiceClient = fake_client(DICT)
    cfg = GCPSecretManagerConfiguration("fake_id")
    assert cfg["foo"] == "foo_val"
    assert cfg["with_underscore"] == "works"
    assert cfg.get("foo", "default") == "foo_val"


@pytest.mark.skipif("secretmanager_v1 is None")
def test_expiration(mocker):  # type: ignore
    # with cache
    secretmanager_v1.SecretManagerServiceClient = fake_client(DICT)
    cfg = GCPSecretManagerConfiguration("fake_id")

    spy = mocker.spy(cfg._client, "access_secret_version")
    assert cfg["foo"] == "foo_val"
    assert cfg["foo"] == "foo_val"
    assert spy.call_count == 1

    # without cache
    secretmanager_v1.SecretManagerServiceClient = fake_client(DICT)
    cfg = GCPSecretManagerConfiguration("fake_id", cache_expiration=0)

    spy = mocker.spy(cfg._client, "access_secret_version")
    assert cfg["foo"] == "foo_val"
    assert cfg["foo"] == "foo_val"  # this will ignore the cache
    assert spy.call_count == 2


@pytest.mark.skipif("secretmanager_v1 is None")
def test_deletion():  # type: ignore
    d = DICT.copy()
    secretmanager_v1.SecretManagerServiceClient = fake_client(d)
    cfg = GCPSecretManagerConfiguration("fake_id", cache_expiration=0)

    assert cfg["foo"] == "foo_val"
    assert "foo" in cfg._cache
    del d["foo"]

    with raises(KeyError):
        assert cfg["foo"] is KeyError


@pytest.mark.skipif("secretmanager_v1 is None")
def test_missing_key():  # type: ignore
    d = DICT.copy()
    secretmanager_v1.SecretManagerServiceClient = fake_client(d)
    cfg = GCPSecretManagerConfiguration("fake_id", cache_expiration=0)

    with raises(KeyError):
        assert cfg["foo-missing"] is KeyError

    assert cfg.get("foo-missing", "default") == "default"


@pytest.mark.skipif("secretmanager_v1 is None")
def test_get_attr():  # type: ignore
    d = DICT.copy()
    secretmanager_v1.SecretManagerServiceClient = fake_client(d)
    cfg = GCPSecretManagerConfiguration("fake_id", cache_expiration=0)

    assert cfg.foo == "foo_val"

    with raises(AttributeError):
        assert cfg.foo_missing is AttributeError


@pytest.mark.skipif("secretmanager_v1 is None")
def test_dict():  # type: ignore
    d = DICT.copy()
    secretmanager_v1.SecretManagerServiceClient = fake_client(d)
    cfg = GCPSecretManagerConfiguration("fake_id", cache_expiration=0)

    assert sorted(cfg.keys()) == sorted(d.keys())
    assert sorted(cfg.values()) == sorted(d.values())
    assert sorted(cfg.items()) == sorted(d.items())


@pytest.mark.skipif("secretmanager_v1 is None")
def test_repr():  # type: ignore
    d = DICT.copy()
    secretmanager_v1.SecretManagerServiceClient = fake_client(d)
    cfg = GCPSecretManagerConfiguration("fake_id", cache_expiration=0)

    assert repr(cfg) == "<GCPSecretManagerConfiguration: 'fake_id'>"


@pytest.mark.skipif("secretmanager_v1 is None")
def test_str():  # type: ignore
    d = DICT.copy()
    secretmanager_v1.SecretManagerServiceClient = fake_client(d)
    cfg = GCPSecretManagerConfiguration("fake_id", cache_expiration=0)

    # str
    assert (
        str(cfg)
        == "{'bar': 'bar_val', 'foo': 'foo_val', 'password': '******', 'with_underscore': 'works'}"
    )
    assert cfg["password"] == "some passwd"


@pytest.mark.skipif("secretmanager_v1 is None")
def test_reload():  # type: ignore
    secretmanager_v1.SecretManagerServiceClient = fake_client(DICT)
    cfg = GCPSecretManagerConfiguration("fake_id")
    assert cfg == config_from_dict(DICT)

    cfg._client = FakeSecretClient(DICT2)
    cfg.reload()
    assert cfg == config_from_dict(DICT2)
