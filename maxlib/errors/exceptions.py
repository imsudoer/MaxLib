"""
MaxLib exception hierarchy.
"""
from typing import Any, Optional


class MaxError(Exception):
    """Base exception for all MaxLib errors."""
    def __init__(self, message: str, code: Optional[str] = None, raw_payload: Optional[Any] = None) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.raw_payload = raw_payload

    def __str__(self) -> str:
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message


class NotConnectedError(MaxError):
    """Raised when an operation requires an active connection but the client is disconnected."""
    def __init__(self, message: str = "Client is not connected to server.") -> None:
        super().__init__(message, code="NOT_CONNECTED")


class TransportClosedError(MaxError):
    """Raised when the underlying socket transport is closed unexpectedly."""
    def __init__(self, message: str = "Transport connection was closed.") -> None:
        super().__init__(message, code="TRANSPORT_CLOSED")


class PacketError(MaxError):
    """Raised when the server returns an error packet (cmd=3)."""
    def __init__(self, message: str, code: Optional[str] = None, title: Optional[str] = None, raw_payload: Optional[Any] = None) -> None:
        super().__init__(message, code=code, raw_payload=raw_payload)
        self.title = title

    def __str__(self) -> str:
        parts = []
        if self.title:
            parts.append(self.title)
        if self.code:
            parts.append(f"({self.code})")
        if self.message and self.message != self.title:
            parts.append(f": {self.message}")
        return " ".join(parts) if parts else super().__str__()


class AuthError(PacketError):
    """Base exception for authentication failures."""
    pass


class VerifyCodeWrongError(AuthError):
    """Raised when the verification code entered by the user is incorrect."""
    def __init__(self, message: str = "Invalid verification code", code: str = "verify.code.wrong", title: Optional[str] = None, raw_payload: Optional[Any] = None) -> None:
        super().__init__(message, code=code, title=title or "Wrong Code", raw_payload=raw_payload)


class AuthBlockedError(AuthError):
    """Raised when the account or IP is temporarily blocked due to too many attempts."""
    def __init__(self, message: str = "Authentication blocked", code: str = "auth.blocked", title: Optional[str] = None, raw_payload: Optional[Any] = None) -> None:
        super().__init__(message, code=code, title=title or "Auth Blocked", raw_payload=raw_payload)


class SessionExpiredError(AuthError):
    """Raised when the current session token has expired or was revoked."""
    def __init__(self, message: str = "Session has expired or token is invalid", code: str = "session.expired", title: Optional[str] = None, raw_payload: Optional[Any] = None) -> None:
        super().__init__(message, code=code, title=title or "Session Expired", raw_payload=raw_payload)


class UserNotFoundError(PacketError):
    """Raised when a specified user or contact is not found."""
    def __init__(self, message: str = "User not found", code: str = "user.not_found", title: Optional[str] = None, raw_payload: Optional[Any] = None) -> None:
        super().__init__(message, code=code, title=title or "User Not Found", raw_payload=raw_payload)


class ChatNotFoundError(PacketError):
    """Raised when a specified chat is not found or not accessible."""
    def __init__(self, message: str = "Chat not found", code: str = "chat.not_found", title: Optional[str] = None, raw_payload: Optional[Any] = None) -> None:
        super().__init__(message, code=code, title=title or "Chat Not Found", raw_payload=raw_payload)


class MessageNotFoundError(PacketError):
    """Raised when a message cannot be found."""
    def __init__(self, message: str = "Message not found", code: str = "msg.not_found", title: Optional[str] = None, raw_payload: Optional[Any] = None) -> None:
        super().__init__(message, code=code, title=title or "Message Not Found", raw_payload=raw_payload)


class FloodWaitError(PacketError):
    """Raised when the client is rate-limited by the server."""
    def __init__(self, wait_seconds: int = 5, message: str = "Flood wait triggered", code: str = "flood.wait", title: Optional[str] = None, raw_payload: Optional[Any] = None) -> None:
        super().__init__(f"{message} (wait {wait_seconds}s)", code=code, title=title or "Flood Wait", raw_payload=raw_payload)
        self.wait_seconds = wait_seconds


class UploadError(MaxError):
    """Raised when media or file upload fails."""
    def __init__(self, message: str, status_code: Optional[int] = None, response_text: Optional[str] = None) -> None:
        super().__init__(message, code="UPLOAD_ERROR")
        self.status_code = status_code
        self.response_text = response_text


class DownloadError(MaxError):
    """Raised when media or file download fails."""
    def __init__(self, message: str, status_code: Optional[int] = None) -> None:
        super().__init__(message, code="DOWNLOAD_ERROR")
        self.status_code = status_code


class StopPropagation(Exception):
    """Raised inside an event handler to halt propagation to subsequent handlers."""
    pass
