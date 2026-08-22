"""
Media & File download utility for MAX messenger using aiohttp.
"""
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional, Union
import aiohttp

from ..errors.exceptions import DownloadError


@dataclass
class DownloadProgress:
    current: int
    total: int
    speed: float = 0.0
    eta: float = 0.0

    @property
    def percentage(self) -> float:
        return (self.current / self.total * 100) if self.total > 0 else 0.0


ProgressCallback = Callable[[DownloadProgress], Any]


async def download_file(
    url: str,
    destination: Union[str, Path],
    *,
    chunk_size: int = 65536,
    progress_callback: Optional[ProgressCallback] = None,
) -> Path:
    """
    Downloads file from URL to destination path with progress tracking.
    """
    dest_path = Path(destination)
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise DownloadError(f"Download failed with HTTP status {resp.status}: {text}", status_code=resp.status)

            total_size = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            start_time = time.time()

            with open(dest_path, "wb") as f:
                async for chunk in resp.content.iter_chunked(chunk_size):
                    f.write(chunk)
                    downloaded += len(chunk)
                    elapsed = max(time.time() - start_time, 0.001)
                    speed = downloaded / elapsed
                    remaining = total_size - downloaded
                    eta = (remaining / speed) if speed > 0 else 0.0

                    if progress_callback:
                        prog = DownloadProgress(current=downloaded, total=total_size, speed=speed, eta=eta)
                        try:
                            res = progress_callback(prog)
                            if hasattr(res, "__await__"):
                                await res
                        except Exception:
                            pass

    return dest_path
