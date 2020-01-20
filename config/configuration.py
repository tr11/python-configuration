"""Configuration class."""

import base64
from typing import (
    Any,
    Dict,
    ItemsView,
    Iterator,
    KeysView,
    Mapping,
    Optional,
    Tuple,
    Union,
    ValuesView,
    cast,
)

from .helpers import as_bool, clean


class Configuration:
    """
    Configuration class.

    The Configuration class takes a dictionary input with keys such as

        - ``a1.b1.c1``
        - ``a1.b1.c2``
        - ``a1.b2.c1``
        - ``a1.b2.c2``
        - ``a2.b1.c1``
        - ``a2.b1.c2``
        - ``a2.b2.c1``
        - ``a2.b2.c2``
    """

    def __init__(self, config_: Mapping[str, Any], lowercase_keys: bool = False):
        """
        Constructor.

        :param config_: a mapping of configuration values. Keys need to be strings.
        :param lowercase_keys: whether to convert every key to lower case.
        """
        self._lowercase = lowercase_keys
        self._config: Dict[str, Any] = self._flatten_dict(config_)

    def __eq__(self, other):  # type: ignore
        """Equality operator."""
        return self.as_dict() == other.as_dict()

    def _filter_dict(self, d: Dict[str, Any], prefix: str) -> Dict[str, Any]:
        """
        Filter a dictionary and return the items that are prefixed by :attr:`prefix`.

        :param d: dictionary
        :param prefix: prefix to filter on
        """
        if self._lowercase:
            return {
                k[(len(prefix) + 1) :].lower(): v
                for k, v in d.items()
                if k.startswith(prefix + ".")
            }
        else:
            return {
                k[(len(prefix) + 1) :]: v
                for k, v in d.items()
                if k.startswith(prefix + ".")
            }

    def _flatten_dict(self, d: Mapping[str, Any]) -> Dict[str, Any]:
        """
        Flatten one level of a dictionary.

        :param d: dict
        :return: a flattened dict
        """
        nested = {k for k, v in d.items() if isinstance(v, dict)}
        if self._lowercase:
            result = {
                k.lower() + "." + ki: vi
                for k in nested
                for ki, vi in self._flatten_dict(d[k]).items()
            }
            result.update(
                (k.lower(), v) for k, v in d.items() if not isinstance(v, dict)
            )
        else:
            result = {
                k + "." + ki: vi
                for k in nested
                for ki, vi in self._flatten_dict(d[k]).items()
            }
            result.update((k, v) for k, v in d.items() if not isinstance(v, dict))
        return result

    def _get_subset(self, prefix: str) -> Union[Dict[str, Any], Any]:
        """
        Return the subset of the config dictionary whose keys start with :attr:`prefix`.

        :param prefix: string
        :return: dict
        """
        d = {
            k[(len(prefix) + 1) :]: v
            for k, v in self._config.items()
            if k.startswith(prefix + ".")
        }
        if not d:
            prefixes = prefix.split(".")
            if len(prefixes) == 1:
                return self._config.get(prefix, {})
            d = self._config
            while prefixes:  # pragma: no branches
                p = prefixes[0]
                new_d = self._filter_dict(d, p)
                if new_d == {}:
                    return d.get(p, {}) if len(prefixes) == 1 else {}
                d = new_d
                prefixes = prefixes[1:]
        return d

    def __getitem__(self, item: str) -> Union["Configuration", Any]:  # noqa: D105
        v = self._get_subset(item)
        if v == {}:
            raise KeyError(item)
        return Configuration(v) if isinstance(v, dict) else v

    def __getattr__(self, item: str) -> Any:  # noqa: D105
        v = self._get_subset(item)
        if v == {}:
            raise KeyError(item)
        return Configuration(v) if isinstance(v, dict) else v

    def get(self, key: str, default: Any = None) -> Union[dict, Any]:
        """
        Get the configuration values corresponding to :attr:`key`.

        :param key: key to retrieve
        :param default: default value in case the key is missing
        :return: the value found or a default
        """
        return self.as_dict().get(key, default)

    def as_dict(self) -> dict:
        """Return the representation as a dictionary."""
        return self._config

    def get_bool(self, item: str) -> bool:
        """
        Get the item value as a bool.

        :param item: key
        """
        return as_bool(self[item])

    def get_str(self, item: str, fmt: str = "{}") -> str:
        """
        Get the item value as an int.

        :param item: key
        :param fmt: format to use
        """
        return fmt.format(self[item])

    def get_int(self, item: str) -> int:
        """
        Get the item value as an int.

        :param item: key
        """
        return int(self[item])

    def get_float(self, item: str) -> float:
        """
        Get the item value as a float.

        :param item: key
        """
        return float(self[item])

    def get_dict(self, item: str) -> dict:
        """
        Get the item values as a dictionary.

        :param item: key
        """
        return dict(self._get_subset(item))

    def base64encode(self, item: str) -> bytes:
        """
        Get the item value as a Base64 encoded bytes instance.

        :param item: key
        """
        b = self[item]
        b = b if isinstance(b, bytes) else b.encode()
        return base64.b64encode(b)

    def base64decode(self, item: str) -> bytes:
        """
        Get the item value as a Base64 decoded bytes instance.

        :param item: key
        """
        b = self[item]
        b = b if isinstance(b, bytes) else b.encode()
        return base64.b64decode(b, validate=True)

    def keys(
        self, levels: Optional[int] = None
    ) -> Union["Configuration", Any, KeysView[str]]:
        """Return a set-like object providing a view on the configuration keys."""
        assert levels is None or levels > 0
        try:
            return self["keys"]  # don't filter levels, existing attribute
        except KeyError:
            return cast(
                KeysView[str],
                list(
                    {
                        ".".join(x.split(".")[:levels])
                        for x in set(self.as_dict().keys())
                    }
                ),
            )

    def values(
        self, levels: Optional[int] = None
    ) -> Union["Configuration", Any, ValuesView[Any]]:
        """Return a set-like object providing a view on the configuration values."""
        assert levels is None or levels > 0
        try:
            return self["values"]
        except KeyError:
            return dict(self.items(levels=levels)).values()

    def items(
        self, levels: Optional[int] = None
    ) -> Union["Configuration", Any, ItemsView[str, Any]]:
        """Return a set-like object providing a view on the configuration items."""
        assert levels is None or levels > 0
        try:
            return self["items"]
        except KeyError:
            keys = cast(KeysView[str], self.keys(levels=levels))
            return {k: self._get_subset(k) for k in keys}.items()

    def __iter__(self) -> Iterator[Tuple[str, Any]]:  # noqa: D105
        return iter(self.keys())  # type: ignore

    def __reversed__(self) -> Iterator[Tuple[str, Any]]:  # noqa: D105
        return reversed(self.keys())  # type: ignore

    def __len__(self) -> int:  # noqa: D105
        return len(self._config)

    def __setitem__(self, key: str, value: Any) -> None:  # noqa: D105
        self.update({key: value})

    def __delitem__(self, prefix: str) -> None:  # noqa: D105
        """
        Filter a dictionary and delete the items that are prefixed by :attr:`prefix`.

        :param prefix: prefix to filter on to delete keys
        """
        remove = []
        for k in self._config:
            kl = k.lower() if self._lowercase else k
            if kl == prefix or kl.startswith(prefix + "."):
                remove.append(k)
        if not remove:
            raise KeyError("No key with prefix '%s' found." % prefix)
        for k in remove:
            del self._config[k]

    def __contains__(self, prefix: str) -> bool:  # noqa: D105
        try:
            self[prefix]
            return True
        except KeyError:
            return False

    def clear(self) -> None:
        """Remove all items."""
        self._config.clear()

    def copy(self) -> "Configuration":
        """Return shallow copy."""
        return Configuration(self._config)

    def pop(self, prefix: str, value: Any = None) -> Any:
        """
        Remove keys with the specified prefix and return the corresponding value.

        If the prefix is not found a KeyError is raised.
        """
        try:
            value = self[prefix]
            del self[prefix]
        except KeyError:
            if value is None:
                raise
        return value

    def setdefault(self, key: str, default: Any = None) -> Any:
        """
        Insert key with a value of default if key is not in the Configuration.

        Return the value for key if key is in the Configuration, else default.
        """
        try:
            return self[key]
        except KeyError:
            self[key] = default
        return self[key]

    def update(self, other: Mapping[str, Any]) -> None:
        """Update the Configuration with another Configuration object or Mapping."""
        self._config.update(self._flatten_dict(other))

    def reload(self) -> None:  # pragma: no cover
        """
        Reload the configuration.

        This method is not implemented for simple Configuration objects and is
        intended only to be used in subclasses.
        """
        raise NotImplementedError()

    def __repr__(self) -> str:  # noqa: D105
        return "<Configuration: %s>" % hex(id(self))

    def __str__(self) -> str:  # noqa: D105
        return str({k: clean(k, v) for k, v in sorted(self.items())})
