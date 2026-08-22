"""
Media & File upload utility for MAX messenger using aiohttp.
"""
import io
import mimetypes
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Union
import aiohttp

from ..errors.exceptions import UploadError


@dataclass
class UploadProgress:
    current: int
    total: int
    speed: float = 0.0  # Bytes per second
    eta: float = 0.0    # Estimated seconds remaining

    @property
    def percentage(self) -> float:
        return (self.current / self.total * 100) if self.total > 0 else 0.0


ProgressCallback = Callable[[UploadProgress], Any]


async def upload_binary_data(
    url: str,
    data: Union[bytes, io.BytesIO, Path, str],
    *,
    headers: Optional[Dict[str, str]] = None,
    progress_callback: Optional[ProgressCallback] = None,
    chunk_size: int = 65536,
) -> Dict[str, Any]:
    """
    Uploads raw binary stream to upload endpoint with progress updates.
    """
    if isinstance(data, (str, Path)):
        file_path = Path(data)
        total_size = file_path.stat().st_size
        file_obj = open(file_path, "rb")
        should_close = True
    elif isinstance(data, bytes):
        total_size = len(data)
        file_obj = io.BytesIO(data)
        should_close = False
    elif isinstance(data, io.BytesIO):
        file_obj = data
        file_obj.seek(0, os.SEEK_END)
        total_size = file_obj.tell()
        file_obj.seek(0)
        should_close = False
    else:
        raise ValueError("Unsupported data type for upload")

    req_headers = headers.copy() if headers else {}
    if "Content-Type" not in req_headers:
        req_headers["Content-Type"] = "application/octet-stream"

    start_time = time.time()
    uploaded_bytes = 0

    async def _stream_generator():
        nonlocal uploaded_bytes
        while True:
            chunk = file_obj.read(chunk_size)
            if not chunk:
                break
            uploaded_bytes += len(chunk)
            elapsed = max(time.time() - start_time, 0.001)
            speed = uploaded_bytes / elapsed
            remaining = total_size - uploaded_bytes
            eta = (remaining / speed) if speed > 0 else 0.0

            if progress_callback:
                prog = UploadProgress(current=uploaded_bytes, total=total_size, speed=speed, eta=eta)
                try:
                    res = progress_callback(prog)
                    if hasattr(res, "__await__"):
                        await res
                except Exception:
                    pass

            yield chunk

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=_stream_generator(), headers=req_headers) as resp:
                text = await resp.text()
                if resp.status not in (200, 201):
                    raise UploadError(f"Upload failed with HTTP status {resp.status}: {text}", status_code=resp.status, response_text=text)
                try:
                    return await resp.json()
                except Exception:
                    return {"response": text}
    finally:
        if should_close:
            file_obj.close()


async def upload_multipart_file(
    url: str,
    file_path: Union[str, Path],
    *,
    field_name: str = "file",
    extra_fields: Optional[Dict[str, str]] = None,
    progress_callback: Optional[ProgressCallback] = None,
) -> Dict[str, Any]:
    """
    Uploads a file using multipart/form-data.
    """
    path = Path(file_path)
    mime_type, _ = mimetypes.guess_type(str(path))
    content_type = mime_type or "application/octet-stream"

    data = aiohttp.FormData()
    if extra_fields:
        for k, v in extra_fields.items():
            data.add_field(k, str(v))

    with open(path, "rb") as f:
        file_bytes = f.read()

    data.add_field(field_name, file_bytes, filename=path.name, content_type=content_type)

    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data) as resp:
            text = await resp.text()
            if resp.status not in (200, 201):
                raise UploadError(f"Multipart upload failed with status {resp.status}: {text}", status_code=resp.status, response_text=text)
            try:
                return await resp.json()
            except Exception:
                return {"response": text}
