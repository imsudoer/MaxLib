"""
Device profile generator and hardware emulator for MAX Messenger.
"""
import random
import uuid
from dataclasses import dataclass
from typing import Dict, Any


DEVICE_MODELS = [
    ("Xiaomi", "2312DRA50G", "Redmi Note 13 Pro"),
    ("Xiaomi", "22101316G", "Redmi Note 12"),
    ("Samsung", "SM-S928B", "Galaxy S24 Ultra"),
    ("Samsung", "SM-S911B", "Galaxy S23"),
    ("Samsung", "SM-A546B", "Galaxy A54 5G"),
    ("Google", "Pixel 8 Pro", "Pixel 8 Pro"),
    ("Google", "Pixel 7a", "Pixel 7a"),
    ("OnePlus", "CPH2581", "OnePlus 12"),
    ("TECNO", "TECNO CK8n", "CAMON 20 Premier 5G"),
    ("Realme", "RMX3771", "realme 11 Pro+ 5G"),
]

SCREEN_RESOLUTIONS = [
    "1080x2400 440dpi",
    "1080x2340 420dpi",
    "1080x2412 450dpi",
    "1440x3120 515dpi",
    "1440x3088 500dpi",
]

ANDROID_VERSIONS = ["Android 14", "Android 13", "Android 12"]


@dataclass
class DeviceInfo:
    device_id: str
    instance_id: str
    client_session_id: int
    device_type: str = "ANDROID"
    app_version: str = "26.17.1"
    build_number: int = 6712
    os_version: str = "Android 14"
    timezone: str = "Europe/Moscow"
    screen: str = "1080x2400 440dpi"
    push_device_type: str = "GCM"
    arch: str = "arm64-v8a"
    locale: str = "ru"
    device_name: str = "Samsung SM-S928B"
    device_locale: str = "ru"

    @classmethod
    def generate_random(cls) -> "DeviceInfo":
        brand, model, name = random.choice(DEVICE_MODELS)
        return cls(
            device_id=str(uuid.uuid4()),
            instance_id=str(uuid.uuid4()),
            client_session_id=random.randint(100000000, 999999999),
            device_type="ANDROID",
            app_version="26.17.1",
            build_number=random.randint(6700, 6750),
            os_version=random.choice(ANDROID_VERSIONS),
            timezone="Europe/Moscow",
            screen=random.choice(SCREEN_RESOLUTIONS),
            push_device_type="GCM",
            arch="arm64-v8a",
            locale="ru",
            device_name=f"{brand} {model}",
            device_locale="ru",
        )

    def to_user_agent_dict(self) -> Dict[str, Any]:
        """Formats the payload for Opcode.SESSION_INIT (opcode 6)."""
        return {
            "userAgent": {
                "deviceType": self.device_type,
                "appVersion": self.app_version,
                "buildNumber": self.build_number,
                "osVersion": self.os_version,
                "timezone": self.timezone,
                "screen": self.screen,
                "pushDeviceType": self.push_device_type,
                "arch": self.arch,
                "locale": self.locale,
                "deviceName": self.device_name,
                "deviceLocale": self.device_locale,
            },
            "deviceId": self.device_id,
            "instanceId": self.instance_id,
            "clientSessionId": self.client_session_id,
        }
