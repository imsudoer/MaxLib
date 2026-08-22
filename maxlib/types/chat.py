"""
Chat and ChatMember models with rich bound actions for MAX messenger.
"""
from enum import Enum
from typing import Any, AsyncIterator, Dict, List, Optional, Union, TYPE_CHECKING
from .base import BaseObject

if TYPE_CHECKING:
    from ..client.client import MaxClient
    from .message import Message
    from .user import User


class ChatType(str, Enum):
    DIALOG = "DIALOG"
    GROUP = "CHAT"
    CHANNEL = "CHANNEL"


class ChatMember(BaseObject):
    def __init__(
        self,
        client: Optional["MaxClient"] = None,
        raw: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        data = raw or kwargs
        super().__init__(client=client, raw=data)
        self.user_id: int = data.get("userId") or data.get("id", 0)
        self.role: str = data.get("role", "MEMBER")  # OWNER, ADMIN, MEMBER
        self.join_time: Optional[int] = data.get("joinTime")
        self.invited_by: Optional[int] = data.get("invitedBy")

    @property
    def is_admin(self) -> bool:
        return self.role in ("ADMIN", "OWNER")

    @property
    def is_owner(self) -> bool:
        return self.role == "OWNER"

    async def get_user(self) -> "User":
        if not self._client:
            raise ValueError("No client bound to ChatMember")
        return await self._client.get_user(self.user_id)


class Chat(BaseObject):
    """
    Represents a dialogue, group chat, or channel in MAX messenger.
    """
    def __init__(
        self,
        client: Optional["MaxClient"] = None,
        raw: Optional[Dict[str, Any]] = None,
        chat_id: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        data = raw or kwargs
        super().__init__(client=client, raw=data)

        self.id: int = chat_id or data.get("id") or data.get("chatId", 0)
        self.type: str = data.get("type", "DIALOG")
        self.title: Optional[str] = data.get("title")
        self.owner_id: Optional[int] = data.get("owner")
        self.participants_count: int = data.get("participantsCount", 0)
        self.status: str = data.get("status", "ACTIVE")
        self.access: str = data.get("access", "PUBLIC")
        self.options: Dict[str, Any] = data.get("options", {})
        self.last_event_time: Optional[int] = data.get("lastEventTime")
        self.new_messages: int = data.get("newMessages", 0)
        self.link: str = f"https://web.max.ru/{self.id}"

    @property
    def is_dialog(self) -> bool:
        return self.type == "DIALOG"

    @property
    def is_group(self) -> bool:
        return self.type == "CHAT"

    @property
    def is_channel(self) -> bool:
        return self.type == "CHANNEL" or self.options.get("A_PLUS_CHANNEL", False)

    async def send_message(self, text: str, **kwargs: Any) -> "Message":
        """Sends a text message to this chat."""
        if not self._client:
            raise ValueError("No client bound to Chat")
        return await self._client.send_message(self.id, text, **kwargs)

    async def send_photo(self, photo: Union[bytes, str], caption: str = "", **kwargs: Any) -> "Message":
        """Sends a photo to this chat."""
        if not self._client:
            raise ValueError("No client bound to Chat")
        return await self._client.send_photo(self.id, photo, caption=caption, **kwargs)

    async def send_document(self, document: Union[bytes, str], caption: str = "", **kwargs: Any) -> "Message":
        """Sends a document to this chat."""
        if not self._client:
            raise ValueError("No client bound to Chat")
        return await self._client.send_document(self.id, document, caption=caption, **kwargs)

    async def get_history(self, limit: int = 30, from_time: Optional[int] = None, forward: int = 0) -> List["Message"]:
        """Fetches recent messages from this chat."""
        if not self._client:
            raise ValueError("No client bound to Chat")
        return await self._client.get_history(self.id, count=limit, from_time=from_time, forward=forward)

    def iter_history(self, limit: Optional[int] = None, chunk_size: int = 40) -> AsyncIterator["Message"]:
        """Asynchronously iterates over messages in this chat."""
        if not self._client:
            raise ValueError("No client bound to Chat")
        return self._client.iter_history(self.id, limit=limit, chunk_size=chunk_size)

    async def pin(self) -> bool:
        """Pins this chat in the user's dialog list."""
        if not self._client:
            raise ValueError("No client bound to Chat")
        return await self._client.pin_chat(self.id)

    async def unpin(self) -> bool:
        """Unpins this chat from the user's dialog list."""
        if not self._client:
            raise ValueError("No client bound to Chat")
        return await self._client.unpin_chat(self.id)

    async def leave(self) -> bool:
        """Leaves this chat."""
        if not self._client:
            raise ValueError("No client bound to Chat")
        return await self._client.leave_chat(self.id)

    async def clear_history(self) -> bool:
        """Clears all messages history in this chat."""
        if not self._client:
            raise ValueError("No client bound to Chat")
        return await self._client.clear_chat(self.id)

    async def set_title(self, title: str) -> bool:
        """Updates the chat title."""
        if not self._client:
            raise ValueError("No client bound to Chat")
        return await self._client.edit_chat(self.id, title=title)

    async def get_members(self) -> List[ChatMember]:
        """Retrieves list of chat members."""
        if not self._client:
            raise ValueError("No client bound to Chat")
        return await self._client.get_chat_members(self.id)

    async def add_members(self, user_ids: List[int]) -> bool:
        """Adds members to chat."""
        if not self._client:
            raise ValueError("No client bound to Chat")
        return await self._client.add_chat_members(self.id, user_ids)

    async def remove_member(self, user_id: int) -> bool:
        """Removes a member from chat."""
        if not self._client:
            raise ValueError("No client bound to Chat")
        return await self._client.remove_chat_member(self.id, user_id)
