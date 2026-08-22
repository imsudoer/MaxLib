"""
Network Packet model for MAX protocol.
"""
from dataclasses import dataclass
from typing import Any, Optional


@dataclass(slots=True)
class Packet:
    """
    Represents a single protocol frame in MAX protocol.
    """
    api: int = 11
    cmd: int = 0
    seq: int = 0
    opcode: int = 0
    payload: Any = None

    @property
    def is_ok(self) -> bool:
        """True if server returned success response (cmd == 1)."""
        return self.cmd == 1

    @property
    def is_error(self) -> bool:
        """True if server returned error response (cmd == 3)."""
        return self.cmd == 3

    @property
    def is_push(self) -> bool:
        """True if packet is a server-initiated push notification / event (cmd == 0)."""
        return self.cmd == 0

    @property
    def is_not_found(self) -> bool:
        """True if resource was not found (cmd == 2)."""
        return self.cmd == 2

    @property
    def error_code(self) -> Optional[str]:
        """Extracts error code string if payload is an error dictionary."""
        if isinstance(self.payload, dict):
            return self.payload.get("error")
        return None

    @property
    def error_message(self) -> Optional[str]:
        """Extracts error message if payload is an error dictionary."""
        if isinstance(self.payload, dict):
            return self.payload.get("localizedMessage") or self.payload.get("message") or self.payload.get("title")
        return None
