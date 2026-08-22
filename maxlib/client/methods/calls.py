"""
Voice & Video call signaling mixin for MaxClient.
"""
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from ...protocol.opcodes import Opcode

if TYPE_CHECKING:
    from ..client import MaxClient


class CallsMixin:
    """
    Mixin providing operations on calls and video chats.
    """
    async def get_call_history(self: "MaxClient", limit: int = 30) -> List[Dict[str, Any]]:
        """
        Fetches voice/video calls history.
        """
        packet = await self.transport.invoke(Opcode.VIDEO_CHAT_HISTORY, {"count": limit})
        return (packet.payload or {}).get("history", [])
