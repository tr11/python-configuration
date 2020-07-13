"""ConfigurationSet class."""

from typing import (
    Any,
    Dict,
    ItemsView,
    Iterable,
    KeysView,
    List,
    Mapping,
    Optional,
    Union,
    ValuesView,
    cast,
)

from .configuration import Configuration
from .helpers import InterpolateType, clean, interpolate_object


class ConfigurationSet(Configuration):
    """
    Configuration Sets.

    A class that combines multiple :class:`Configuration` instances
    in a hierarchical manner.
    """

    def __init__(
        self, *configs: Configuration, interpolate: InterpolateType = False
    ):  # noqa: D107
        self._interpolate = {} if interpolate is True else interpolate
        try:
            self._configs: List[Configuration] = list(configs)
        except Exception:  # pragma: no cover
            raise ValueError(
                "configs should be a non-empty iterable of Configuration objects"
            )
        if not self._configs:  # pragma: no cover
            raise ValueError(
                "configs should be a non-empty iterable of Configuration objects"
            )
        if not all(
            isinstance(x, Configuration) for x in self._configs
        ):  # pragma: no cover
            raise ValueError(
                "configs should be a non-empty iterable of Configuration objects"
            )
        self._writable = False

    def _from_configs(self, attr: str, *args: Any, **kwargs: dict) -> Any:
        last_err = Exception()
        values = []
        for config_ in self._configs:
            try:
                values.append(getattr(config_, attr)(*args, **kwargs))
            except Exception as err:
                last_err = err
                continue
        if not values:
            # raise the last error
            raise last_err
        if all(isinstance(v, Configuration) for v in values):
            result: dict = {}
            for v in values[::-1]:
                result.update(v)
            return Configuration(result)
        elif isinstance(values[0], Configuration):
            result = {}
            for v in values[::-1]:
                if not isinstance(v, Configuration):
                    continue
                result.update(v)
            return Configuration(result)
        elif self._interpolate is not False:
            d = {}
            for config_ in self._configs:
                c = config_.as_dict()
                for k, v in c.items():
                    v = interpolate_object(v, d)
                    c[k] = v
                    d.update(c)
            return d[args[0]]
        else:
            return values[0]

    def _writable_config(self) -> Configuration:
        if not self._writable:
            lowercase = bool(self._configs and self._configs[0]._lowercase)
            self._configs.insert(0, Configuration({}, lowercase_keys=lowercase))
            self._writable = True
        return self._configs[0]

    @property
    def _config(self) -> Dict[str, Any]:  # type: ignore
        return self.as_dict()

    @property
    def configs(self) -> List[Configuration]:
        """List of underlying configuration objects."""
        if self._writable:
            return self._configs[1:]
        else:
            return list(self._configs)

    @configs.setter
    def configs(self, iterable: Iterable[Configuration]) -> None:
        if self._writable:
            self._configs = [self._configs[0]] + list(iterable)
        else:
            self._configs = list(iterable)

    def __getitem__(self, item: str) -> Union[Configuration, Any]:  # noqa: D105
        return self._from_configs("__getitem__", item)

    def __getattr__(self, item: str) -> Union[Configuration, Any]:  # noqa: D105
        return self._from_configs("__getattr__", item)

    def get(self, key: str, default: Any = None) -> Union[dict, Any]:
        """
        Get the configuration values corresponding to :attr:`key`.

        :param key: key to retrieve
        :param default: default value in case the key is missing
        :return: the value found or a default
        """
        try:
            return self[key]
        except Exception:
            return default

    def as_dict(self) -> dict:
        """Return the representation as a dictionary."""
        result = {}
        for config_ in self._configs[::-1]:
            result.update(config_.as_dict())
        return result

    def get_dict(self, item: str) -> dict:
        """
        Get the item values as a dictionary.

        :param item: key
        """
        return dict(self[item])

    def keys(
        self, levels: Optional[int] = None
    ) -> Union["Configuration", Any, KeysView[str]]:
        """Return a set-like object providing a view on the configuration keys."""
        return Configuration(self.as_dict()).keys(levels)

    def values(
        self, levels: Optional[int] = None
    ) -> Union["Configuration", Any, ValuesView[Any]]:
        """Return a set-like object providing a view on the configuration values."""
        return Configuration(self.as_dict()).values(levels)

    def items(
        self, levels: Optional[int] = None
    ) -> Union["Configuration", Any, ItemsView[str, Any]]:
        """Return a set-like object providing a view on the configuration items."""
        return Configuration(self.as_dict()).items(levels)

    def __setitem__(self, key: str, value: Any) -> None:  # noqa: D105
        cfg = self._writable_config()
        cfg[key] = value

    def __delitem__(self, prefix: str) -> None:  # noqa: D105
        removed = False
        for cfg in self._configs:
            try:
                del cfg[prefix]
                removed = True
            except KeyError:
                continue
        if not removed:
            raise KeyError()

    def __contains__(self, prefix: str) -> bool:  # noqa: D105
        return any(prefix in cfg for cfg in self._configs)

    def clear(self) -> None:
        """Remove all items."""
        for cfg in self._configs:
            cfg.clear()

    def copy(self) -> "Configuration":
        """Return shallow copy."""
        return ConfigurationSet(*self._configs)

    def update(self, other: Mapping[str, Any]) -> None:
        """Update the ConfigurationSet with another Configuration object or Mapping."""
        cfg = self._writable_config()
        cfg.update(other)

    def reload(self) -> None:
        """Reload the underlying configuration instances."""
        for cfg in self._configs:
            try:
                cfg.reload()
            except NotImplementedError:
                pass

    def __repr__(self) -> str:  # noqa: D105
        return "<ConfigurationSet: %s>" % hex(id(self))

    def __str__(self) -> str:  # noqa: D105
        return str({k: clean(k, v) for k, v in sorted(self.as_dict().items())})
