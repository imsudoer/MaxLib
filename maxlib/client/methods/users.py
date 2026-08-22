"""
User and Contact operations mixin for MaxClient.
"""
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING
from ...errors.exceptions import UserNotFoundError
from ...protocol.opcodes import Opcode
from ...types.user import Contact, Presence, User

if TYPE_CHECKING:
    from ..client import MaxClient


class UsersMixin:
    """
    Mixin providing operations on users, contacts, and presence.
    """
    async def get_user(
        self: "MaxClient",
        id: Optional[Union[int, str]] = None,
        phone: Optional[Union[int, str]] = None,
        chat_id: Optional[Union[int, str]] = None,
    ) -> User:
        """
        Retrieves a user profile by ID, phone number, or 1-on-1 chat ID.
        """
        if id is not None:
            payload = {"contactIds": [int(id)]}
            packet = await self.transport.invoke(Opcode.CONTACT_INFO, payload)
            contacts = (packet.payload or {}).get("contacts", [])
            if not contacts:
                raise UserNotFoundError(f"User with ID {id} not found")
            return User(client=self, raw={"contact": contacts[0]})

        elif phone is not None:
            clean_phone = str(phone).strip().replace(" ", "").replace("-", "")
            if not clean_phone.startswith("+"):
                clean_phone = f"+{clean_phone}"
            payload = {"phone": clean_phone}
            packet = await self.transport.invoke(Opcode.CONTACT_INFO_BY_PHONE, payload)
            contact_data = (packet.payload or {}).get("contact")
            if not contact_data:
                raise UserNotFoundError(f"User with phone {clean_phone} not found")
            return User(client=self, raw={"contact": contact_data})

        elif chat_id is not None:
            if not self.me:
                raise ValueError("Cannot resolve user by chat_id without active self.me profile")
            resolved_user_id = self.me.id ^ int(chat_id)
            return await self.get_user(id=resolved_user_id)

        raise ValueError("Must provide either 'id', 'phone', or 'chat_id'")

    async def search_users(self: "MaxClient", query: str, count: int = 20) -> List[User]:
        """
        Searches public users and channels by query.
        """
        payload = {"query": query, "count": count}
        packet = await self.transport.invoke(Opcode.PUBLIC_SEARCH, payload)
        contacts = (packet.payload or {}).get("contacts", [])
        return [User(client=self, raw={"contact": c}) for c in contacts]

    async def get_contacts(self: "MaxClient") -> List[Contact]:
        """
        Retrieves the user's address book / contacts list.
        """
        packet = await self.transport.invoke(Opcode.CONTACT_LIST, {})
        contacts = (packet.payload or {}).get("contacts", [])
        return [Contact(client=self, raw=c) for c in contacts]

    async def add_contact(
        self: "MaxClient",
        user_id: int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> bool:
        """
        Adds a user to contacts.
        """
        payload: Dict[str, Any] = {
            "contactId": int(user_id),
            "action": "ADD",
        }
        if first_name is not None:
            payload["firstName"] = first_name
        if last_name is not None:
            payload["lastName"] = last_name
        await self.transport.invoke(Opcode.CONTACT_UPDATE, payload)
        return True

    async def remove_contact(self: "MaxClient", user_id: int) -> bool:
        """
        Removes a user from contacts.
        """
        payload = {
            "contactId": int(user_id),
            "action": "REMOVE",
        }
        await self.transport.invoke(Opcode.CONTACT_UPDATE, payload)
        return True

    async def block_contact(self: "MaxClient", user_id: int) -> bool:
        """
        Blocks a user.
        """
        payload = {
            "contactId": int(user_id),
            "action": "BLOCK",
        }
        await self.transport.invoke(Opcode.CONTACT_UPDATE, payload)
        return True

    async def unblock_contact(self: "MaxClient", user_id: int) -> bool:
        """
        Unblocks a user.
        """
        payload = {
            "contactId": int(user_id),
            "action": "UNBLOCK",
        }
        await self.transport.invoke(Opcode.CONTACT_UPDATE, payload)
        return True

    async def get_presence(self: "MaxClient", user_ids: List[int]) -> Dict[int, Presence]:
        """
        Fetches last seen / online presence statuses for users.
        """
        payload = {"contactIds": user_ids}
        packet = await self.transport.invoke(Opcode.CONTACT_PRESENCE, payload)
        presence_map = (packet.payload or {}).get("presence", {})
        return {
            int(uid): Presence(raw=p_info)
            for uid, p_info in presence_map.items()
        }
