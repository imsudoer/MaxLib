"""
Main MaxClient orchestrator combining Transport, Dispatcher, Session, and API Mixins.
"""
import asyncio
import logging
import random
import signal
import sys
from pathlib import Path
from typing import Any, Callable, Optional, Union

from ..dispatcher.dispatcher import Dispatcher
from ..dispatcher.filters import Filter
from ..dispatcher.fsm.storage import BaseStorage
from ..errors.exceptions import AuthError, MaxError, NotConnectedError, SessionExpiredError
from ..protocol.constants import (
    DEFAULT_HOST,
    DEFAULT_PING_INTERVAL,
    DEFAULT_PORT,
    DEFAULT_REQUEST_TIMEOUT,
)
from ..protocol.opcodes import Opcode
from ..protocol.transport import Transport
from ..protocol.websocket import WebSocketTransport
from ..session.base import BaseSession
from ..session.json_session import JsonSession
from ..session.memory_session import MemorySession
from ..types.packet import Packet
from ..types.user import User
from .methods import (
    AuthMixin,
    CallsMixin,
    ChatsMixin,
    MediaMixin,
    MessagesMixin,
    SettingsMixin,
    UsersMixin,
)

logger = logging.getLogger("maxlib.client")


class MaxClient(
    AuthMixin,
    MessagesMixin,
    ChatsMixin,
    UsersMixin,
    MediaMixin,
    SettingsMixin,
    CallsMixin,
):
    """
    Next-generation asynchronous client for MAX Messenger.
    """
    def __init__(
        self,
        session: Union[str, Path, BaseSession] = "me",
        *,
        token: Optional[str] = None,
        phone: Optional[str] = None,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        protocol: str = "mobile",  # "mobile" (binary TCP+TLS) or "web" (WebSocket)
        request_timeout: float = DEFAULT_REQUEST_TIMEOUT,
        ping_interval: float = DEFAULT_PING_INTERVAL,
        auto_reconnect: bool = True,
        max_reconnect_delay: float = 60.0,
        fsm_storage: Optional[BaseStorage] = None,
    ) -> None:
        self.host = host
        self.port = port
        self.protocol_type = protocol.lower()
        self.request_timeout = request_timeout
        self.ping_interval = ping_interval
        self.auto_reconnect = auto_reconnect
        self.max_reconnect_delay = max_reconnect_delay

        # Session Setup
        if isinstance(session, BaseSession):
            self.session = session
        elif isinstance(session, (str, Path)):
            session_str = str(session)
            if not session_str.endswith(".session") and not session_str.endswith(".json"):
                session_str = f"{session_str}.session"
            self.session = JsonSession(session_str)
        else:
            self.session = MemorySession()

        # Load session data
        self.session.load()
        if token:
            self.session.token = token
        if phone:
            self.session.phone = phone

        # Dispatcher & FSM
        self.dispatcher = Dispatcher(fsm_storage=fsm_storage)
        self.fsm = self.dispatcher.fsm

        # Transport Engine
        if self.protocol_type == "web":
            self.transport: Union[Transport, WebSocketTransport] = WebSocketTransport(
                request_timeout=request_timeout,
            )
        else:
            self.transport = Transport(
                host=host,
                port=port,
                request_timeout=request_timeout,
            )

        self.transport.set_disconnect_handler(self._on_transport_disconnected)
        self.transport.add_push_handler(self._on_push_packet)

        # Internal State
        self.me: Optional[User] = None
        self._is_running: bool = False
        self._ping_task: Optional[asyncio.Task[None]] = None
        self._reconnect_task: Optional[asyncio.Task[None]] = None
        self._stop_event = asyncio.Event()
        self._reconnect_attempt = 0

    @property
    def is_connected(self) -> bool:
        return self.transport.is_connected

    @property
    def is_authorized(self) -> bool:
        return self.me is not None

    # --- Decorator Forwarders to Dispatcher ---

    def on_message(self, filter: Optional[Filter] = None, *, group: int = 0) -> Callable:
        return self.dispatcher.on_message(filter, group=group)

    def on_edited_message(self, filter: Optional[Filter] = None, *, group: int = 0) -> Callable:
        return self.dispatcher.on_edited_message(filter, group=group)

    def on_deleted_message(self, filter: Optional[Filter] = None, *, group: int = 0) -> Callable:
        return self.dispatcher.on_deleted_message(filter, group=group)

    def on_reaction(self, filter: Optional[Filter] = None, *, group: int = 0) -> Callable:
        return self.dispatcher.on_reaction(filter, group=group)

    def on_typing(self, filter: Optional[Filter] = None, *, group: int = 0) -> Callable:
        return self.dispatcher.on_typing(filter, group=group)

    def on_presence(self, filter: Optional[Filter] = None, *, group: int = 0) -> Callable:
        return self.dispatcher.on_presence(filter, group=group)

    def on_raw_packet(self, opcode: Optional[Union[int, Opcode]] = None, *, group: int = 0) -> Callable:
        return self.dispatcher.on_raw_packet(opcode, group=group)

    def on_connect(self, func: Callable[[], Any]) -> Callable[[], Any]:
        return self.dispatcher.on_connect(func)

    def on_disconnect(self, func: Callable[[Optional[BaseException]], Any]) -> Callable[[Optional[BaseException]], Any]:
        return self.dispatcher.on_disconnect(func)

    # --- Lifecycle & Connection ---

    async def connect(self) -> None:
        """Connects to server and initializes session."""
        if self.is_connected:
            return

        await self.transport.connect()
        if self.protocol_type != "web":
            await self._send_session_init()

        # Start periodic heartbeat ping task
        if self._ping_task is None or self._ping_task.done():
            self._ping_task = asyncio.create_task(self._ping_loop(), name="maxlib_ping_loop")

        logger.info("Connected and initialized session with MAX server")

    async def start(
        self,
        token: Optional[str] = None,
        phone: Optional[str] = None,
        code_callback: Optional[Callable[[], Union[str, Any]]] = None,
    ) -> User:
        """
        Connects, logs in (or performs interactive authorization), and notifies handlers.
        """
        await self.connect()

        use_token = token or self.session.token
        if use_token:
            try:
                user = await self.login(use_token)
            except SessionExpiredError:
                logger.warning("Stored session token expired, falling back to auth flow")
                user = await self.authorize_interactive(phone=phone or self.session.phone, code_callback=code_callback)
        else:
            user = await self.authorize_interactive(phone=phone or self.session.phone, code_callback=code_callback)

        self._is_running = True
        self._stop_event.clear()
        self._reconnect_attempt = 0

        # Trigger on_connect callbacks
        await self.dispatcher.notify_connect()
        return user

    async def stop(self) -> None:
        """Gracefully disconnects and stops background tasks."""
        self._is_running = False
        self._stop_event.set()

        if self._ping_task and not self._ping_task.done():
            self._ping_task.cancel()
            try:
                await self._ping_task
            except asyncio.CancelledError:
                pass

        if self._reconnect_task and not self._reconnect_task.done():
            self._reconnect_task.cancel()

        await self.transport.close()
        logger.info("MaxClient stopped")

    async def disconnect(self) -> None:
        """Alias for stop()."""
        await self.stop()

    async def idle(self) -> None:
        """Blocks until the client is stopped or cancelled."""
        await self._stop_event.wait()

    def run(
        self,
        token: Optional[str] = None,
        phone: Optional[str] = None,
        code_callback: Optional[Callable[[], Union[str, Any]]] = None,
    ) -> None:
        """
        Synchronous convenience entry point for scripts.
        Runs event loop and starts client until SIGINT / Ctrl+C.
        """
        async def _main():
            await self.start(token=token, phone=phone, code_callback=code_callback)
            print(f"[*] MaxLib running as {self.me.name if self.me else 'User'} (ID: {self.me.id if self.me else '?'})")
            print("[*] Press Ctrl+C to stop.")
            try:
                await self.idle()
            finally:
                await self.stop()

        try:
            asyncio.run(_main())
        except (KeyboardInterrupt, SystemExit):
            print("\n[*] Exiting MaxLib...")

    # --- Async Context Manager ---

    async def __aenter__(self) -> "MaxClient":
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.stop()

    # --- Internal Handlers ---

    async def _on_push_packet(self, packet: Packet) -> None:
        """Receives incoming packets from transport and forwards to dispatcher."""
        await self.dispatcher.feed_packet(self, packet)

    async def _ping_loop(self) -> None:
        """Periodic heartbeat loop sending Opcode.PING."""
        try:
            while self.is_connected:
                await asyncio.sleep(self.ping_interval)
                try:
                    await self.transport.send_packet(Opcode.PING, {"interactive": False})
                    logger.debug("Sent heartbeat ping")
                except Exception as e:
                    logger.warning("Failed to send ping: %s", e)
                    break
        except asyncio.CancelledError:
            pass

    def _on_transport_disconnected(self, error: Optional[BaseException]) -> None:
        """Handles unexpected transport disconnects and schedules auto-reconnect."""
        logger.warning("Transport disconnected: %s", error)
        asyncio.create_task(self.dispatcher.notify_disconnect(error))

        if self._is_running and self.auto_reconnect:
            if self._reconnect_task is None or self._reconnect_task.done():
                self._reconnect_task = asyncio.create_task(self._reconnect_loop(), name="maxlib_reconnect_loop")

    async def _reconnect_loop(self) -> None:
        """Exponential backoff reconnect loop."""
        while self._is_running and not self.is_connected:
            self._reconnect_attempt += 1
            delay = min(2 ** (self._reconnect_attempt - 1), self.max_reconnect_delay)
            jitter = random.uniform(0.5, 1.5)
            wait_time = delay * jitter

            logger.info("Attempting reconnect #%d in %.2f seconds...", self._reconnect_attempt, wait_time)
            await asyncio.sleep(wait_time)

            try:
                await self.connect()
                if self.session.token:
                    await self.login(self.session.token)
                self._reconnect_attempt = 0
                logger.info("Successfully reconnected and logged in!")
                await self.dispatcher.notify_connect()
                break
            except Exception as e:
                logger.warning("Reconnect attempt #%d failed: %s", self._reconnect_attempt, e)
