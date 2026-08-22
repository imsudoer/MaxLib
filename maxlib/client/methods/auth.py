"""
Authentication and login mixin for MaxClient.
"""
import logging
from typing import Any, Callable, Dict, Optional, Union, TYPE_CHECKING
from ...errors.exceptions import AuthError, VerifyCodeWrongError, AuthBlockedError
from ...protocol.opcodes import Opcode
from ...types.user import User

if TYPE_CHECKING:
    from ..client import MaxClient

logger = logging.getLogger("maxlib.auth")


class AuthMixin:
    """
    Mixin providing authentication methods for MaxClient.
    """
    async def _send_session_init(self: "MaxClient") -> None:
        """Sends Opcode 6 (SESSION_INIT) with device metadata."""
        user_agent_payload = self.session.device.to_user_agent_dict()
        packet = await self.transport.invoke(Opcode.SESSION_INIT, user_agent_payload)
        logger.debug("Session init response: %s", packet.payload)

    async def start_auth(self: "MaxClient", phone: str) -> Dict[str, Any]:
        """
        Initiates phone-based login and sends SMS/verification code.
        """
        clean_phone = phone.strip().replace(" ", "").replace("-", "")
        if not clean_phone.startswith("+"):
            clean_phone = f"+{clean_phone}"

        payload = {
            "phone": clean_phone,
            "type": "START_AUTH",
            "language": "ru",
        }
        packet = await self.transport.invoke(Opcode.AUTH_START, payload)
        self.session.phone = clean_phone
        return packet.payload or {}

    async def check_code(self: "MaxClient", token: str, code: str) -> Dict[str, Any]:
        """
        Submits verification code to server.
        """
        payload = {
            "token": token,
            "verifyCode": str(code).strip(),
            "authTokenType": "CHECK_CODE",
        }
        packet = await self.transport.invoke(Opcode.AUTH_CHECK_CODE, payload)
        return packet.payload or {}

    async def login(self: "MaxClient", token: Optional[str] = None) -> User:
        """
        Logs into MAX messenger using an authentication token (Opcode 19).
        """
        use_token = token or self.session.token
        if not use_token:
            raise AuthError("No authentication token available for login")

        payload = {
            "interactive": True,
            "token": use_token,
            "chatsSync": 0,
            "contactsSync": 0,
            "presenceSync": 0,
            "draftsSync": 0,
            "chatsCount": 40,
        }
        packet = await self.transport.invoke(Opcode.LOGIN, payload)
        resp_payload = packet.payload or {}

        # Save session token
        self.session.token = use_token
        profile_data = resp_payload.get("profile", {})
        contact_data = profile_data.get("contact", {})
        self.session.account_id = contact_data.get("id")
        self.session.save()

        # Instantiate user profile
        usr = User(client=self, profile=profile_data)
        self.me = usr
        logger.info("Successfully logged in as %s (ID: %s)", usr.name, usr.id)
        return usr

    async def authorize_interactive(
        self: "MaxClient",
        phone: Optional[str] = None,
        code_callback: Optional[Callable[[], Union[str, Any]]] = None,
    ) -> User:
        """
        Interactive authorization flow: sends code, prompts for input, verifies, and logs in.
        """
        if not phone:
            phone = input("Enter phone number (+7...): ").strip()

        print(f"Sending verification code to {phone}...")
        start_resp = await self.start_auth(phone)
        temp_token = start_resp.get("token")
        if not temp_token:
            raise AuthError(f"Failed to start auth: {start_resp}")

        print("Verification code sent! Please enter the code.")
        while True:
            if code_callback:
                code = code_callback()
                if hasattr(code, "__await__"):
                    code = await code
            else:
                code = input("Enter SMS/Push Code: ").strip()

            try:
                check_resp = await self.check_code(temp_token, code)
                token_attrs = check_resp.get("tokenAttrs", {})
                login_entry = token_attrs.get("LOGIN", {})
                login_token = login_entry.get("token") or check_resp.get("token")

                if not login_token:
                    raise AuthError(f"No login token in response: {check_resp}")

                return await self.login(login_token)
            except VerifyCodeWrongError as e:
                print(f"[!] {e.title} ({e.code}). Please try again.")
            except AuthBlockedError as e:
                print(f"[!] Blocked: {e.title}")
                raise

    async def logout(self: "MaxClient") -> bool:
        """
        Terminates the active session and clears stored tokens.
        """
        try:
            await self.transport.invoke(Opcode.LOGOUT, {})
        except Exception:
            pass
        self.session.delete()
        self.me = None
        logger.info("Logged out successfully")
        return True
