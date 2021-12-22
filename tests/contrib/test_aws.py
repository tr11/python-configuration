import pytest
import json
from pytest import raises


try:
    import boto3 as aws
    from config.contrib.aws import AWSSecretsManagerConfiguration
except ImportError:  # pragma: no cover
    aws = None


DICT = {
    "foo": "foo_val",
    "bar": "bar_val",
    "test.a": "val_a",
    "test.b": "val_b",
    "password": "some passwd",
}

DICT2 = {"a": "b", "c": "d"}


class MockSession:
    def __init__(self, val, *args, **kwargs):  # type: ignore
        self._value = val

    class Client:
        def __init__(self, val):  # type: ignore
            self._value = val

        def get_secret_value(self, SecretId: str):  # type: ignore
            return {"SecretString": json.dumps(self._value)}

    def client(self, *args, **kwargs):  # type: ignore
        return self.Client(self._value)


class MockSessionFail:
    def __init__(self, val, *args, **kwargs):  # type: ignore
        self._value = val

    class Client:
        def __init__(self, val):  # type: ignore
            self._value = val

        def get_secret_value(self, SecretId: str):  # type: ignore
            return self._value

    def client(self, *args, **kwargs):  # type: ignore
        return self.Client(self._value)


@pytest.mark.skipif("aws is None")
def test_load_dict(mocker):  # type: ignore
    mocker.patch.object(aws.session, "Session", return_value=MockSession(DICT))
    cfg = AWSSecretsManagerConfiguration(secret_name="test-secret")

    assert cfg.as_dict() == DICT


@pytest.mark.skipif("aws is None")
def test_expiration(mocker):  # type: ignore
    mocker.patch.object(aws.session, "Session", return_value=MockSession(DICT))

    # with cache
    cfg = AWSSecretsManagerConfiguration(secret_name="test-secret")
    mocker.patch.object(
        cfg._client, "get_secret_value", return_value={"SecretString": json.dumps(DICT)}
    )
    assert cfg["foo"] == "foo_val"
    cfg._client.get_secret_value.assert_called_once()
    cfg._client.get_secret_value.reset_mock()
    assert cfg["foo"] == "foo_val"
    cfg._client.get_secret_value.assert_not_called()
    mocker.resetall()

    # without cache
    cfg = AWSSecretsManagerConfiguration(secret_name="test-secret", cache_expiration=0)
    mocker.patch.object(
        cfg._client, "get_secret_value", return_value={"SecretString": json.dumps(DICT)}
    )
    assert cfg["foo"] == "foo_val"
    cfg._client.get_secret_value.assert_called()
    cfg._client.get_secret_value.reset_mock()
    assert cfg["foo"] == "foo_val"
    cfg._client.get_secret_value.assert_called()


@pytest.mark.skipif("aws is None")
def test_missing_key(mocker):  # type: ignore
    mocker.patch.object(aws.session, "Session", return_value=MockSession(DICT))
    cfg = AWSSecretsManagerConfiguration(secret_name="test-secret", cache_expiration=0)

    with raises(KeyError):
        assert cfg["foo-missing"] is KeyError

    assert cfg.get("foo-missing", "default") == "default"


@pytest.mark.skipif("aws is None")
def test_get_attr(mocker):  # type: ignore
    mocker.patch.object(aws.session, "Session", return_value=MockSession(DICT))
    cfg = AWSSecretsManagerConfiguration(secret_name="test-secret", cache_expiration=0)

    assert cfg.foo == "foo_val"

    with raises(AttributeError):
        assert cfg.foo_missing is AttributeError


@pytest.mark.skipif("aws is None")
def test_dict(mocker):  # type: ignore
    mocker.patch.object(aws.session, "Session", return_value=MockSession(DICT))
    cfg = AWSSecretsManagerConfiguration(secret_name="test-secret", cache_expiration=0)

    assert sorted(cfg.keys()) == sorted(DICT.keys())
    assert sorted(cfg.values()) == sorted(DICT.values())
    assert sorted(cfg.items()) == sorted(DICT.items())

    assert sorted(cfg.keys(levels=1)) == ["bar", "foo", "password", "test"]
    assert sorted(cfg.items(levels=1)) == [
        ("bar", "bar_val"),
        ("foo", "foo_val"),
        ("password", "some passwd"),
        ("test", {"a": "val_a", "b": "val_b"}),
    ]


@pytest.mark.skipif("aws is None")
def test_repr(mocker):  # type: ignore
    mocker.patch.object(aws.session, "Session", return_value=MockSession(DICT))
    cfg = AWSSecretsManagerConfiguration(secret_name="test-secret", cache_expiration=0)
    assert repr(cfg) == "<AWSSecretsManagerConfiguration: 'test-secret'>"


@pytest.mark.skipif("aws is None")
def test_str(mocker):  # type: ignore
    mocker.patch.object(aws.session, "Session", return_value=MockSession(DICT))
    cfg = AWSSecretsManagerConfiguration(secret_name="test-secret", cache_expiration=0)

    # str
    assert (
        str(cfg)
        == "{'bar': 'bar_val', 'foo': 'foo_val', 'password': '******', 'test.a': 'val_a', 'test.b': 'val_b'}"
    )
    assert cfg["password"] == "some passwd"


@pytest.mark.skipif("aws is None")
def test_fail_binary(mocker):  # type: ignore
    mocker.patch.object(aws.session, "Session", return_value=MockSessionFail(DICT))
    cfg = AWSSecretsManagerConfiguration(secret_name="test-secret", cache_expiration=0)

    with raises(ValueError):
        cfg.as_dict()


@pytest.mark.skipif("aws is None")
def test_reload(mocker):  # type: ignore
    mocker.patch.object(aws.session, "Session", return_value=MockSession(DICT))
    cfg = AWSSecretsManagerConfiguration(secret_name="test-secret")
    assert cfg.as_dict() == DICT

    mocker.patch.object(aws.session, "Session", return_value=MockSession(DICT2))
    cfg._client = MockSession(DICT2).client(service_name="secretsmanager")
    cfg.reload()
    assert cfg.as_dict() == DICT2
