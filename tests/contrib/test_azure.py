from dataclasses import dataclass
from collections import namedtuple
from pytest import raises

try:
    import azure
    from config.contrib.azure import AzureKeyVaultConfiguration
    from azure.core.exceptions import ResourceNotFoundError
except ImportError:  # pragma: no cover
    azure = None


DICT = {"foo": "foo_val", "bar": "bar_val", "with-underscore": "works"}

FakeKeySecret = namedtuple("FakeKeySecret", ["key", "value"])


if azure:

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

    def test_load_dict():  # type: ignore
        cfg = AzureKeyVaultConfiguration(
            "fake_id", "fake_secret", "fake_tenant", "fake_vault"
        )
        cfg._kv_client = FakeSecretClient(DICT)
        assert cfg["foo"] == "foo_val"
        assert cfg["with_underscore"] == "works"
        assert cfg.get("foo", "default") == "foo_val"

    def test_expiration(mocker):  # type: ignore
        # with cache
        cfg = AzureKeyVaultConfiguration(
            "fake_id", "fake_secret", "fake_tenant", "fake_vault"
        )
        cfg._kv_client = FakeSecretClient(DICT)

        spy = mocker.spy(cfg._kv_client, "get_secret")
        assert cfg["foo"] == "foo_val"
        assert cfg["foo"] == "foo_val"
        assert spy.call_count == 1

        # without cache
        cfg = AzureKeyVaultConfiguration(
            "fake_id", "fake_secret", "fake_tenant", "fake_vault", cache_expiration=0
        )
        cfg._kv_client = FakeSecretClient(DICT)

        spy = mocker.spy(cfg._kv_client, "get_secret")
        assert cfg["foo"] == "foo_val"
        assert cfg["foo"] == "foo_val"  # this will ignore the cache
        assert spy.call_count == 2

    def test_deletion():  # type: ignore
        cfg = AzureKeyVaultConfiguration(
            "fake_id", "fake_secret", "fake_tenant", "fake_vault", cache_expiration=0
        )
        d = DICT.copy()
        cfg._kv_client = FakeSecretClient(d)

        assert cfg["foo"] == "foo_val"
        assert "foo" in cfg._cache
        del d["foo"]

        with raises(KeyError):
            assert cfg["foo"] is KeyError

    def test_missing_key():  # type: ignore
        cfg = AzureKeyVaultConfiguration(
            "fake_id", "fake_secret", "fake_tenant", "fake_vault", cache_expiration=0
        )
        d = DICT.copy()
        cfg._kv_client = FakeSecretClient(d)

        with raises(KeyError):
            assert cfg["foo-missing"] is KeyError

        assert cfg.get("foo-missing", "default") == "default"

    def test_get_attr():  # type: ignore
        cfg = AzureKeyVaultConfiguration(
            "fake_id", "fake_secret", "fake_tenant", "fake_vault", cache_expiration=0
        )
        d = DICT.copy()
        cfg._kv_client = FakeSecretClient(d)

        assert cfg.foo == "foo_val"

        with raises(KeyError):
            assert cfg.foo_missing is KeyError

    def test_dict():  # type: ignore
        cfg = AzureKeyVaultConfiguration(
            "fake_id", "fake_secret", "fake_tenant", "fake_vault", cache_expiration=0
        )
        d = DICT.copy()
        cfg._kv_client = FakeSecretClient(d)

        assert sorted(cfg.keys()) == sorted(d.keys())
        assert sorted(cfg.values()) == sorted(d.values())
        assert sorted(cfg.items()) == sorted(d.items())

    def test_repr():  # type: ignore
        cfg = AzureKeyVaultConfiguration(
            "fake_id", "fake_secret", "fake_tenant", "fake_vault", cache_expiration=0
        )
        d = DICT.copy()
        cfg._kv_client = FakeSecretClient(d)

        assert repr(cfg) == "<AzureKeyVaultConfiguration: 'vault URL'>"
