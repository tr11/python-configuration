"""Configuration from GCP Secret Manager."""

import time
from typing import Any, Dict, ItemsView, KeysView, Optional, Union, ValuesView, cast

from google.api_core.client_options import ClientOptions
from google.api_core.exceptions import NotFound
from google.auth.credentials import Credentials
from google.cloud import secretmanager_v1

from .. import Configuration, InterpolateType


class Cache:
    """Cache class."""

    def __init__(self, value: str, ts: float):  # noqa: D107
        self.value = value
        self.ts = ts


class GCPSecretManagerConfiguration(Configuration):
    """
    GCP Secret Manager Configuration class.

    The GCP Secret Manager Configuration class takes GCP Secret Manager credentials and
    behaves like a drop-in replacement for the regular Configuration class.

    The following limitations apply to the GCP Secret Manager Configurations:
        - keys must conform to the pattern '^[0-9a-zA-Z-_]+$'. In particular,
          there is no support for levels and nested values as there are no
          natural key separators for the pattern above.
        - values must be strings.
    """

    def __init__(
        self,
        project_id: str,
        credentials: Credentials = None,
        client_options: Optional[ClientOptions] = None,
        cache_expiration: int = 5 * 60,
        interpolate: InterpolateType = False,
    ) -> None:
        """
        Constructor.

        See https://googleapis.dev/python/secretmanager/latest/gapic/v1/api.html#google.cloud.secretmanager_v1.SecretManagerServiceClient
        for more details on credentials and options.

        :param project_id: GCP Project ID
        :param credentials: GCP credentials
        :param client_options: GCP client_options
        :param cache_expiration: Cache expiration (in seconds)
        """  # noqa: E501
        self._client = secretmanager_v1.SecretManagerServiceClient(
            credentials=credentials, client_options=client_options
        )
        self._project_id = project_id
        self._parent = f"projects/{project_id}"
        self._cache_expiration = cache_expiration
        self._cache: Dict[str, Cache] = {}
        self._interpolate = {} if interpolate is True else interpolate
        self._default_levels = None

    def _get_secret(self, key: str) -> Optional[str]:
        now = time.time()
        from_cache = self._cache.get(key)
        if from_cache and from_cache.ts + self._cache_expiration > now:
            return from_cache.value
        try:
            path = f"projects/{self._project_id}/secrets/{key}/versions/latest"
            secret = self._client.access_secret_version(
                request={"name": path}
            ).payload.data.decode()
            self._cache[key] = Cache(value=secret, ts=now)
            return cast(str, secret)
        except NotFound:
            if key in self._cache:
                del self._cache[key]
            return None

    def __getitem__(self, item: str) -> Any:  # noqa: D105
        secret = self._get_secret(item)
        if secret is None:
            raise KeyError(item)
        else:
            return secret

    def __getattr__(self, item: str) -> Any:  # noqa: D105
        secret = self._get_secret(item)
        if secret is None:
            raise KeyError(item)
        else:
            return secret

    def get(self, key: str, default: Any = None) -> Union[dict, Any]:
        """
        Get the configuration values corresponding to :attr:`key`.

        :param key: key to retrieve
        :param default: default value in case the key is missing
        :return: the value found or a default
        """
        secret = self._get_secret(key)
        if secret is None:
            return default
        else:
            return secret

    def keys(
        self, levels: Optional[int] = None
    ) -> Union["Configuration", Any, KeysView[str]]:
        """Return a set-like object providing a view on the configuration keys."""
        assert not levels  # GCP Secret Manager secrets don't support separators
        return cast(
            KeysView[str],
            (
                k.name.split("/")[-1]
                for k in self._client.list_secrets(request={"parent": self._parent})
            ),
        )

    def values(
        self, levels: Optional[int] = None
    ) -> Union["Configuration", Any, ValuesView[Any]]:
        """Return a set-like object providing a view on the configuration values."""
        assert not levels  # GCP Secret Manager secrets don't support separators
        return cast(
            ValuesView[str],
            (
                self._get_secret(k.name.split("/")[-1])
                for k in self._client.list_secrets(request={"parent": self._parent})
            ),
        )

    def items(
        self, levels: Optional[int] = None
    ) -> Union["Configuration", Any, ItemsView[str, Any]]:
        """Return a set-like object providing a view on the configuration items."""
        assert not levels  # GCP Secret Manager secrets don't support separators
        return cast(
            ItemsView[str, Any],
            (
                (k.name.split("/")[-1], self._get_secret(k.name.split("/")[-1]))
                for k in self._client.list_secrets(request={"parent": self._parent})
            ),
        )

    def reload(self) -> None:
        """Reload the configuration."""
        self._cache.clear()

    def __repr__(self) -> str:  # noqa: D105
        return "<GCPSecretManagerConfiguration: %r>" % self._project_id

    @property
    def _config(self) -> Dict[str, Any]:  # type: ignore
        return dict(self.items())
