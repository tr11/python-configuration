from config.azure import AzureKeyVaultConfiguration
from azure.core.exceptions import ResourceNotFoundError
from collections import namedtuple
from pytest import raises
import pytest


DICT = {"foo": "foo_val", "bar": "bar_val", "with-underscore": "works"}

FakeKeySecret = namedtuple("FakeKeySecret", ["key", "value"])


class FakeSecretClient:
    def __init__(self, dct: dict):
        self._dict = dct

    def get_secret(self, key: str) -> FakeKeySecret:
        if "_" in key:
            raise ValueError("Azure Key Vault doesn't take underscores.")
        if key in self._dict:
            return FakeKeySecret(key, self._dict[key])
        else:
            raise ResourceNotFoundError()


def test_load_dict():  # type: ignore
    cfg = AzureKeyVaultConfiguration(
        "fake_id", "fake_secret", "fake_tenant", "fake_vault"
    )
    cfg._kv_client = FakeSecretClient(DICT)
    assert cfg["foo"] == "foo_val"
    assert cfg["with_underscore"] == "works"
