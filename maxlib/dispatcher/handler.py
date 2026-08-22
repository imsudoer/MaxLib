"""
Handler wrapper and registration model for MaxLib.
"""
import inspect
from typing import Any, Callable, Optional, TYPE_CHECKING
from .filters import Filter

if TYPE_CHECKING:
    from ..client.client import MaxClient


class Handler:
    """
    Encapsulates a user-defined event callback function with associated filter and group.
    """
    def __init__(
        self,
        callback: Callable[..., Any],
        filter: Optional[Filter] = None,
        *,
        group: int = 0,
    ) -> None:
        self.callback = callback
        self.filter = filter
        self.group = group
        self._takes_client = self._check_takes_client(callback)

    @staticmethod
    def _check_takes_client(fn: Callable[..., Any]) -> bool:
        try:
            sig = inspect.signature(fn)
            params = [
                p for p in sig.parameters.values()
                if p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
            ]
            return len(params) >= 2
        except Exception:
            return False

    async def check(self, client: "MaxClient", update: Any) -> bool:
        """Evaluates whether the filter passes for this update."""
        if self.filter is None:
            return True
        return await self.filter(client, update)

    async def execute(self, client: "MaxClient", update: Any, *args: Any, **kwargs: Any) -> Any:
        """Calls the callback function with appropriate arguments."""
        if self._takes_client:
            res = self.callback(client, update, *args, **kwargs)
        else:
            res = self.callback(update, *args, **kwargs)

        if hasattr(res, "__await__"):
            return await res
        return res
