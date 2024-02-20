"""Configuration instances from Hashicorp Vault."""

import time
from typing import (
    Any,
    Dict,
    ItemsView,
    KeysView,
    Mapping,
    Optional,
    Union,
    ValuesView,
    cast,
)

import hvac
from hvac.exceptions import InvalidPath

from .. import Configuration, InterpolateType, config_from_dict


class Cache:
    """Cache class."""

    def __init__(self, value: Dict[str, Any], ts: float):  # noqa: D107
        self.value = value
        self.ts = ts


class HashicorpVaultConfiguration(Configuration):
    """Hashicorp Vault Configuration class.

    The Hashicorp Vault Configuration class takes Vault credentials and
    behaves like a drop-in replacement for the regular Configuration class.

    The following limitations apply to the Hashicorp Vault Configurations:
        - only works with KV version 2
        - only supports the latest secret version
        - assumes that secrets are named as <engine name>/<path>/<field>
    """

    def __init__(
        self,
        engine: str,
        cache_expiration: int = 5 * 60,
        interpolate: InterpolateType = False,
        **kwargs: Mapping[str, Any],
    ) -> None:
        """Class Constructor.

        See https://developer.hashicorp.com/vault/docs/get-started/developer-qs.
        """  # noqa: E501
        self._client = hvac.Client(**kwargs)
        self._cache_expiration = cache_expiration
        self._cache: Dict[str, Cache] = {}
        self._engine = engine
        self._interpolate = {} if interpolate is True else interpolate
        self._default_levels = None

    def _get_secret(self, secret: str) -> Optional[Dict[str, Any]]:
        now = time.time()
        from_cache = self._cache.get(secret)
        if from_cache and from_cache.ts + self._cache_expiration > now:
            return from_cache.value
        try:
            data = cast(
                Dict[str, Any],
                self._client.kv.v2.read_secret(secret, mount_point=self._engine)[
                    "data"
                ]["data"],
            )
            self._cache[secret] = Cache(value=data, ts=now)
            return data
        except (InvalidPath, KeyError):
            if secret in self._cache:
                del self._cache[secret]
            return None

    def __getitem__(self, item: str) -> Any:  # noqa: D105
        path, *rest = item.split(".", 1)
        secret = self._get_secret(path)
        if secret is None:
            raise KeyError(item)
        else:
            return (
                Configuration(secret)[".".join(rest)] if rest else Configuration(secret)
            )

    def __getattr__(self, item: str) -> Any:  # noqa: D105
        secret = self._get_secret(item)
        if secret is None:
            raise AttributeError(item)
        else:
            return Configuration(secret)

    def get(self, key: str, default: Any = None) -> Union[dict, Any]:
        """Get the configuration values corresponding to `key`.

        Params:
            key: key to retrieve.
            default: default value in case the key is missing.

        Returns:
            the value found or a default.
        """
        try:
            return self[key]
        except KeyError:
            return default

    def keys(
        self,
        levels: Optional[int] = None,
    ) -> Union["Configuration", Any, KeysView[str]]:
        """Return a set-like object providing a view on the configuration keys."""
        assert not levels  # Vault secrets don't support separators
        return cast(
            KeysView[str],
            self._client.list(f"/{self._engine}/metadata")["data"]["keys"],
        )

    def values(
        self,
        levels: Optional[int] = None,
    ) -> Union["Configuration", Any, ValuesView[Any]]:
        """Return a set-like object providing a view on the configuration values."""
        assert not levels  # GCP Secret Manager secrets don't support separators
        return cast(
            ValuesView[str],
            (
                self._get_secret(k)
                for k in self._client.list(f"/{self._engine}/metadata")["data"]["keys"]
            ),
        )

    def items(
        self,
        levels: Optional[int] = None,
    ) -> Union["Configuration", Any, ItemsView[str, Any]]:
        """Return a set-like object providing a view on the configuration items."""
        assert not levels  # GCP Secret Manager secrets don't support separators
        return cast(
            ItemsView[str, Any],
            (
                (k, self._get_secret(k))
                for k in self._client.list(f"/{self._engine}/metadata")["data"]["keys"]
            ),
        )

    def reload(self) -> None:
        """Reload the configuration."""
        self._cache.clear()

    def __repr__(self) -> str:  # noqa: D105
        return "<HashicorpVaultConfiguration: %r>" % self._engine

    @property
    def _config(self) -> Dict[str, Any]:  # type: ignore
        return config_from_dict(dict(self.items()))._config
