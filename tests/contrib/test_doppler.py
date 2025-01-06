r"""
Tests for Doppler secret service integration.

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

# ruff: noqa: D103, D107, I001

from datetime import timedelta
from time import sleep
from typing import List, Dict, Any, Optional, Set, Union
from unittest.mock import MagicMock

import pytest

try:
    import dopplersdk as doppler
    from config.contrib.doppler import DopplerConfiguration
except ImportError:  # pragma: no cover
    doppler = None

ACCESS_TOKEN = "dp.st.dev.MockTokenForUnitTestsXXXXXXXXXXXXXXXXXXXXXX"

DOPPLER_PROJECT_CONFIG: Dict[str, str] = {
    "DOPPLER_PROJECT": "doppler-testing-mock",
    "DOPPLER_ENVIRONMENT": "dev",
    "DOPPLER_CONFIG": "dev_local",
}

ENV_DATA: Dict[str, Any] = {
    "VALUE_1": "A simple string value.",
    "ANOTHER_VALUE": "Something else.",
}

REQUESTED_SECRETS: List[str] = [
    "VALUE_1",
]

SECRET_LISTS: Dict[str, Optional[Union[str, List[str]]]] = {
    "none": None,
    "string": "VALUE_1",
    "string-list": ["VALUE_1"],
    "string-list-multi": ["VALUE_1", "ANOTHER_VALUE"],
    "string-csv": "VALUE_1,ANOTHER_VALUE",
}

class DopplerSecretServiceMock:
    r"""Mock the Doppler `Service` class."""
    class SecretsListResponseMock:
        r"""Mock the response type from call to list secrets."""
        def __init__(self, data: dict):
            self._data = data
        @property
        def secrets(self) -> List[str]:  # noqa: D102
            return list(self._data.keys()) if self._data else []

    class SecretsGetResponseMock:
        r"""Mock the response type from call to get a secret."""
        def __init__(self, value: Any):
            self._value = value
        @property
        def value(self) -> Dict[str, str]:  # noqa: D102
            return {
                "computed": self._value,
            }

    def __init__(self) -> None:
        self._project: str = DOPPLER_PROJECT_CONFIG["DOPPLER_PROJECT"]
        self._env: str = DOPPLER_PROJECT_CONFIG["DOPPLER_ENVIRONMENT"]
        self._config: str = DOPPLER_PROJECT_CONFIG["DOPPLER_CONFIG"]
        self._data: Dict[str, Any] = DOPPLER_PROJECT_CONFIG.copy()
        self._data.update(ENV_DATA)

    def get(self, name: str, project: str, config: str) -> SecretsGetResponseMock:  # noqa: D102
        return DopplerSecretServiceMock.SecretsGetResponseMock(self._data.get(name))

    def list(  # noqa: D102
            self,
            project: str,
            config: str,
            secrets: Optional[str] = None,
    ) -> SecretsListResponseMock:
        if secrets is None:
            return DopplerSecretServiceMock.SecretsListResponseMock(self._data)
        key_filter: Set[str] = set(secrets.split(","))
        key_filter.update(DOPPLER_PROJECT_CONFIG.keys())
        filtered_data: Dict[str, Any] = {
            k: v
            for k, v in self._data.items()
            if k in key_filter
        }
        return DopplerSecretServiceMock.SecretsListResponseMock(
            filtered_data,
        )

@pytest.mark.skipif("doppler is None")
def apply_doppler_config_mocks() -> None:
    mock_class = DopplerConfiguration
    def mock_get_doppler_secrets_client(access_token: str) -> DopplerSecretServiceMock:
        return DopplerSecretServiceMock()
    mock_class._get_doppler_secrets_client = mock_get_doppler_secrets_client  # type: ignore[method-assign]

@pytest.mark.skipif("doppler is None")
@pytest.mark.parametrize("secrets", SECRET_LISTS.values())
def test_constructor(secrets: Optional[Union[str, List[str]]]) -> None:
    apply_doppler_config_mocks()

    parameters: Dict[str, Any] = {}
    parameters.update({"secrets": secrets})
    instance: DopplerConfiguration = DopplerConfiguration(
        access_token=ACCESS_TOKEN,
        project=DOPPLER_PROJECT_CONFIG["DOPPLER_PROJECT"],
        config=DOPPLER_PROJECT_CONFIG["DOPPLER_CONFIG"],
        **parameters,
    )
    assert isinstance(instance, DopplerConfiguration)

    # if secrets is None:
    #     assert len(instance.as_dict()) > 0

    def check_moar_things() -> None:
        requested_keys: Set[str] = set(instance._requested_secrets)
        env_keys: Set[str] = set(ENV_DATA.keys())
        doppler_keys: Set[str] = set(DOPPLER_PROJECT_CONFIG.keys())
        all_keys = env_keys.union(doppler_keys)
        keys: Set[str] = set(instance.keys())  # type: ignore[arg-type]

        all_values: Dict[str, Any] = ENV_DATA.copy()
        all_values.update(DOPPLER_PROJECT_CONFIG.copy())
        selected_values: Dict[str, Any] = {
            k: v
            for (k, v) in all_values.items()
            if (
                    len(requested_keys) == 0
                    or k in requested_keys
            )
        }

        # Check for expected keys
        if len(requested_keys) == 0:
            assert keys == all_keys
        else:
            assert len(keys.symmetric_difference(requested_keys)) == 0

        # check for correct dictionary values
        dc_dict: Dict[str, Any] = instance.as_dict()
        if len(requested_keys) == 0:
            # All keys from the env and doppler vars should be present in the dict
            assert dc_dict == all_values
        else:
            assert dc_dict == selected_values

    check_moar_things()


@pytest.fixture
@pytest.mark.skipif("doppler is None")
def doppler_config() -> "DopplerConfiguration":  # type: ignore[misc]
    apply_doppler_config_mocks()

    dc: DopplerConfiguration = DopplerConfiguration(
        access_token=ACCESS_TOKEN,
        project=DOPPLER_PROJECT_CONFIG["DOPPLER_PROJECT"],
        config=DOPPLER_PROJECT_CONFIG["DOPPLER_CONFIG"],
        secrets=REQUESTED_SECRETS,
    )
    dc._doppler_client = DopplerSecretServiceMock()
    yield dc

@pytest.mark.skipif("doppler is None")
def test_cache_expiration(doppler_config) -> None:  # type: ignore[misc, no-untyped-def]
    variable_key_name: str = set(ENV_DATA.keys()).pop()

    # set a short expiration so we don't wait too long for the test
    short_expiration_time: float = .1
    doppler_config._cache_duration = timedelta(seconds=short_expiration_time)
    doppler_config.reload()

    doppler_config._get_doppler_config_values = MagicMock("_get_doppler_config_values")

    doppler_config.get(variable_key_name)
    doppler_config._get_doppler_config_values.assert_not_called()

    sleep(short_expiration_time)
    doppler_config.get(variable_key_name)
    doppler_config._get_doppler_config_values.assert_called()

@pytest.mark.skipif("doppler is None")
def test_expiration_duration_none() -> None:
    apply_doppler_config_mocks()
    dc: DopplerConfiguration = DopplerConfiguration(
        access_token=ACCESS_TOKEN,
        project=DOPPLER_PROJECT_CONFIG["DOPPLER_PROJECT"],
        config=DOPPLER_PROJECT_CONFIG["DOPPLER_CONFIG"],
        secrets=None,
        cache_expiration=None,
    )
    variable_key_name: str = set(ENV_DATA.keys()).pop()
    variable_value: str = str(dc.get(variable_key_name, ""))
    assert variable_value == ENV_DATA.get(variable_key_name)

@pytest.mark.skipif("doppler is None")
def test_repr(doppler_config) -> None:  # type: ignore[misc, no-untyped-def]
    expected_repr = r"""<DopplerConfiguration: doppler-testing-mock | dev_local>"""
    assert doppler_config.__repr__() == expected_repr
