"""
Middleware pipeline for MaxLib.
"""
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from ..client.client import MaxClient


class BaseMiddleware(ABC):
    """
    Base class for custom middlewares.
    """
    @abstractmethod
    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Any],
        event: Any,
        data: Dict[str, Any],
    ) -> Any:
        """
        Executes middleware logic around event handling.
        """
        return await handler(event, data)


class MiddlewareManager:
    def __init__(self) -> None:
        self._middlewares: List[BaseMiddleware] = []

    def register(self, middleware: BaseMiddleware) -> None:
        self._middlewares.append(middleware)

    async def wrap_and_execute(
        self,
        final_handler: Callable[[Any, Dict[str, Any]], Any],
        event: Any,
        data: Dict[str, Any],
    ) -> Any:
        handler = final_handler
        for mw in reversed(self._middlewares):
            def make_layer(m: BaseMiddleware, next_h: Callable[[Any, Dict[str, Any]], Any]):
                async def layer(evt: Any, d: Dict[str, Any]) -> Any:
                    return await m(next_h, evt, d)
                return layer
            handler = make_layer(mw, handler)

        return await handler(event, data)
