"""
Asyncio TCP stream transport for MAX Mobile API with TLS and sequence multiplexing.
"""
import asyncio
import logging
import ssl
from typing import Any, Callable, Dict, List, Optional

from ..errors.exceptions import (
    MaxError,
    NotConnectedError,
    PacketError,
    SessionExpiredError,
    TransportClosedError,
    VerifyCodeWrongError,
    AuthBlockedError,
    UserNotFoundError,
    ChatNotFoundError,
    MessageNotFoundError,
    FloodWaitError,
)
from ..types.packet import Packet
from .binary import (
    pack_packet,
    unpack_packet_header,
    unpack_packet_payload,
)
from .constants import (
    CMD_ERROR,
    CMD_NOT_FOUND,
    CMD_OK,
    DEFAULT_CONNECT_TIMEOUT,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_REQUEST_TIMEOUT,
    HEADER_SIZE,
)
from .opcodes import Opcode

logger = logging.getLogger("maxlib.transport")


class Transport:
    """
    High-performance asynchronous transport for the MAX binary protocol.
    """
    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        *,
        request_timeout: float = DEFAULT_REQUEST_TIMEOUT,
        connect_timeout: float = DEFAULT_CONNECT_TIMEOUT,
        use_tls: bool = True,
        ssl_context: Optional[ssl.SSLContext] = None,
    ) -> None:
        self.host = host
        self.port = port
        self.request_timeout = request_timeout
        self.connect_timeout = connect_timeout
        self.use_tls = use_tls
        self.ssl_context = ssl_context

        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._reader_task: Optional[asyncio.Task[None]] = None
        self._seq: int = 0
        self._pending: Dict[int, asyncio.Future[Packet]] = {}
        self._push_queue: asyncio.Queue[Packet] = asyncio.Queue()
        self._push_handlers: List[Callable[[Packet], Any]] = []
        self._send_lock = asyncio.Lock()
        self._on_disconnect: Optional[Callable[[Optional[BaseException]], Any]] = None
        self._closing: bool = False

    @property
    def is_connected(self) -> bool:
        return (
            self._writer is not None
            and not self._writer.is_closing()
            and self._reader_task is not None
            and not self._reader_task.done()
        )

    def next_seq(self) -> int:
        self._seq = (self._seq + 1) & 0xFFFF
        if self._seq == 0:
            self._seq = 1
        return self._seq

    def set_disconnect_handler(self, handler: Optional[Callable[[Optional[BaseException]], Any]]) -> None:
        self._on_disconnect = handler

    def add_push_handler(self, handler: Callable[[Packet], Any]) -> None:
        if handler not in self._push_handlers:
            self._push_handlers.append(handler)

    def remove_push_handler(self, handler: Callable[[Packet], Any]) -> None:
        if handler in self._push_handlers:
            self._push_handlers.remove(handler)

    async def connect(self) -> None:
        """Establishes TLS connection to server and starts background reader task."""
        if self.is_connected:
            return

        self._closing = False
        context = None
        if self.use_tls:
            context = self.ssl_context or ssl.create_default_context()

        logger.debug("Connecting to %s:%d (TLS=%s)", self.host, self.port, self.use_tls)
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(
                    self.host,
                    self.port,
                    ssl=context,
                    server_hostname=self.host if context else None,
                ),
                timeout=self.connect_timeout,
            )
        except Exception as e:
            logger.error("Failed to connect to %s:%d: %s", self.host, self.port, e)
            raise

        self._reader_task = asyncio.create_task(self._read_loop(), name="maxlib_transport_reader")
        logger.info("Connected to %s:%d", self.host, self.port)

    async def close(self) -> None:
        """Gracefully closes the connection."""
        self._closing = True
        if self._writer is not None and not self._writer.is_closing():
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except Exception:
                pass

        if self._reader_task is not None and not self._reader_task.done():
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass

        self._cleanup_pending(TransportClosedError("Transport was explicitly closed."))
        self._reader = None
        self._writer = None
        self._reader_task = None
        logger.info("Transport closed")

    async def send_raw(self, data: bytes) -> None:
        """Sends raw bytes over the TCP socket."""
        if not self.is_connected or self._writer is None:
            raise NotConnectedError()

        async with self._send_lock:
            self._writer.write(data)
            await self._writer.drain()

    async def send_packet(
        self,
        opcode: int,
        payload: Any = None,
        *,
        seq: Optional[int] = None,
        compress: bool = True,
    ) -> int:
        """Packs and sends a packet without awaiting a response."""
        use_seq = self.next_seq() if seq is None else seq
        raw = pack_packet(opcode, payload, seq=use_seq, compress=compress)
        await self.send_raw(raw)
        return use_seq

    async def invoke(
        self,
        opcode: int,
        payload: Any = None,
        *,
        timeout: Optional[float] = None,
        compress: bool = True,
        check_error: bool = True,
    ) -> Packet:
        """
        Sends a request packet and awaits the corresponding response packet matching its sequence ID.
        """
        if not self.is_connected:
            raise NotConnectedError()

        seq = self.next_seq()
        loop = asyncio.get_running_loop()
        future: asyncio.Future[Packet] = loop.create_future()
        self._pending[seq] = future

        try:
            raw = pack_packet(opcode, payload, seq=seq, compress=compress)
            await self.send_raw(raw)
            effective_timeout = timeout if timeout is not None else self.request_timeout
            response = await asyncio.wait_for(future, timeout=effective_timeout)

            if check_error and response.is_error:
                self._raise_error_packet(response)

            return response
        except asyncio.TimeoutError:
            logger.warning("Request timed out for opcode=%s seq=%d", opcode, seq)
            raise TimeoutError(f"Request timed out for opcode {opcode} (seq {seq})")
        finally:
            self._pending.pop(seq, None)

    async def _read_loop(self) -> None:
        """Main background reader loop reading fixed-size headers and dynamic payloads."""
        error: Optional[BaseException] = None
        try:
            while not self._closing and self._reader is not None:
                # 1. Read 10-byte header
                header_bytes = await self._reader.readexactly(HEADER_SIZE)
                api, cmd, seq, opcode, comp_flag, payload_len = unpack_packet_header(header_bytes)

                # 2. Read payload body
                body_bytes = b""
                if payload_len > 0:
                    body_bytes = await self._reader.readexactly(payload_len)

                # 3. Unpack msgpack payload
                payload = unpack_packet_payload(body_bytes, comp_flag=comp_flag)
                packet = Packet(api=api, cmd=cmd, seq=seq, opcode=opcode, payload=payload)

                logger.debug("Received packet: opcode=%s seq=%d cmd=%d", opcode, seq, cmd)

                # 4. Dispatch packet
                self._dispatch_received_packet(packet)

        except asyncio.IncompleteReadError as e:
            if not self._closing:
                logger.warning("Connection closed by peer (incomplete read)")
                error = TransportClosedError("Incomplete read from socket")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            if not self._closing:
                logger.error("Error in transport reader loop: %s", e)
                error = e
        finally:
            if not self._closing:
                self._cleanup_pending(error or TransportClosedError("Transport disconnected"))
                if self._on_disconnect:
                    try:
                        res = self._on_disconnect(error)
                        if asyncio.iscoroutine(res):
                            asyncio.create_task(res)
                    except Exception as handler_err:
                        logger.error("Error in disconnect handler: %s", handler_err)

    def _dispatch_received_packet(self, packet: Packet) -> None:
        """Dispatches an incoming packet to pending future or push handlers."""
        # Check if a pending invoke() future is waiting for this sequence
        future = self._pending.get(packet.seq)
        if future is not None and not future.done():
            future.set_result(packet)
            return

        # If it's a server push (cmd == 0) or unmapped packet, route to push handlers
        self._push_queue.put_nowait(packet)
        for handler in self._push_handlers:
            try:
                res = handler(packet)
                if asyncio.iscoroutine(res):
                    asyncio.create_task(res)
            except Exception as e:
                logger.error("Error in push handler: %s", e)

    def _cleanup_pending(self, exc: BaseException) -> None:
        """Cancels/fails all pending response futures."""
        for seq, fut in list(self._pending.items()):
            if not fut.done():
                fut.set_exception(exc)
        self._pending.clear()

    @staticmethod
    def _raise_error_packet(packet: Packet) -> None:
        """Converts error packet payload to appropriate typed exception."""
        payload = packet.payload or {}
        if not isinstance(payload, dict):
            raise PacketError(f"Server error: {payload}", raw_payload=payload)

        err = payload.get("error", "unknown_error")
        msg = payload.get("localizedMessage") or payload.get("message") or str(payload)
        title = payload.get("title")

        if err == "verify.code.wrong":
            raise VerifyCodeWrongError(msg, code=err, title=title, raw_payload=payload)
        elif err == "auth.blocked":
            raise AuthBlockedError(msg, code=err, title=title, raw_payload=payload)
        elif err in ("session.expired", "token.invalid", "auth.required"):
            raise SessionExpiredError(msg, code=err, title=title, raw_payload=payload)
        elif err in ("user.not_found", "contact.not_found"):
            raise UserNotFoundError(msg, code=err, title=title, raw_payload=payload)
        elif err in ("chat.not_found", "chat.forbidden"):
            raise ChatNotFoundError(msg, code=err, title=title, raw_payload=payload)
        elif err == "msg.not_found":
            raise MessageNotFoundError(msg, code=err, title=title, raw_payload=payload)
        elif err in ("flood.wait", "rate.limit"):
            wait_sec = payload.get("wait", 5)
            raise FloodWaitError(wait_seconds=wait_sec, message=msg, code=err, title=title, raw_payload=payload)
        else:
            raise PacketError(msg, code=err, title=title, raw_payload=payload)
