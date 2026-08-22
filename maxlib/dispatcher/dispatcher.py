"""
Event Dispatcher for routing incoming packets and updates to registered handlers.
"""
import asyncio
import logging
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, Union, TYPE_CHECKING

from ..errors.exceptions import StopPropagation
from ..protocol.opcodes import Opcode
from ..types.events import (
    Event,
    MessageDeletedEvent,
    MessageEditedEvent,
    MessageEvent,
    PresenceEvent,
    ReactionEvent,
    TypingEvent,
)
from ..types.message import Message
from ..types.packet import Packet
from ..types.reaction import ReactionInfo
from .filters import Filter
from .fsm.storage import BaseStorage, MemoryStorage
from .handler import Handler
from .middlewares import MiddlewareManager

if TYPE_CHECKING:
    from ..client.client import MaxClient

logger = logging.getLogger("maxlib.dispatcher")


class Dispatcher:
    """
    Central router for all updates, messages, events, and FSM states.
    """
    def __init__(self, fsm_storage: Optional[BaseStorage] = None) -> None:
        self.fsm: BaseStorage = fsm_storage or MemoryStorage()
        self.middlewares: MiddlewareManager = MiddlewareManager()

        # Handlers grouped by group ID (sorted ascending: group 0 runs before group 1)
        self._message_handlers: Dict[int, List[Handler]] = defaultdict(list)
        self._edited_message_handlers: Dict[int, List[Handler]] = defaultdict(list)
        self._deleted_message_handlers: Dict[int, List[Handler]] = defaultdict(list)
        self._reaction_handlers: Dict[int, List[Handler]] = defaultdict(list)
        self._typing_handlers: Dict[int, List[Handler]] = defaultdict(list)
        self._presence_handlers: Dict[int, List[Handler]] = defaultdict(list)
        self._raw_handlers: Dict[int, List[Handler]] = defaultdict(list)
        self._connect_handlers: List[Callable[[], Any]] = []
        self._disconnect_handlers: List[Callable[[Optional[BaseException]], Any]] = []

    def on_message(self, filter: Optional[Filter] = None, *, group: int = 0) -> Callable:
        """Decorator to register a new incoming message handler."""
        def decorator(func: Callable) -> Callable:
            self._message_handlers[group].append(Handler(func, filter, group=group))
            return func
        return decorator

    def on_edited_message(self, filter: Optional[Filter] = None, *, group: int = 0) -> Callable:
        """Decorator to register a message edit handler."""
        def decorator(func: Callable) -> Callable:
            self._edited_message_handlers[group].append(Handler(func, filter, group=group))
            return func
        return decorator

    def on_deleted_message(self, filter: Optional[Filter] = None, *, group: int = 0) -> Callable:
        """Decorator to register a message deletion handler."""
        def decorator(func: Callable) -> Callable:
            self._deleted_message_handlers[group].append(Handler(func, filter, group=group))
            return func
        return decorator

    def on_reaction(self, filter: Optional[Filter] = None, *, group: int = 0) -> Callable:
        """Decorator to register a reaction event handler."""
        def decorator(func: Callable) -> Callable:
            self._reaction_handlers[group].append(Handler(func, filter, group=group))
            return func
        return decorator

    def on_typing(self, filter: Optional[Filter] = None, *, group: int = 0) -> Callable:
        """Decorator to register a typing event handler."""
        def decorator(func: Callable) -> Callable:
            self._typing_handlers[group].append(Handler(func, filter, group=group))
            return func
        return decorator

    def on_presence(self, filter: Optional[Filter] = None, *, group: int = 0) -> Callable:
        """Decorator to register a presence update handler."""
        def decorator(func: Callable) -> Callable:
            self._presence_handlers[group].append(Handler(func, filter, group=group))
            return func
        return decorator

    def on_raw_packet(self, opcode: Optional[Union[int, Opcode]] = None, *, group: int = 0) -> Callable:
        """Decorator to register a handler for raw low-level packets."""
        def decorator(func: Callable) -> Callable:
            def raw_filter(client, packet: Packet) -> bool:
                return opcode is None or packet.opcode == int(opcode)
            self._raw_handlers[group].append(Handler(func, Filter(raw_filter, f"opcode={opcode}"), group=group))
            return func
        return decorator

    def on_connect(self, func: Callable[[], Any]) -> Callable[[], Any]:
        """Decorator for connection established callback."""
        self._connect_handlers.append(func)
        return func

    def on_disconnect(self, func: Callable[[Optional[BaseException]], Any]) -> Callable[[Optional[BaseException]], Any]:
        """Decorator for disconnection callback."""
        self._disconnect_handlers.append(func)
        return func

    async def notify_connect(self) -> None:
        for handler in self._connect_handlers:
            try:
                res = handler()
                if hasattr(res, "__await__"):
                    await res
            except Exception as e:
                logger.error("Error in connect handler: %s", e)

    async def notify_disconnect(self, error: Optional[BaseException]) -> None:
        for handler in self._disconnect_handlers:
            try:
                res = handler(error)
                if hasattr(res, "__await__"):
                    await res
            except Exception as e:
                logger.error("Error in disconnect handler: %s", e)

    async def feed_packet(self, client: "MaxClient", packet: Packet) -> None:
        """Feeds an incoming packet into dispatcher for parsing and routing."""
        # 1. Dispatch raw packet handlers
        await self._dispatch_handlers(self._raw_handlers, client, packet)

        # 2. Dispatch high-level opcode events
        payload = packet.payload
        if not isinstance(payload, dict):
            return

        opcode = packet.opcode

        # Opcode 128: PUSH_NEW_MESSAGE
        if opcode == Opcode.PUSH_NEW_MESSAGE or opcode == 128:
            chat_id = payload.get("chatId", 0)
            msg_dict = payload.get("message")
            if isinstance(msg_dict, dict):
                msg = Message(client=client, chatId=chat_id, raw=msg_dict)
                await self._dispatch_handlers(self._message_handlers, client, msg)

        # Opcode 130: PUSH_MESSAGE_EDIT
        elif opcode == Opcode.PUSH_MESSAGE_EDIT or opcode == 130:
            chat_id = payload.get("chatId", 0)
            msg_dict = payload.get("message")
            if isinstance(msg_dict, dict):
                msg = Message(client=client, chatId=chat_id, raw=msg_dict)
                await self._dispatch_handlers(self._edited_message_handlers, client, msg)

        # Opcode 131: PUSH_MESSAGE_DELETE
        elif opcode == Opcode.PUSH_MESSAGE_DELETE or opcode == 131:
            chat_id = payload.get("chatId", 0)
            message_ids = [str(mid) for mid in payload.get("messageIds", [])]
            evt = MessageDeletedEvent(client=client, chat_id=chat_id, message_ids=message_ids, packet=packet)
            await self._dispatch_handlers(self._deleted_message_handlers, client, evt)

        # Opcode 134: PUSH_REACTION
        elif opcode == Opcode.PUSH_REACTION or opcode == 134:
            chat_id = payload.get("chatId", 0)
            message_id = str(payload.get("messageId", ""))
            reactions = ReactionInfo(raw=payload.get("reactionInfo"))
            evt = ReactionEvent(client=client, chat_id=chat_id, message_id=message_id, reaction_info=reactions, packet=packet)
            await self._dispatch_handlers(self._reaction_handlers, client, evt)

        # Opcode 129: PUSH_TYPING
        elif opcode == Opcode.PUSH_TYPING or opcode == 129:
            chat_id = payload.get("chatId", 0)
            user_id = payload.get("userId", 0)
            evt = TypingEvent(client=client, chat_id=chat_id, user_id=user_id, packet=packet)
            await self._dispatch_handlers(self._typing_handlers, client, evt)

        # Opcode 133: PUSH_PRESENCE
        elif opcode == Opcode.PUSH_PRESENCE or opcode == 133:
            user_id = payload.get("userId", 0)
            seen = payload.get("seen", 0)
            is_online = payload.get("online", False)
            evt = PresenceEvent(client=client, user_id=user_id, seen=seen, is_online=is_online, packet=packet)
            await self._dispatch_handlers(self._presence_handlers, client, evt)

    async def _dispatch_handlers(
        self,
        handlers_by_group: Dict[int, List[Handler]],
        client: "MaxClient",
        event: Any,
    ) -> None:
        """Executes matching handlers sorted by group index with StopPropagation support."""
        for group in sorted(handlers_by_group.keys()):
            for handler in handlers_by_group[group]:
                try:
                    if await handler.check(client, event):
                        async def execute_handler(evt, data):
                            return await handler.execute(client, evt)

                        await self.middlewares.wrap_and_execute(execute_handler, event, {})
                        break  # In the same group, only the first matching handler runs (Pyrogram style)
                except StopPropagation:
                    return  # Stop handling across all subsequent groups
                except Exception as e:
                    logger.error("Exception in event handler %s: %s", handler.callback, e, exc_info=True)
