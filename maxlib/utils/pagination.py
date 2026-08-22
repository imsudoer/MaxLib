"""
Async pagination and generator utilities for MaxLib.
"""
from typing import AsyncIterator, Callable, Generic, List, Optional, TypeVar

T = TypeVar("T")


class AsyncPagination(Generic[T]):
    """
    Asynchronous iterator for automatic pagination of chats, messages, and members.
    """
    def __init__(
        self,
        fetcher: Callable[[Optional[int], int], AsyncIterator[List[T]]],
        *,
        limit: Optional[int] = None,
        chunk_size: int = 40,
    ) -> None:
        self.fetcher = fetcher
        self.limit = limit
        self.chunk_size = chunk_size
        self._count = 0

    async def __aiter__(self) -> AsyncIterator[T]:
        offset = None
        while self.limit is None or self._count < self.limit:
            batch_size = self.chunk_size
            if self.limit is not None:
                batch_size = min(batch_size, self.limit - self._count)

            items, next_offset = await self.fetcher(offset, batch_size)
            if not items:
                break

            for item in items:
                yield item
                self._count += 1
                if self.limit is not None and self._count >= self.limit:
                    return

            if next_offset is None or next_offset == offset:
                break
            offset = next_offset
