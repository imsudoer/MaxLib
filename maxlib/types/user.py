"""
User, Contact, and Name models with bound actions for MAX messenger.
"""
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING
from .base import BaseObject

if TYPE_CHECKING:
    from ..client.client import MaxClient
    from .chat import Chat
    from .message import Message


class Name(BaseObject):
    def __init__(
        self,
        name: str = "",
        firstName: str = "",
        lastName: str = "",
        type: str = "ONEME",
        raw: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(raw=raw)
        self.name = name
        self.first_name = firstName
        self.last_name = lastName
        self.type = type


class Presence(BaseObject):
    def __init__(self, raw: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(raw=raw)
        data = raw or {}
        self.seen: Optional[int] = data.get("seen")
        self.is_online: bool = data.get("online", False)


class Contact(BaseObject):
    def __init__(
        self,
        client: Optional["MaxClient"] = None,
        raw: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        data = raw or kwargs
        super().__init__(client=client, raw=data)

        self.id: int = data.get("id", 0)
        self.phone: Optional[Union[str, int]] = data.get("phone")
        self.description: Optional[str] = data.get("description")
        self.photo_id: Optional[int] = data.get("photoId")
        self.base_url: Optional[str] = data.get("baseUrl")
        self.base_raw_url: Optional[str] = data.get("baseRawUrl")
        self.gender: Optional[str] = data.get("gender")
        self.status: Optional[str] = data.get("status")
        self.update_time: Optional[int] = data.get("updateTime")
        self.options: List[str] = data.get("options", [])
        self.account_status: Optional[int] = data.get("accountStatus")
        self.link: Optional[str] = data.get("link")

        raw_names = data.get("names", [])
        self.names: List[Name] = [Name(**n, raw=n) for n in raw_names] if raw_names else []
        if not self.names and "name" in data:
            self.names = [Name(name=data.get("name", ""), firstName=data.get("firstName", ""), lastName=data.get("lastName", ""))]

    @property
    def display_name(self) -> str:
        if self.names:
            return self.names[0].name or f"{self.names[0].first_name} {self.names[0].last_name}".strip()
        return str(self.id)

    @property
    def first_name(self) -> str:
        if self.names:
            return self.names[0].first_name or self.names[0].name
        return ""

    @property
    def last_name(self) -> str:
        if self.names:
            return self.names[0].last_name
        return ""

    async def add(self) -> Any:
        """Adds this contact to address book."""
        if not self._client:
            raise ValueError("No client bound to Contact object")
        return await self._client.add_contact(self.id)

    async def remove(self) -> Any:
        """Removes this contact from address book."""
        if not self._client:
            raise ValueError("No client bound to Contact object")
        return await self._client.remove_contact(self.id)

    async def block(self) -> Any:
        """Blocks this contact."""
        if not self._client:
            raise ValueError("No client bound to Contact object")
        return await self._client.block_contact(self.id)

    async def unblock(self) -> Any:
        """Unblocks this contact."""
        if not self._client:
            raise ValueError("No client bound to Contact object")
        return await self._client.unblock_contact(self.id)


class User(BaseObject):
    """
    Represents a full user profile with bound actions.
    """
    def __init__(
        self,
        client: Optional["MaxClient"] = None,
        profile: Optional[Dict[str, Any]] = None,
        raw: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        data = profile or raw or kwargs
        super().__init__(client=client, raw=data)

        contact_dict = data.get("contact") if isinstance(data, dict) and "contact" in data else data
        self.contact = Contact(client=client, raw=contact_dict)
        self.id: int = self.contact.id
        self.profile_options: List[str] = data.get("profileOptions", []) if isinstance(data, dict) else []

    @property
    def name(self) -> str:
        return self.contact.display_name

    @property
    def first_name(self) -> str:
        return self.contact.first_name

    @property
    def last_name(self) -> str:
        return self.contact.last_name

    @property
    def phone(self) -> Optional[Union[str, int]]:
        return self.contact.phone

    @property
    def avatar_url(self) -> Optional[str]:
        return self.contact.base_url

    def mention(self, custom_name: Optional[str] = None) -> str:
        """Generates markdown mention link for this user."""
        label = custom_name or self.name
        return f"[{label}](user:{self.id})"

    async def send_message(self, text: str, **kwargs: Any) -> "Message":
        """Sends a direct message to this user."""
        if not self._client:
            raise ValueError("No client bound to User object")
        dm_id = await self.get_dm_chat_id()
        return await self._client.send_message(dm_id, text, **kwargs)

    async def get_dm_chat_id(self) -> int:
        """Computes or retrieves direct message chat ID for this user."""
        if self._client and self._client.me:
            return self._client.me.id ^ self.id
        return self.id

    async def add_contact(self) -> Any:
        return await self.contact.add()

    async def remove_contact(self) -> Any:
        return await self.contact.remove()

    async def block(self) -> Any:
        return await self.contact.block()

    async def unblock(self) -> Any:
        return await self.contact.unblock()
