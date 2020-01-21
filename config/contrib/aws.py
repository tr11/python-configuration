"""Configuration from AWS Secrets Manager."""

import json
import time
from typing import Any, Dict, Optional

import boto3

from botocore.exceptions import ClientError


from .. import Configuration


class Cache:
    """Cache class."""

    def __init__(self, value: Dict[str, Any], ts: float):  # noqa: D107
        self.value = value
        self.ts = ts


class AWSSecretsManagerConfiguration(Configuration):
    """
    AWS Configuration class.

    The AWS Configuration class takes AWS Secrets Manager credentials and
    behaves like a drop-in replacement for the regular Configuration class.
    """

    def __init__(
        self,
        secret_name: str,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_session_token: Optional[str] = None,
        region_name: Optional[str] = None,
        profile_name: Optional[str] = None,
        cache_expiration: int = 5 * 60,
        lowercase_keys: bool = False,
    ) -> None:
        """
        Constructor.

        :param secret_name: Name of the secret
        :param aws_access_key_id:  AWS Access Key ID
        :param aws_secret_access_key: AWS Secret Access Key
        :param aws_session_token:  AWS Temporary Session Token
        :param region_name: Region Name
        :param profile_name: Profile Name
        :param cache_expiration: Cache expiration (in seconds)
        :param lowercase_keys: whether to convert every key to lower case.
        """
        self._session = boto3.session.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
            region_name=region_name,
            profile_name=profile_name,
        )
        self._client = self._session.client(service_name="secretsmanager")
        self._secret_name = secret_name
        self._secret: Cache = Cache({}, 0)
        self._expiration: float = cache_expiration
        self._lowercase = lowercase_keys

    @property
    def _config(self) -> Dict[str, Any]:  # type: ignore
        now = time.time()
        if self._secret.ts + self._expiration > now:
            return self._secret.value
        try:
            get_secret_value_response = self._client.get_secret_value(
                SecretId=self._secret_name
            )
        except ClientError as e:  # pragma: no cover
            if e.response["Error"]["Code"] == "DecryptionFailureException":
                # Secrets Manager can't decrypt the protected secret text using
                # the provided KMS key.
                # Deal with the exception here, and/or rethrow at your discretion.
                raise RuntimeError("Cannot read the AWS secret")
            elif e.response["Error"]["Code"] == "InternalServiceErrorException":
                # An error occurred on the server side.
                # Deal with the exception here, and/or rethrow at your discretion.
                raise RuntimeError("Cannot read the AWS secret")
            elif e.response["Error"]["Code"] == "InvalidParameterException":
                # You provided an invalid value for a parameter.
                # Deal with the exception here, and/or rethrow at your discretion.
                raise RuntimeError("Cannot read the AWS secret")
            elif e.response["Error"]["Code"] == "InvalidRequestException":
                # You provided a parameter value that is not valid for the current
                # state of the resource.
                # Deal with the exception here, and/or rethrow at your discretion.
                raise RuntimeError("Cannot read the AWS secret")
            elif e.response["Error"]["Code"] == "ResourceNotFoundException":
                # We can't find the resource that you asked for.
                # Deal with the exception here, and/or rethrow at your discretion.
                raise RuntimeError("Cannot read the AWS secret")
        else:
            # Decrypts secret using the associated KMS CMK.
            # Depending on whether the secret is a string or binary, one of these
            # fields will be populated.
            if "SecretString" in get_secret_value_response:
                secret: str = get_secret_value_response["SecretString"]
            else:
                raise ValueError("Binary AWS secrets are not supported.")

            self._secret = Cache(json.loads(secret), now)
            return self._secret.value

    def reload(self) -> None:
        """Reload the configuration."""
        self._secret = Cache({}, 0)

    def __repr__(self) -> str:  # noqa: D105
        return "<AWSSecretsManagerConfiguration: %r>" % self._secret_name
