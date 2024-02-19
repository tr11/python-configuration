from collections import namedtuple
import pytest
from pytest import raises

from config import config_from_dict

try:
    import azure
    from config.contrib.azure import AzureKeyVaultConfiguration
    from azure.core.exceptions import ResourceNotFoundError
except ImportError:  # pragma: no cover
    azure = None  # type: ignore


DICT = {
    "foo": "foo_val",
    "bar": "bar_val",
    "with-underscore": "works",
    "password": "some passwd",
}

DICT2 = {"a": "b", "c": "d"}

FakeKeySecret = namedtuple("FakeKeySecret", ["key", "value"])


class Secret:
    def __init__(self, name: str, value: str):
        self.name = name
        self.value = value


class FakeSecretClient:
    vault_url = "vault URL"

    def __init__(self, dct: dict):
        self._dict = dct

    def get_secret(self, key: str) -> FakeKeySecret:
        if "_" in key:
            raise ValueError("Azure Key Vault doesn't take underscores.")
        if key in self._dict:
            return FakeKeySecret(key, self._dict[key])
        else:
            raise ResourceNotFoundError()

    def list_properties_of_secrets(self) -> list:
        return [Secret(name=k, value=v) for k, v in self._dict.items()]


@pytest.mark.skipif("azure is None")
def test_load_dict():  # type: ignore
    cfg = AzureKeyVaultConfiguration(
        "fake_id", "fake_secret", "fake-tenant", "fake_vault"
    )
    cfg._kv_client = FakeSecretClient(DICT)
    assert cfg["foo"] == "foo_val"
    assert cfg["with_underscore"] == "works"
    assert cfg.get("foo", "default") == "foo_val"


@pytest.mark.skipif("azure is None")
def test_expiration(mocker):  # type: ignore
    # with cache
    cfg = AzureKeyVaultConfiguration(
        "fake_id", "fake_secret", "fake-tenant", "fake_vault"
    )
    cfg._kv_client = FakeSecretClient(DICT)

    spy = mocker.spy(cfg._kv_client, "get_secret")
    assert cfg["foo"] == "foo_val"
    assert cfg["foo"] == "foo_val"
    assert spy.call_count == 1

    # without cache
    cfg = AzureKeyVaultConfiguration(
        "fake_id", "fake_secret", "fake-tenant", "fake_vault", cache_expiration=0
    )
    cfg._kv_client = FakeSecretClient(DICT)

    spy = mocker.spy(cfg._kv_client, "get_secret")
    assert cfg["foo"] == "foo_val"
    assert cfg["foo"] == "foo_val"  # this will ignore the cache
    assert spy.call_count == 2


@pytest.mark.skipif("azure is None")
def test_deletion():  # type: ignore
    cfg = AzureKeyVaultConfiguration(
        "fake_id", "fake_secret", "fake-tenant", "fake_vault", cache_expiration=0
    )
    d = DICT.copy()
    cfg._kv_client = FakeSecretClient(d)

    assert cfg["foo"] == "foo_val"
    assert "foo" in cfg._cache
    del d["foo"]

    with raises(KeyError):
        assert cfg["foo"] is KeyError


@pytest.mark.skipif("azure is None")
def test_missing_key():  # type: ignore
    cfg = AzureKeyVaultConfiguration(
        "fake_id", "fake_secret", "fake-tenant", "fake_vault", cache_expiration=0
    )
    d = DICT.copy()
    cfg._kv_client = FakeSecretClient(d)

    with raises(KeyError):
        assert cfg["foo-missing"] is KeyError

    assert cfg.get("foo-missing", "default") == "default"


@pytest.mark.skipif("azure is None")
def test_get_attr():  # type: ignore
    cfg = AzureKeyVaultConfiguration(
        "fake_id", "fake_secret", "fake-tenant", "fake_vault", cache_expiration=0
    )
    d = DICT.copy()
    cfg._kv_client = FakeSecretClient(d)

    assert cfg.foo == "foo_val"

    with raises(AttributeError):
        assert cfg.foo_missing is AttributeError


@pytest.mark.skipif("azure is None")
def test_dict():  # type: ignore
    cfg = AzureKeyVaultConfiguration(
        "fake_id", "fake_secret", "fake-tenant", "fake_vault", cache_expiration=0
    )
    d = DICT.copy()
    cfg._kv_client = FakeSecretClient(d)

    assert sorted(cfg.keys()) == sorted(d.keys())
    assert sorted(cfg.values()) == sorted(d.values())
    assert sorted(cfg.items()) == sorted(d.items())


@pytest.mark.skipif("azure is None")
def test_repr():  # type: ignore
    cfg = AzureKeyVaultConfiguration(
        "fake_id", "fake_secret", "fake-tenant", "fake_vault", cache_expiration=0
    )
    d = DICT.copy()
    cfg._kv_client = FakeSecretClient(d)

    assert repr(cfg) == "<AzureKeyVaultConfiguration: 'vault URL'>"


@pytest.mark.skipif("azure is None")
def test_str():  # type: ignore
    cfg = AzureKeyVaultConfiguration(
        "fake_id", "fake_secret", "fake-tenant", "fake_vault", cache_expiration=0
    )
    d = DICT.copy()
    cfg._kv_client = FakeSecretClient(d)

    # str
    assert (
        str(cfg)
        == "{'bar': 'bar_val', 'foo': 'foo_val', 'password': '******', 'with-underscore': 'works'}"
    )
    assert cfg["password"] == "some passwd"


@pytest.mark.skipif("azure is None")
def test_reload():  # type: ignore
    cfg = AzureKeyVaultConfiguration(
        "fake_id", "fake_secret", "fake-tenant", "fake_vault"
    )
    cfg._kv_client = FakeSecretClient(DICT)
    assert cfg == config_from_dict(DICT)

    cfg._kv_client = FakeSecretClient(DICT2)
    cfg.reload()
    assert cfg == config_from_dict(DICT2)
