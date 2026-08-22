"""
JSON File Session storage for MaxLib.
"""
import json
import logging
from pathlib import Path
from typing import Union
from .base import BaseSession

logger = logging.getLogger("maxlib.session")


class JsonSession(BaseSession):
    """
    Session storage that saves device attributes and tokens to a JSON file.
    Supports backward compatibility with legacy plaintext token `.session` files.
    """
    def __init__(self, session_path: Union[str, Path] = "me.session") -> None:
        super().__init__()
        self.path = Path(session_path)

    def load(self) -> bool:
        if not self.path.exists():
            return False

        try:
            content = self.path.read_text(encoding="utf-8").strip()
            if not content:
                return False

            # Check if JSON format
            if content.startswith("{") and content.endswith("}"):
                data = json.loads(content)
                self.from_dict(data)
                logger.debug("Loaded JSON session from %s", self.path)
                return True
            else:
                # Legacy plaintext token format (e.g. from original MaxLib)
                self.token = content
                logger.info("Migrated legacy plaintext session token from %s", self.path)
                self.save()
                return True
        except Exception as e:
            logger.warning("Failed to read session file %s: %s", self.path, e)
            return False

    def save(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            data = self.to_dict()
            self.path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            logger.debug("Saved session to %s", self.path)
        except Exception as e:
            logger.error("Failed to save session to %s: %s", self.path, e)

    def delete(self) -> None:
        if self.path.exists():
            try:
                self.path.unlink()
                logger.info("Deleted session file %s", self.path)
            except Exception as e:
                logger.error("Failed to delete session file %s: %s", self.path, e)
