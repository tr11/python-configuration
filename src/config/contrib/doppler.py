r"""
Configuration object connected to Doppler config.

Copyright (c) 2024 Matthew Galbraith

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

# ruff: noqa: I001

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Union, Optional

from dopplersdk.models import SecretsGetResponse, SecretsListResponse
from dopplersdk.services.secrets import Secrets

from .. import Configuration


class DopplerConfiguration(Configuration):
    r"""Configuration class for use with Doppler, https://www.doppler.com/."""
    _doppler_vars: List[str] = [
        "DOPPLER_CONFIG",
        "DOPPLER_ENVIRONMENT",
        "DOPPLER_PROJECT",
    ]

    def __init__(
            self,
            access_token: str,
            project: str,
            config: str,
            secrets: Optional[Union[str, Iterable[str], None]]  = None,
            cache_expiration: Optional[Union[float, int]] = 5 * 60,
            suppress_exceptions: bool = False,
            **kwargs: Dict[str, Any],
    ):
        r"""
        Construct a Configuration subclass for Doppler.

        Parameters:
        access_token: User or Service token to access Doppler.
        project: Doppler project name.
        config: Doppler config name.
        secrets: Either a CSV string or a list of secret names to include. If None, all
            secrets for the config will be included.
        cache_expiration: Cache expiration (in seconds)
        suppress_exceptions: Suppress exceptions raised by calls to the Doppler service.
        """
        # Doppler-specific fields
        self._doppler_client = DopplerConfiguration._get_doppler_secrets_client(
            access_token=access_token,
        )
        self._doppler_project = project
        self._doppler_config_name = config
        self._requested_secrets: List[str]
        if isinstance(secrets, str):
            self._requested_secrets = secrets.split(",")
        else:
            self._requested_secrets = list(secrets or [])
        self._suppress_exceptions = suppress_exceptions

        # Cache fields
        self._cache_duration: Optional[timedelta] = None
        self._cache_expiration: Optional[datetime] = None
        if cache_expiration:
            self._cache_duration = timedelta(seconds=float(cache_expiration))
        self._cache: Optional[Dict[str, Any]] = None

        # call the super init with config_ == {} since we've implemented
        #   _config as a property
        super().__init__({}, **kwargs)  # type: ignore[arg-type]

        # perform initial read of the Doppler config and cache the results
        self.reload()

    @staticmethod
    def _get_doppler_secrets_client(access_token: str) -> Secrets:  # type: ignore[misc]
        r"""Wrap Doppler Secrets client constructor to enable mock testing."""
        return Secrets(access_token=access_token)  # pragma: no cover

    def _reset_expiration(self) -> None:
        if self._cache_duration:
            expire_at = datetime.now(tz=timezone.utc) + self._cache_duration
            self._cache_expiration = expire_at

    def _is_cache_expired(self) -> bool:
        if self._cache_expiration is None:
            return False
        return datetime.now(tz=timezone.utc) >= self._cache_expiration

    def __repr__(self) -> str:
        r"""Construct repr value from class name and configuration values."""
        class_name = self.__class__.__name__
        project_name = self._doppler_project or "NONE"
        config_name = self._doppler_config_name or "NONE"
        return f"<{class_name}: {project_name} | {config_name}>"

    def _get_doppler_keys(self) -> Iterable[str]:
        r"""List all keys available in the Doppler config."""
        parameters: Dict[str, Any] = {
            "config": self._doppler_config_name,
            "project": self._doppler_project,
        }
        if self._requested_secrets:
            parameters["secrets"] = ",".join(self._requested_secrets)
        response: SecretsListResponse = self._doppler_client.list(
            **parameters,
        )
        _keys: List[str] = []
        for secret_name in response.secrets:
            if (
                secret_name in self._requested_secrets
                or len(self._requested_secrets or []) == 0
            ):
                _keys.append(secret_name)
        return _keys

    def _get_doppler_value(self, item: str) -> Any:
        r"""Get single value from the Doppler config."""
        value: Any = None
        try:
            response: SecretsGetResponse = self._doppler_client.get(
                name=item,
                project=self._doppler_project,
                config=self._doppler_config_name,
            )
            value = response.value.get("computed")
        except Exception:  # pragma: no cover
            if not self._suppress_exceptions:
                raise

        return value

    def _get_doppler_config_values(self) -> Dict[str, Any]:
        r"""Get all values from Doppler config."""
        config_values: Dict[str, Any] = {}
        try:
            for key in self._get_doppler_keys():
                config_values[key] = self._get_doppler_value(key)
        except TypeError:  # pragma: no cover
            pass
        except Exception:  # pragma: no cover
            if not self._suppress_exceptions:
                raise
        return config_values

    @property
    def _config(self) -> Dict[str, Any]:  # type: ignore[misc]
        r"""Override Configuration._config to enable cache management."""
        if self._cache is None or self._is_cache_expired():
            self.reload()
        return (self._cache or {}).copy()

    @_config.setter
    def _config(self, value: Any) -> None:
        r"""Ignore attempts to set _config to override related base-class behaviors."""
        return

    def reload(self) -> None:
        r"""Remove cached values and requery the Doppler service."""
        config_values = self._get_doppler_config_values()
        self._reset_expiration()
        self._cache = self._flatten_dict(config_values)

    def as_dict(self) -> Dict[str, Any]:
        r"""Return a copy of internal the dictionary."""
        return self._config.copy()
