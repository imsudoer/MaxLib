"""
Media attachment models for MAX Messenger.
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union
from .base import BaseObject


class Attachment(BaseObject):
    """
    Base class for message attachments.
    """
    def __init__(self, raw: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(raw=raw)
        data = raw or {}
        self.type: str = data.get("_type") or data.get("type", "UNKNOWN")
        self.id: Optional[Union[str, int]] = data.get("id") or data.get("fileId") or data.get("photoId")
        self.url: Optional[str] = data.get("url") or data.get("baseUrl")


class Photo(Attachment):
    def __init__(self, raw: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(raw=raw)
        data = raw or {}
        self.photo_id: Optional[int] = data.get("photoId") or data.get("id")
        self.url: Optional[str] = data.get("baseUrl") or data.get("url")
        self.width: Optional[int] = data.get("width")
        self.height: Optional[int] = data.get("height")
        self.preview_url: Optional[str] = data.get("previewUrl")


class Video(Attachment):
    def __init__(self, raw: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(raw=raw)
        data = raw or {}
        self.video_id: Optional[int] = data.get("videoId") or data.get("id")
        self.url: Optional[str] = data.get("url") or data.get("baseUrl")
        self.duration: int = data.get("duration", 0)
        self.width: Optional[int] = data.get("width")
        self.height: Optional[int] = data.get("height")
        self.thumbnail: Optional[str] = data.get("thumbnail")


class Audio(Attachment):
    def __init__(self, raw: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(raw=raw)
        data = raw or {}
        self.audio_id: Optional[int] = data.get("audioId") or data.get("id")
        self.url: Optional[str] = data.get("url")
        self.duration: int = data.get("duration", 0)
        self.performer: Optional[str] = data.get("performer")
        self.title: Optional[str] = data.get("title")


class Voice(Attachment):
    def __init__(self, raw: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(raw=raw)
        data = raw or {}
        self.voice_id: Optional[int] = data.get("voiceId") or data.get("id")
        self.url: Optional[str] = data.get("url")
        self.duration: int = data.get("duration", 0)
        self.waveform: Optional[List[int]] = data.get("waveform")


class Document(Attachment):
    def __init__(self, raw: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(raw=raw)
        data = raw or {}
        self.file_id: Optional[int] = data.get("fileId") or data.get("id")
        self.name: str = data.get("name", "document")
        self.size: int = data.get("size", 0)
        self.url: Optional[str] = data.get("url")
        self.mime_type: Optional[str] = data.get("mimeType")


class Sticker(Attachment):
    def __init__(self, raw: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(raw=raw)
        data = raw or {}
        self.sticker_id: Optional[int] = data.get("stickerId") or data.get("id")
        self.pack_id: Optional[str] = data.get("packId")
        self.url: Optional[str] = data.get("url") or data.get("baseUrl")


class PollOption:
    def __init__(self, text: str, votes: int = 0, id: Optional[int] = None) -> None:
        self.text = text
        self.votes = votes
        self.id = id


class Poll(Attachment):
    def __init__(self, raw: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(raw=raw)
        data = raw or {}
        self.poll_id: Optional[int] = data.get("pollId") or data.get("id")
        self.question: str = data.get("question", "")
        self.options: List[PollOption] = [
            PollOption(text=opt.get("text", ""), votes=opt.get("votes", 0), id=opt.get("id"))
            for opt in data.get("options", [])
        ]
        self.is_anonymous: bool = data.get("isAnonymous", True)
        self.is_multiple: bool = data.get("isMultiple", False)
        self.is_quiz: bool = data.get("isQuiz", False)
