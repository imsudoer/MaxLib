"""
Async WebSocket transport for MAX Web protocol (JSON over wss://ws-api.oneme.ru/websocket).
"""
import asyncio
import json
import logging
from typing import Any, Callable, Dict, List, Optional
import websockets
from websockets.client import WebSocketClientProtocol

from ..errors.exceptions import NotConnectedError, TransportClosedError
from ..types.packet import Packet
from .constants import DEFAULT_WEB_ORIGIN, DEFAULT_WS_URL

logger = logging.getLogger("maxlib.websocket")


class WebSocketTransport:
    """
    Asynchronous WebSocket transport for the web version of MAX.
    """
    def __init__(
        self,
        url: str = DEFAULT_WS_URL,
        *,
        origin: str = DEFAULT_WEB_ORIGIN,
        user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        request_timeout: float = 30.0,
    ) -> None:
        self.url = url
        self.origin = origin
        self.user_agent = user_agent
        self.request_timeout = request_timeout

        self._ws: Optional[WebSocketClientProtocol] = None
        self._reader_task: Optional[asyncio.Task[None]] = None
        self._seq: int = 0
        self._pending: Dict[int, asyncio.Future[Packet]] = {}
        self._push_handlers: List[Callable[[Packet], Any]] = []
        self._closing: bool = False
        self._on_disconnect: Optional[Callable[[Optional[BaseException]], Any]] = None

    @property
    def is_connected(self) -> bool:
        return self._ws is not None and not self._ws.closed

    def next_seq(self) -> int:
        self._seq += 1
        return self._seq

    def set_disconnect_handler(self, handler: Optional[Callable[[Optional[BaseException]], Any]]) -> None:
        self._on_disconnect = handler

    def add_push_handler(self, handler: Callable[[Packet], Any]) -> None:
        if handler not in self._push_handlers:
            self._push_handlers.append(handler)

    async def connect(self) -> None:
        if self.is_connected:
            return

        self._closing = False
        headers = {
            "User-Agent": self.user_agent,
            "Origin": self.origin,
        }
        self._ws = await websockets.connect(self.url, extra_headers=headers)
        self._reader_task = asyncio.create_task(self._read_loop(), name="maxlib_ws_reader")
        logger.info("Connected to WebSocket %s", self.url)

    async def close(self) -> None:
        self._closing = True
        if self._ws is not None and not self._ws.closed:
            await self._ws.close()

        if self._reader_task is not None and not self._reader_task.done():
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass

        self._ws = None
        self._reader_task = None

    async def send_packet(self, opcode: int, payload: Any = None, *, seq: Optional[int] = None) -> int:
        if not self.is_connected or self._ws is None:
            raise NotConnectedError()

        use_seq = self.next_seq() if seq is None else seq
        msg = {
            "ver": 11,
            "cmd": 0,
            "seq": use_seq,
            "opcode": int(opcode),
            "payload": payload or {},
        }
        await self._ws.send(json.dumps(msg))
        return use_seq

    async def invoke(self, opcode: int, payload: Any = None, *, timeout: Optional[float] = None) -> Packet:
        if not self.is_connected or self._ws is None:
            raise NotConnectedError()

        seq = self.next_seq()
        loop = asyncio.get_running_loop()
        future: asyncio.Future[Packet] = loop.create_future()
        self._pending[seq] = future

        try:
            await self.send_packet(opcode, payload, seq=seq)
            effective_timeout = timeout if timeout is not None else self.request_timeout
            return await asyncio.wait_for(future, timeout=effective_timeout)
        finally:
            self._pending.pop(seq, None)

    async def _read_loop(self) -> None:
        error: Optional[BaseException] = None
        try:
            while not self._closing and self._ws is not None:
                raw_msg = await self._ws.recv()
                if isinstance(raw_msg, bytes):
                    raw_msg = raw_msg.decode("utf-8")
                data = json.loads(raw_msg)

                api = data.get("ver", 11)
                cmd = data.get("cmd", 0)
                seq = data.get("seq", 0)
                opcode = data.get("opcode", 0)
                payload = data.get("payload")

                packet = Packet(api=api, cmd=cmd, seq=seq, opcode=opcode, payload=payload)

                future = self._pending.get(seq)
                if future is not None and not future.done():
                    future.set_result(packet)
                else:
                    for handler in self._push_handlers:
                        res = handler(packet)
                        if asyncio.iscoroutine(res):
                            asyncio.create_task(res)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            if not self._closing:
                error = e
        finally:
            if not self._closing and self._on_disconnect:
                res = self._on_disconnect(error or TransportClosedError())
                if asyncio.iscoroutine(res):
                    asyncio.create_task(res)
