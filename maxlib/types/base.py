"""
Base class for all MaxLib models.
"""
from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..client.client import MaxClient


class BaseObject:
    """
    Base class for all models in MaxLib with client binding and JSON serialization.
    """
    __slots__ = ("_client", "_raw")

    def __init__(self, client: Optional["MaxClient"] = None, raw: Optional[Dict[str, Any]] = None) -> None:
        self._client = client
        self._raw = raw or {}

    @property
    def client(self) -> Optional["MaxClient"]:
        return self._client

    @property
    def raw(self) -> Dict[str, Any]:
        return self._raw

    def bind_client(self, client: "MaxClient") -> None:
        self._client = client

    def to_dict(self) -> Dict[str, Any]:
        return self._raw.copy()

    def __repr__(self) -> str:
        attrs = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items() if not k.startswith("_"))
        return f"{self.__class__.__name__}({attrs})"
