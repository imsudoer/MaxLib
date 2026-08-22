"""
Chat management methods mixin for MaxClient.
"""
import time
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple, Union, TYPE_CHECKING
from ...protocol.opcodes import Opcode
from ...types.chat import Chat, ChatMember
from ...types.message import Message
from ...utils.pagination import AsyncPagination

if TYPE_CHECKING:
    from ..client import MaxClient


class ChatsMixin:
    """
    Mixin providing operations on chats, dialogues, and channels.
    """
    async def get_chat(self: "MaxClient", chat_id: Union[int, str]) -> Chat:
        """
        Fetches detailed info for a chat.
        """
        payload = {"chatIds": [int(chat_id)]}
        packet = await self.transport.invoke(Opcode.CHAT_INFO, payload)
        chats = (packet.payload or {}).get("chats", [])
        if not chats:
            return Chat(client=self, chat_id=int(chat_id))
        return Chat(client=self, raw=chats[0])

    async def get_chats(self: "MaxClient", count: int = 40, marker: Optional[int] = None) -> List[Chat]:
        """
        Fetches a list of active chats/dialogues.
        """
        payload: Dict[str, Any] = {"count": count}
        if marker is not None:
            payload["marker"] = marker
        packet = await self.transport.invoke(Opcode.CHATS_LIST, payload)
        chats_data = (packet.payload or {}).get("chats", [])
        return [Chat(client=self, raw=c) for c in chats_data]

    def iter_dialogs(self: "MaxClient", limit: Optional[int] = None, chunk_size: int = 40) -> AsyncIterator[Chat]:
        """
        Asynchronously iterates over user's chat dialogs.
        """
        async def fetch_page(offset: Optional[int], size: int) -> Tuple[List[Chat], Optional[int]]:
            payload: Dict[str, Any] = {"count": size}
            if offset is not None:
                payload["marker"] = offset
            packet = await self.transport.invoke(Opcode.CHATS_LIST, payload)
            payload_dict = packet.payload or {}
            chats = [Chat(client=self, raw=c) for c in payload_dict.get("chats", [])]
            next_marker = payload_dict.get("marker")
            return chats, next_marker

        return AsyncPagination(fetch_page, limit=limit, chunk_size=chunk_size)

    async def get_history(
        self: "MaxClient",
        chat_id: Union[int, str],
        count: int = 30,
        from_time: Optional[int] = None,
        forward: int = 0,
        backward: Optional[int] = None,
    ) -> List[Message]:
        """
        Fetches message history for a chat.
        """
        use_from = from_time if from_time is not None else int(time.time() * 1000)
        use_backward = backward if backward is not None else count
        payload = {
            "chatId": int(chat_id),
            "from": use_from,
            "forward": forward,
            "backward": use_backward,
            "getMessages": True,
        }
        packet = await self.transport.invoke(Opcode.CHAT_HISTORY, payload)
        raw_msgs = (packet.payload or {}).get("messages", [])
        return [Message(client=self, chatId=int(chat_id), raw=m) for m in raw_msgs]

    def iter_history(
        self: "MaxClient",
        chat_id: Union[int, str],
        limit: Optional[int] = None,
        chunk_size: int = 40,
    ) -> AsyncIterator[Message]:
        """
        Asynchronously iterates through message history in reverse chronological order.
        """
        cid = int(chat_id)

        async def fetch_page(offset: Optional[int], size: int) -> Tuple[List[Message], Optional[int]]:
            use_from = offset if offset is not None else int(time.time() * 1000)
            payload = {
                "chatId": cid,
                "from": use_from,
                "forward": 0,
                "backward": size,
                "getMessages": True,
            }
            packet = await self.transport.invoke(Opcode.CHAT_HISTORY, payload)
            raw_msgs = (packet.payload or {}).get("messages", [])
            messages = [Message(client=self, chatId=cid, raw=m) for m in raw_msgs]
            next_offset = messages[-1].time if messages else None
            return messages, next_offset

        return AsyncPagination(fetch_page, limit=limit, chunk_size=chunk_size)

    async def create_chat(
        self: "MaxClient",
        title: str,
        user_ids: Optional[List[int]] = None,
        is_channel: bool = False,
    ) -> Chat:
        """
        Creates a new group chat or channel.
        """
        payload = {
            "title": title,
            "userIds": user_ids or [],
            "options": {"A_PLUS_CHANNEL": True} if is_channel else {},
        }
        packet = await self.transport.invoke(Opcode.CHAT_CREATE, payload)
        chat_data = (packet.payload or {}).get("chat", {})
        return Chat(client=self, raw=chat_data)

    async def edit_chat(
        self: "MaxClient",
        chat_id: Union[int, str],
        *,
        title: Optional[str] = None,
        icon_photo_id: Optional[int] = None,
    ) -> bool:
        """
        Updates chat metadata like title or avatar.
        """
        payload: Dict[str, Any] = {"chatId": int(chat_id)}
        if title is not None:
            payload["title"] = title
        if icon_photo_id is not None:
            payload["iconPhotoId"] = icon_photo_id
        await self.transport.invoke(Opcode.CHAT_UPDATE, payload)
        return True

    async def pin_chat(self: "MaxClient", chat_id: Union[int, str]) -> bool:
        """
        Pins a chat in the favorites list.
        """
        payload = {
            "settings": {
                "chats": {
                    str(chat_id): {
                        "favIndex": int(time.time() * 1000)
                    }
                }
            }
        }
        await self.transport.invoke(Opcode.CONFIG, payload)
        return True

    async def unpin_chat(self: "MaxClient", chat_id: Union[int, str]) -> bool:
        """
        Unpins a chat from favorites list.
        """
        payload = {
            "settings": {
                "chats": {
                    str(chat_id): {
                        "favIndex": 0
                    }
                }
            }
        }
        await self.transport.invoke(Opcode.CONFIG, payload)
        return True

    async def leave_chat(self: "MaxClient", chat_id: Union[int, str]) -> bool:
        """
        Leaves a group chat.
        """
        payload = {"chatId": int(chat_id)}
        await self.transport.invoke(Opcode.CHAT_LEAVE, payload)
        return True

    async def clear_chat(self: "MaxClient", chat_id: Union[int, str]) -> bool:
        """
        Clears chat message history.
        """
        payload = {"chatIds": [int(chat_id)]}
        await self.transport.invoke(Opcode.CHAT_CLEAR, payload)
        return True

    async def get_chat_members(self: "MaxClient", chat_id: Union[int, str]) -> List[ChatMember]:
        """
        Retrieves list of members in a group chat.
        """
        payload = {"chatId": int(chat_id)}
        packet = await self.transport.invoke(Opcode.CHAT_MEMBERS, payload)
        members_data = (packet.payload or {}).get("members", [])
        return [ChatMember(client=self, raw=m) for m in members_data]

    async def add_chat_members(self: "MaxClient", chat_id: Union[int, str], user_ids: List[int]) -> bool:
        """
        Adds users to a group chat.
        """
        payload = {
            "chatId": int(chat_id),
            "userIds": user_ids,
        }
        await self.transport.invoke(Opcode.CHAT_MEMBERS_UPDATE, payload)
        return True

    async def remove_chat_member(self: "MaxClient", chat_id: Union[int, str], user_id: int) -> bool:
        """
        Removes / kicks a user from a group chat.
        """
        payload = {
            "chatId": int(chat_id),
            "userId": user_id,
            "action": "REMOVE",
        }
        await self.transport.invoke(Opcode.CHAT_MEMBERS_UPDATE, payload)
        return True
