"""
High-level event models dispatched by MaxLib.
"""
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING
from .base import BaseObject
from .message import Message
from .packet import Packet
from .reaction import ReactionInfo

if TYPE_CHECKING:
    from ..client.client import MaxClient


class Event(BaseObject):
    def __init__(self, client: Optional["MaxClient"] = None, packet: Optional[Packet] = None) -> None:
        super().__init__(client=client, raw=packet.payload if packet else {})
        self.packet = packet


class MessageEvent(Event):
    """Event triggered when a new message arrives (Opcode 128)."""
    def __init__(self, client: Optional["MaxClient"], message: Message, packet: Optional[Packet] = None) -> None:
        super().__init__(client=client, packet=packet)
        self.message = message

    def __getattr__(self, name: str) -> Any:
        return getattr(self.message, name)


class MessageEditedEvent(Event):
    """Event triggered when a message is edited (Opcode 130)."""
    def __init__(self, client: Optional["MaxClient"], message: Message, packet: Optional[Packet] = None) -> None:
        super().__init__(client=client, packet=packet)
        self.message = message

    def __getattr__(self, name: str) -> Any:
        return getattr(self.message, name)


class MessageDeletedEvent(Event):
    """Event triggered when messages are deleted (Opcode 131)."""
    def __init__(self, client: Optional["MaxClient"], chat_id: int, message_ids: List[str], packet: Optional[Packet] = None) -> None:
        super().__init__(client=client, packet=packet)
        self.chat_id = chat_id
        self.message_ids = message_ids


class ReactionEvent(Event):
    """Event triggered when a reaction is added or changed (Opcode 134)."""
    def __init__(self, client: Optional["MaxClient"], chat_id: int, message_id: str, reaction_info: ReactionInfo, packet: Optional[Packet] = None) -> None:
        super().__init__(client=client, packet=packet)
        self.chat_id = chat_id
        self.message_id = message_id
        self.reaction_info = reaction_info


class TypingEvent(Event):
    """Event triggered when a user is typing in a chat (Opcode 129)."""
    def __init__(self, client: Optional["MaxClient"], chat_id: int, user_id: int, packet: Optional[Packet] = None) -> None:
        super().__init__(client=client, packet=packet)
        self.chat_id = chat_id
        self.user_id = user_id


class PresenceEvent(Event):
    """Event triggered when user presence status updates (Opcode 133)."""
    def __init__(self, client: Optional["MaxClient"], user_id: int, seen: int, is_online: bool, packet: Optional[Packet] = None) -> None:
        super().__init__(client=client, packet=packet)
        self.user_id = user_id
        self.seen = seen
        self.is_online = is_online
