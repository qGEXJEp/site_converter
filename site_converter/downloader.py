import os
import asyncio
import logging
import aiohttp
import aiofiles
import aiofiles.os  # Klasör kontrolleri için asenkron I/O
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
        connector = aiohttp.TCPConnector(limit=0)
        self.session = aiohttp.ClientSession(connector=connector, timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    # Orijinal kodundaki bu metodu KESİNLİKLE tutmalısın
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
            file_path = unquote(parsed.path.lstrip('/')) or "index.html"
            
            # Alt klasörleri ve dosya isimlerini ayır
            local_dir = os.path.join(self.output_dir, folder, os.path.dirname(file_path))
            filename = os.path.basename(file_path) or "index.html"

            # 1. Klasör oluşturmayı asenkron yap (Döngüyü tıkama)
            if not await aiofiles.os.path.exists(local_dir):
                await asyncio.to_thread(os.makedirs, local_dir, exist_ok=True)

            local_path = os.path.join(local_dir, filename)

            if await aiofiles.os.path.exists(local_path):
                logger.info(f"[SKIP] Zaten var: {local_path}")
                return f"{folder}/{file_path}"

            async with self.semaphore:
                async with self.session.get(url) as response:
                    if response.status != 200:
                        logger.error(f"[ERR] Başarısız {url}: HTTP {response.status}")
                        return None
                    
                    # 2. Eksik uzantıları Content-Type'dan tahmin et ve düzelt
                    if "." not in filename or filename.endswith("file"):
                        content_type = response.headers.get("Content-Type", "")
                        ext = self._guess_extension(content_type)
                        if ext:
                            filename = f"{filename}.{ext}"
                            local_path = os.path.join(local_dir, filename)
                            file_path = os.path.join(os.path.dirname(file_path), filename).replace("\\", "/")

                    # İçeriği parçalar (chunks) halinde diske asenkron yaz (RAM dostu)
                    async with aiofiles.open(local_path, "wb") as f:
                        async for chunk in response.content.iter_chunked(64 * 1024):
                            await f.write(chunk)
                    
                    logger.info(f"[OK] İndirildi: {local_path}")
                    return f"{folder}/{file_path}"
                    
        except asyncio.TimeoutError:
            logger.error(f"[TIMEOUT] İndirme zaman aşımı: {url}")
            return None
        except Exception as e:
            logger.error(f"[ERR] İndirme hatası {url}: {e}")
            return None