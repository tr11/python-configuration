"""Helper functions."""

from typing import Any


TRUTH_TEXT = frozenset(("t", "true", "y", "yes", "on", "1"))
FALSE_TEXT = frozenset(("f", "false", "n", "no", "off", "0", ""))
PROTECTED_KEYS = frozenset(("secret", "password", "passwd", "pwd"))


def as_bool(s: Any) -> bool:
    """
    Boolean value from an object.

    Return the boolean value ``True`` if the case-lowered value of string
    input ``s`` is a `truthy string`. If ``s`` is already one of the
    boolean values ``True`` or ``False``, return it.
    """
    if s is None:
        return False
    if isinstance(s, bool):
        return s
    s = str(s).strip().lower()
    if s not in TRUTH_TEXT and s not in FALSE_TEXT:
        raise ValueError("Expected a valid True or False expression.")
    return s in TRUTH_TEXT


def clean(key: str, value: Any, mask: str = "******") -> Any:
    """
    Mask a value if needed.

    :param key: key
    :param value: value to hide
    :param mask: string to use in case value should be hidden
    :return: clear value or mask
    """
    key = key.lower()
    # check for protected keys
    for pk in PROTECTED_KEYS:
        if pk in key:
            return mask
    # urls
    if isinstance(value, str) and "://" in value:
        from urllib.parse import urlparse

        url = urlparse(value)
        if url.password is None:
            return value
        else:
            return url._replace(
                netloc="{}:{}@{}".format(url.username, mask, url.hostname)
            ).geturl()
    return value
