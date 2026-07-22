import os
import asyncio
import logging
import aiohttp
from urllib.parse import urlparse, unquote
from typing import Optional

from .config import CONTENT_TYPE_MAP

logger = logging.getLogger(__name__)

class AsyncDownloader:
    def __init__(self, output_dir: str, timeout: int = 60, max_concurrent: int = 20):
        self.output_dir: str = output_dir
        self.timeout: aiohttp.ClientTimeout = aiohttp.ClientTimeout(total=timeout)
        self.semaphore: asyncio.Semaphore = asyncio.Semaphore(max_concurrent)
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        connector = aiohttp.TCPConnector(limit=0)  # Rate limiting is handled by semaphore
        self.session = aiohttp.ClientSession(connector=connector, timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def _guess_extension(self, content_type: Optional[str], fallback: str = "bin") -> str:
        if not content_type:
            return fallback
        for ctype, ext in CONTENT_TYPE_MAP.items():
            if content_type.startswith(ctype):
                return ext
        return fallback

    async def download_file(self, url: str, folder: str) -> Optional[str]:
        if not self.session:
            raise RuntimeError("Downloader session is not initialized")

        try:
            parsed = urlparse(url)
            filename = unquote(os.path.basename(parsed.path)) or "file"
            if "?" in filename:
                filename = filename.split("?")[0]

            local_dir = os.path.join(self.output_dir, folder)
            os.makedirs(local_dir, exist_ok=True)
            local_path = os.path.join(local_dir, filename)

            if os.path.exists(local_path):
                logger.info(f"[SKIP] Already exists: {filename}")
                return f"{folder}/{filename}"

            async with self.semaphore:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        if "." not in filename or filename.endswith("file"):
                            content_type = response.headers.get("Content-Type", "")
                            ext = self._guess_extension(content_type)
                            filename = f"{filename}.{ext}"
                            local_path = os.path.join(local_dir, filename)

                        content = await response.read()
                        with open(local_path, "wb") as f:
                            f.write(content)
                        logger.info(f"[OK] Downloaded: {filename}")
                        return f"{folder}/{filename}"
                    else:
                        logger.error(f"[ERR] Failed {url}: HTTP {response.status}")
                        return None
        except asyncio.TimeoutError:
            logger.error(f"[TIMEOUT] while fetching {url}")
            return None
        except Exception as e:
            logger.error(f"[ERR] downloading {url}: {e}")
            return None
