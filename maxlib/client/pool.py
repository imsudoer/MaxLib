"""
Multi-account client pool and account manager for MaxLib.
"""
import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional, Union
from .client import MaxClient

logger = logging.getLogger("maxlib.pool")


class ClientPool:
    """
    Manager for orchestrating multiple MaxClient instances concurrently.
    """
    def __init__(self) -> None:
        self.clients: Dict[str, MaxClient] = {}
        self._is_running = False

    def add(self, name: str, client: MaxClient) -> MaxClient:
        """Adds a client to the pool."""
        self.clients[name] = client
        return client

    def create(self, name: str, **kwargs: Any) -> MaxClient:
        """Creates and adds a new MaxClient instance."""
        client = MaxClient(session=name, **kwargs)
        self.clients[name] = client
        return client

    def get(self, name: str) -> Optional[MaxClient]:
        """Gets a client by name."""
        return self.clients.get(name)

    def on_message(self, *args: Any, **kwargs: Any) -> Callable:
        """Registers a message handler across ALL clients in the pool."""
        def decorator(func: Callable) -> Callable:
            for client in self.clients.values():
                client.on_message(*args, **kwargs)(func)
            return func
        return decorator

    async def start_all(self) -> None:
        """Starts all clients in the pool concurrently."""
        self._is_running = True
        tasks = [asyncio.create_task(c.start(), name=f"start_{name}") for name, c in self.clients.items()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for (name, c), res in zip(self.clients.items(), results):
            if isinstance(res, Exception):
                logger.error("Client %s failed to start: %s", name, res)

    async def stop_all(self) -> None:
        """Stops all clients in the pool."""
        self._is_running = False
        tasks = [asyncio.create_task(c.stop(), name=f"stop_{name}") for name, c in self.clients.items()]
        await asyncio.gather(*tasks, return_exceptions=True)

    def run(self) -> None:
        """Synchronous runner for all accounts in pool."""
        async def _main():
            await self.start_all()
            print(f"[*] Started {len(self.clients)} clients in pool.")
            await asyncio.Event().wait()

        try:
            asyncio.run(_main())
        except (KeyboardInterrupt, SystemExit):
            print("\n[*] Stopping all clients...")
