"""
Message model with rich bound methods for MAX messenger.
"""
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING
from .base import BaseObject
from .chat import Chat
from .media import Attachment, Audio, Document, Photo, Poll, Sticker, Video, Voice
from .reaction import ReactionInfo, EMOJIS

if TYPE_CHECKING:
    from ..client.client import MaxClient
    from .user import User


class Message(BaseObject):
    """
    Represents a message sent or received in MAX messenger.
    """
    def __init__(
        self,
        client: Optional["MaxClient"] = None,
        chatId: Optional[Union[int, str]] = None,
        sender: Optional[Union[int, str]] = None,
        id: Optional[Union[int, str]] = None,
        time: Optional[int] = None,
        text: str = "",
        type: str = "USER",
        raw: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        data = raw or kwargs
        super().__init__(client=client, raw=data)

        self.chat_id: int = int(chatId or data.get("chatId") or 0)
        self.sender_id: int = int(sender or data.get("sender") or 0)
        self.id: str = str(id or data.get("id") or "")
        self.time: int = int(time or data.get("time") or 0)
        self.text: str = text if text is not None else data.get("text", "")
        self.type: str = type or data.get("type", "USER")
        self.update_time: Optional[int] = data.get("updateTime")
        self.options: Optional[int] = data.get("options")
        self.cid: Optional[int] = data.get("cid")
        self.elements: List[Dict[str, Any]] = data.get("elements", [])

        # Parse reply link
        self.reply_to_message_id: Optional[str] = None
        link = data.get("link")
        if isinstance(link, dict) and link.get("type") == "REPLY":
            self.reply_to_message_id = str(link.get("messageId"))

        # Parse reactions
        raw_reactions = data.get("reactionInfo") or data.get("reactions")
        self.reaction_info: ReactionInfo = ReactionInfo(raw=raw_reactions if isinstance(raw_reactions, dict) else {})

        # Parse attachments
        self.attaches: List[Attachment] = []
        for att in data.get("attaches", []):
            if not isinstance(att, dict):
                continue
            att_type = att.get("_type") or att.get("type", "")
            if att_type == "PHOTO":
                self.attaches.append(Photo(raw=att))
            elif att_type == "VIDEO":
                self.attaches.append(Video(raw=att))
            elif att_type == "AUDIO":
                self.attaches.append(Audio(raw=att))
            elif att_type == "VOICE":
                self.attaches.append(Voice(raw=att))
            elif att_type == "FILE" or att_type == "DOCUMENT":
                self.attaches.append(Document(raw=att))
            elif att_type == "STICKER":
                self.attaches.append(Sticker(raw=att))
            elif att_type == "POLL":
                self.attaches.append(Poll(raw=att))
            else:
                self.attaches.append(Attachment(raw=att))

        # Lazy caches
        self._from_user: Optional["User"] = None
        self._chat: Optional[Chat] = None

    @property
    def is_from_me(self) -> bool:
        """True if the message was sent by the currently logged-in account."""
        if self._client and self._client.me:
            return self.sender_id == self._client.me.id
        return False

    @property
    def sender(self) -> int:
        """Legacy alias for sender_id."""
        return self.sender_id

    @property
    def chat(self) -> Chat:
        if self._chat is None:
            self._chat = Chat(client=self._client, chat_id=self.chat_id)
        return self._chat

    @property
    def photo(self) -> Optional[Photo]:
        for a in self.attaches:
            if isinstance(a, Photo):
                return a
        return None

    @property
    def video(self) -> Optional[Video]:
        for a in self.attaches:
            if isinstance(a, Video):
                return a
        return None

    @property
    def document(self) -> Optional[Document]:
        for a in self.attaches:
            if isinstance(a, Document):
                return a
        return None

    @property
    def voice(self) -> Optional[Voice]:
        for a in self.attaches:
            if isinstance(a, Voice):
                return a
        return None

    @property
    def sticker(self) -> Optional[Sticker]:
        for a in self.attaches:
            if isinstance(a, Sticker):
                return a
        return None

    @property
    def poll(self) -> Optional[Poll]:
        for a in self.attaches:
            if isinstance(a, Poll):
                return a
        return None

    async def get_sender(self) -> "User":
        """Fetches the sender User profile."""
        if not self._client:
            raise ValueError("No client bound to Message")
        if self._from_user is None:
            self._from_user = await self._client.get_user(self.sender_id)
        return self._from_user

    async def reply(self, text: str, **kwargs: Any) -> "Message":
        """Replies to this message with a quote in the same chat."""
        if not self._client:
            raise ValueError("No client bound to Message")
        return await self._client.send_message(self.chat_id, text, reply_to=self.id, **kwargs)

    async def reply_photo(self, photo: Union[bytes, str], caption: str = "", **kwargs: Any) -> "Message":
        """Replies with a photo."""
        if not self._client:
            raise ValueError("No client bound to Message")
        return await self._client.send_photo(self.chat_id, photo, caption=caption, reply_to=self.id, **kwargs)

    async def reply_document(self, document: Union[bytes, str], caption: str = "", **kwargs: Any) -> "Message":
        """Replies with a document."""
        if not self._client:
            raise ValueError("No client bound to Message")
        return await self._client.send_document(self.chat_id, document, caption=caption, reply_to=self.id, **kwargs)

    async def answer(self, text: str, **kwargs: Any) -> "Message":
        """Sends a message to the same chat without replying."""
        if not self._client:
            raise ValueError("No client bound to Message")
        return await self._client.send_message(self.chat_id, text, **kwargs)

    async def edit(self, text: str, **kwargs: Any) -> "Message":
        """Edits the text of this message."""
        if not self._client:
            raise ValueError("No client bound to Message")
        return await self._client.edit_message(self.chat_id, self.id, text, **kwargs)

    async def delete(self, for_me: bool = False) -> bool:
        """Deletes this message."""
        if not self._client:
            raise ValueError("No client bound to Message")
        return await self._client.delete_messages(self.chat_id, [self.id], for_me=for_me)

    async def react(self, reaction: Union[str, EMOJIS]) -> ReactionInfo:
        """Sets emoji reaction on this message."""
        if not self._client:
            raise ValueError("No client bound to Message")
        return await self._client.set_reaction(self.chat_id, self.id, reaction)

    async def remove_reaction(self) -> ReactionInfo:
        """Removes reaction from this message."""
        if not self._client:
            raise ValueError("No client bound to Message")
        return await self._client.remove_reaction(self.chat_id, self.id)

    async def forward(self, to_chat_id: int) -> "Message":
        """Forwards this message to another chat."""
        if not self._client:
            raise ValueError("No client bound to Message")
        return await self._client.send_message(to_chat_id, self.text)
