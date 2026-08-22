"""
Base session interface for MaxLib.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from ..utils.device import DeviceInfo


class BaseSession(ABC):
    """
    Abstract base class for session storage.
    """
    def __init__(self) -> None:
        self.device: DeviceInfo = DeviceInfo.generate_random()
        self.token: Optional[str] = None
        self.account_id: Optional[int] = None
        self.phone: Optional[str] = None

    @abstractmethod
    def load(self) -> bool:
        """Loads session state from storage. Returns True if loaded, False if new."""
        pass

    @abstractmethod
    def save(self) -> None:
        """Persists session state to storage."""
        pass

    @abstractmethod
    def delete(self) -> None:
        """Deletes session from storage."""
        pass

    def to_dict(self) -> Dict[str, Any]:
        return {
            "token": self.token,
            "account_id": self.account_id,
            "phone": self.phone,
            "device_id": self.device.device_id,
            "instance_id": self.device.instance_id,
            "client_session_id": self.device.client_session_id,
            "device_type": self.device.device_type,
            "app_version": self.device.app_version,
            "build_number": self.device.build_number,
            "os_version": self.device.os_version,
            "timezone": self.device.timezone,
            "screen": self.device.screen,
            "push_device_type": self.device.push_device_type,
            "arch": self.device.arch,
            "locale": self.device.locale,
            "device_name": self.device.device_name,
            "device_locale": self.device.device_locale,
        }

    def from_dict(self, data: Dict[str, Any]) -> None:
        self.token = data.get("token")
        self.account_id = data.get("account_id")
        self.phone = data.get("phone")

        if "device_id" in data:
            self.device = DeviceInfo(
                device_id=data.get("device_id", self.device.device_id),
                instance_id=data.get("instance_id", self.device.instance_id),
                client_session_id=data.get("client_session_id", self.device.client_session_id),
                device_type=data.get("device_type", "ANDROID"),
                app_version=data.get("app_version", "26.17.1"),
                build_number=data.get("build_number", 6712),
                os_version=data.get("os_version", "Android 14"),
                timezone=data.get("timezone", "Europe/Moscow"),
                screen=data.get("screen", "1080x2400 440dpi"),
                push_device_type=data.get("push_device_type", "GCM"),
                arch=data.get("arch", "arm64-v8a"),
                locale=data.get("locale", "ru"),
                device_name=data.get("device_name", "Samsung SM-S928B"),
                device_locale=data.get("device_locale", "ru"),
            )
