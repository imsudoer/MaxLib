"""
In-memory ephemeral session storage for MaxLib.
"""
from typing import Optional
from .base import BaseSession


class MemorySession(BaseSession):
    """
    Ephemeral session storage that exists only in RAM for the duration of the process.
    """
    def __init__(self, token: Optional[str] = None, phone: Optional[str] = None) -> None:
        super().__init__()
        self.token = token
        self.phone = phone

    def load(self) -> bool:
        return self.token is not None

    def save(self) -> None:
        pass

    def delete(self) -> None:
        self.token = None
        self.account_id = None
        self.phone = None
