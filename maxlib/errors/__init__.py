"""
Errors module for MaxLib.
"""
from .exceptions import (
    MaxError,
    NotConnectedError,
    TransportClosedError,
    PacketError,
    AuthError,
    VerifyCodeWrongError,
    AuthBlockedError,
    SessionExpiredError,
    UserNotFoundError,
    ChatNotFoundError,
    MessageNotFoundError,
    FloodWaitError,
    UploadError,
    DownloadError,
    StopPropagation,
)

# Backward-compatibility aliases with previous maxlib version
VerifyCodeWrong = VerifyCodeWrongError
AuthBlocked = AuthBlockedError
UserNotFound = UserNotFoundError
NotConnected = NotConnectedError
TransportClosed = TransportClosedError
SessionExpired = SessionExpiredError

__all__ = [
    "MaxError",
    "NotConnectedError",
    "TransportClosedError",
    "PacketError",
    "AuthError",
    "VerifyCodeWrongError",
    "AuthBlockedError",
    "SessionExpiredError",
    "UserNotFoundError",
    "ChatNotFoundError",
    "MessageNotFoundError",
    "FloodWaitError",
    "UploadError",
    "DownloadError",
    "StopPropagation",
    # Legacy aliases
    "VerifyCodeWrong",
    "AuthBlocked",
    "UserNotFound",
    "NotConnected",
    "TransportClosed",
    "SessionExpired",
]
