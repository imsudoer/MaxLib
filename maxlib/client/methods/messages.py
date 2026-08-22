"""
Messaging methods mixin for MaxClient.
"""
import time
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING
from ...protocol.opcodes import Opcode
from ...types.message import Message
from ...types.reaction import EMOJIS, ReactionInfo
from ...utils.formatting import format_text

if TYPE_CHECKING:
    from ..client import MaxClient


class MessagesMixin:
    """
    Mixin providing rich messaging operations.
    """
    async def send_message(
        self: "MaxClient",
        chat_id: Union[int, str],
        text: str = "",
        *,
        reply_to: Optional[Union[int, str]] = None,
        notify: bool = True,
        parse_mode: str = "markdown",
        elements: Optional[List[Dict[str, Any]]] = None,
        attaches: Optional[List[Dict[str, Any]]] = None,
    ) -> Message:
        """
        Sends a text message to a chat with optional formatting and reply.
        """
        clean_text, parsed_elements = format_text(text, elements=elements, parse_mode=parse_mode)
        cid = -int(time.time() * 1000)

        message_obj: Dict[str, Any] = {
            "text": clean_text,
            "cid": cid,
            "elements": parsed_elements,
            "attaches": attaches or [],
        }

        if reply_to is not None:
            message_obj["link"] = {
                "type": "REPLY",
                "messageId": int(reply_to) if str(reply_to).isdigit() else str(reply_to),
            }

        payload = {
            "chatId": int(chat_id),
            "message": message_obj,
            "notify": notify,
        }

        packet = await self.transport.invoke(Opcode.MSG_SEND, payload)
        resp_payload = packet.payload or {}
        returned_msg = resp_payload.get("message", message_obj)
        return Message(client=self, chatId=int(chat_id), raw=returned_msg)

    async def send_markdown(self: "MaxClient", chat_id: Union[int, str], text: str, **kwargs: Any) -> Message:
        """Helper to send Markdown V2 formatted message."""
        return await self.send_message(chat_id, text, parse_mode="markdown", **kwargs)

    async def send_html(self: "MaxClient", chat_id: Union[int, str], text: str, **kwargs: Any) -> Message:
        """Helper to send HTML formatted message."""
        return await self.send_message(chat_id, text, parse_mode="html", **kwargs)

    async def edit_message(
        self: "MaxClient",
        chat_id: Union[int, str],
        message_id: Union[int, str],
        text: str,
        *,
        parse_mode: str = "markdown",
        elements: Optional[List[Dict[str, Any]]] = None,
        attaches: Optional[List[Dict[str, Any]]] = None,
    ) -> Message:
        """
        Edits text and formatting of an existing message.
        """
        clean_text, parsed_elements = format_text(text, elements=elements, parse_mode=parse_mode)
        payload = {
            "chatId": int(chat_id),
            "messageId": str(message_id),
            "text": clean_text,
            "elements": parsed_elements,
            "attachments": attaches or [],
        }
        packet = await self.transport.invoke(Opcode.MSG_EDIT, payload)
        resp_payload = packet.payload or {}
        return Message(client=self, chatId=int(chat_id), raw=resp_payload.get("message", payload))

    async def delete_messages(
        self: "MaxClient",
        chat_id: Union[int, str],
        message_ids: List[Union[int, str]],
        *,
        for_me: bool = False,
    ) -> bool:
        """
        Deletes one or more messages by ID.
        """
        payload = {
            "chatId": int(chat_id),
            "messageIds": [str(mid) for mid in message_ids],
            "forMe": for_me,
        }
        await self.transport.invoke(Opcode.MSG_DELETE, payload)
        return True

    async def delete_message(
        self: "MaxClient",
        chat_id: Union[int, str],
        message_id: Union[int, str],
        *,
        for_me: bool = False,
    ) -> bool:
        """Helper to delete a single message."""
        return await self.delete_messages(chat_id, [message_id], for_me=for_me)

    async def set_reaction(
        self: "MaxClient",
        chat_id: Union[int, str],
        message_id: Union[int, str],
        reaction: Union[str, EMOJIS],
    ) -> ReactionInfo:
        """
        Sets an emoji reaction on a message.
        """
        payload = {
            "chatId": int(chat_id),
            "messageId": str(message_id),
            "reaction": {
                "reactionType": "EMOJI",
                "id": str(reaction),
            },
        }
        packet = await self.transport.invoke(Opcode.SET_REACTION, payload)
        return ReactionInfo(raw=packet.payload or {})

    async def remove_reaction(
        self: "MaxClient",
        chat_id: Union[int, str],
        message_id: Union[int, str],
    ) -> ReactionInfo:
        """
        Removes current user's reaction from a message.
        """
        payload = {
            "chatId": int(chat_id),
            "messageId": str(message_id),
        }
        packet = await self.transport.invoke(Opcode.REMOVE_REACTION, payload)
        return ReactionInfo(raw=packet.payload or {})

    async def send_typing(self: "MaxClient", chat_id: Union[int, str]) -> bool:
        """
        Sends typing indicator to a chat.
        """
        payload = {"chatId": int(chat_id)}
        await self.transport.send_packet(Opcode.MSG_TYPING, payload)
        return True
