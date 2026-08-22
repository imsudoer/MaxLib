"""
Media upload, send, and download mixin for MaxClient.
"""
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING
from ...errors.exceptions import UploadError
from ...protocol.opcodes import Opcode
from ...types.media import Attachment, Document, Photo, Video, Voice
from ...types.message import Message
from ...utils.downloads import DownloadProgress, ProgressCallback, download_file
from ...utils.uploads import upload_binary_data, upload_multipart_file

if TYPE_CHECKING:
    from ..client import MaxClient


class MediaMixin:
    """
    Mixin providing media and file transmission features.
    """
    async def send_photo(
        self: "MaxClient",
        chat_id: Union[int, str],
        photo: Union[bytes, str, Path],
        *,
        caption: str = "",
        reply_to: Optional[Union[int, str]] = None,
        progress_callback: Optional[ProgressCallback] = None,
        parse_mode: str = "markdown",
    ) -> Message:
        """
        Uploads and sends a photo to a chat.
        """
        # 1. Request upload slot
        packet = await self.transport.invoke(Opcode.PHOTO_UPLOAD, {})
        upload_info = packet.payload or {}
        upload_url = upload_info.get("url")
        if not upload_url:
            raise UploadError(f"Failed to get photo upload URL: {upload_info}")

        # 2. Upload file data
        if isinstance(photo, (str, Path)):
            res = await upload_multipart_file(upload_url, photo, progress_callback=progress_callback)
        else:
            res = await upload_binary_data(upload_url, photo, progress_callback=progress_callback)

        photo_id = res.get("photoId") or upload_info.get("photoId") or upload_info.get("fileId")

        # 3. Form attachment structure
        attaches = [{
            "_type": "PHOTO",
            "photoId": photo_id,
            "token": upload_info.get("token"),
        }]

        # 4. Send message with photo attachment
        return await self.send_message(
            chat_id,
            caption,
            reply_to=reply_to,
            parse_mode=parse_mode,
            attaches=attaches,
        )

    async def send_document(
        self: "MaxClient",
        chat_id: Union[int, str],
        document: Union[bytes, str, Path],
        *,
        filename: Optional[str] = None,
        caption: str = "",
        reply_to: Optional[Union[int, str]] = None,
        progress_callback: Optional[ProgressCallback] = None,
        parse_mode: str = "markdown",
    ) -> Message:
        """
        Uploads and sends a document or general file to a chat.
        """
        packet = await self.transport.invoke(Opcode.FILE_UPLOAD, {})
        upload_info = packet.payload or {}
        upload_url = upload_info.get("url")
        if not upload_url:
            raise UploadError(f"Failed to get file upload URL: {upload_info}")

        if isinstance(document, (str, Path)):
            res = await upload_multipart_file(upload_url, document, progress_callback=progress_callback)
            doc_name = filename or Path(document).name
        else:
            res = await upload_binary_data(upload_url, document, progress_callback=progress_callback)
            doc_name = filename or "file.bin"

        file_id = res.get("fileId") or upload_info.get("fileId")

        attaches = [{
            "_type": "FILE",
            "fileId": file_id,
            "name": doc_name,
            "token": upload_info.get("token"),
        }]

        return await self.send_message(
            chat_id,
            caption,
            reply_to=reply_to,
            parse_mode=parse_mode,
            attaches=attaches,
        )

    async def send_voice(
        self: "MaxClient",
        chat_id: Union[int, str],
        voice: Union[bytes, str, Path],
        *,
        duration: int = 0,
        waveform: Optional[List[int]] = None,
        reply_to: Optional[Union[int, str]] = None,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> Message:
        """
        Uploads and sends a voice audio message.
        """
        packet = await self.transport.invoke(Opcode.AUDIO_UPLOAD, {})
        upload_info = packet.payload or {}
        upload_url = upload_info.get("url")
        if not upload_url:
            raise UploadError(f"Failed to get voice upload URL: {upload_info}")

        if isinstance(voice, (str, Path)):
            res = await upload_multipart_file(upload_url, voice, progress_callback=progress_callback)
        else:
            res = await upload_binary_data(upload_url, voice, progress_callback=progress_callback)

        audio_id = res.get("audioId") or upload_info.get("audioId") or upload_info.get("fileId")

        attaches = [{
            "_type": "VOICE",
            "voiceId": audio_id,
            "duration": duration,
            "waveform": waveform or [],
            "token": upload_info.get("token"),
        }]

        return await self.send_message(chat_id, "", reply_to=reply_to, attaches=attaches)

    async def send_sticker(
        self: "MaxClient",
        chat_id: Union[int, str],
        sticker_id: int,
        *,
        reply_to: Optional[Union[int, str]] = None,
    ) -> Message:
        """
        Sends a sticker by sticker ID.
        """
        attaches = [{
            "_type": "STICKER",
            "stickerId": int(sticker_id),
        }]
        return await self.send_message(chat_id, "", reply_to=reply_to, attaches=attaches)

    async def download_media(
        self: "MaxClient",
        message_or_attach: Union[Message, Attachment, str],
        destination: Optional[Union[str, Path]] = None,
        *,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> Path:
        """
        Downloads media attachment from a Message or Attachment object to local path.
        """
        url: Optional[str] = None
        target_name = "downloaded_file"

        if isinstance(message_or_attach, Message):
            if message_or_attach.photo:
                url = message_or_attach.photo.url
                target_name = f"photo_{message_or_attach.photo.photo_id}.jpg"
            elif message_or_attach.document:
                url = message_or_attach.document.url
                target_name = message_or_attach.document.name or f"file_{message_or_attach.document.file_id}"
            elif message_or_attach.voice:
                url = message_or_attach.voice.url
                target_name = f"voice_{message_or_attach.voice.voice_id}.ogg"
            elif message_or_attach.video:
                url = message_or_attach.video.url
                target_name = f"video_{message_or_attach.video.video_id}.mp4"
            elif message_or_attach.attaches:
                url = message_or_attach.attaches[0].url
        elif isinstance(message_or_attach, Attachment):
            url = message_or_attach.url
            if isinstance(message_or_attach, Document):
                target_name = message_or_attach.name
        elif isinstance(message_or_attach, str):
            url = message_or_attach

        if not url:
            raise ValueError("No downloadable URL found in media object")

        dest = Path(destination) if destination else Path(target_name)
        return await download_file(url, dest, progress_callback=progress_callback)
