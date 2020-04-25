"""Helper functions."""

import string
from typing import Any, Set, Tuple


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


def interpolate(text: str, d: dict) -> str:
    """
    Return the string interpolated as many times as needed.

    :param text: string possibly containing an interpolation pattern
    :param d: dictionary
    """
    all_variables: Set[Tuple[str, ...]] = set()
    variables: Tuple[str, ...] = ("",)

    while variables:
        variables = tuple(
            sorted(x[1] for x in string.Formatter().parse(text) if x[1] is not None)
        )
        if variables in all_variables:
            raise ValueError("Cycle detected while interpolating keys")
        all_variables.add(variables)
        text = text.format(**d)

    return text


def interpolate_object(obj: Any, d: dict) -> Any:
    """
    Return the interpolated object.

    :param obj: object to interpolate
    :param d: dictionary
    """
    if isinstance(obj, str):
        return interpolate(obj, d)
    elif hasattr(obj, "__iter__"):
        return [interpolate_object(x, d) for x in obj]
    else:
        return obj
