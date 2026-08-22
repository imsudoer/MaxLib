"""
Settings, profile configuration, and privacy mixin for MaxClient.
"""
from typing import Any, Dict, Optional, TYPE_CHECKING
from ...protocol.opcodes import Opcode

if TYPE_CHECKING:
    from ..client import MaxClient


class SettingsMixin:
    """
    Mixin providing operations for account settings and privacy.
    """
    async def update_profile(
        self: "MaxClient",
        *,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> bool:
        """
        Updates profile name and bio description.
        """
        payload: Dict[str, Any] = {}
        if first_name is not None:
            payload["firstName"] = first_name
        if last_name is not None:
            payload["lastName"] = last_name
        if description is not None:
            payload["description"] = description
        await self.transport.invoke(Opcode.PROFILE, payload)
        return True

    async def get_preset_avatars(self: "MaxClient") -> Dict[str, Any]:
        """
        Retrieves MAX catalog of preset animated/styled avatars.
        """
        packet = await self.transport.invoke(Opcode.PRESET_AVATARS, {})
        return packet.payload or {}
