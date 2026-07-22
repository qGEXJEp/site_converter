import os
import re
import asyncio
import logging
import aiohttp
from bs4 import BeautifulSoup
from typing import List, Tuple, Set, Dict, Any

from .config import DIRS, SOCIAL_DOMAINS, TECHNICAL_PATTERNS, EXTERNAL_WHITELIST
from .downloader import AsyncDownloader

logger = logging.getLogger(__name__)

class SiteParser:
    def __init__(self, output_dir: str):
        self.output_dir: str = output_dir

    def classify_url(self, url: str) -> str:
        lower_url = url.lower().split("?")[0]
        for folder, exts in DIRS.items():
            for ext in exts:
                if lower_url.endswith(f".{ext}"):
                    return folder

        if any(x in lower_url for x in [".mp4", ".webm"]):
            return "videos"
        if ".js" in lower_url or "events.framer.com" in lower_url:
            return "scripts"
        if ".css" in lower_url:
            return "css"
        if ".json" in lower_url:
            return "json"

        image_exts = [".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"]
        if any(x in lower_url for x in image_exts):
            return "images"

        return "misc"

    def categorize_external_url(self, url: str) -> str:
        lower_url = url.lower()
        for tech in TECHNICAL_PATTERNS:
            if tech in lower_url:
                return "technical"
        for dom in SOCIAL_DOMAINS:
            if dom in lower_url:
                return "social"
        return "external"

    def report_links(self, html_text: str) -> None:
        urls: List[str] = re.findall(r'https?://[^\s"\'<>]+', html_text)
        unique_urls = list(dict.fromkeys(urls))  # Preserve order, remove duplicates

        technical: List[str] = []
        social: List[str] = []
        external: List[str] = []

        for u in unique_urls:
            if any(w in u for w in EXTERNAL_WHITELIST):
                continue
            cat = self.categorize_external_url(u)
            if cat == "technical":
                technical.append(u)
            elif cat == "social":
                social.append(u)
            else:
                external.append(u)

        logger.info("\n⚙️ External Links Report")
        if external:
            logger.info("🌐 Real external links (not downloaded or ignored):")
            for e in external:
                logger.info(f" - {e}")
        else:
            logger.info("🌐 No real external links found.")

        if social:
            logger.info("\n📱 Social media links (preserved):")
            for s in social:
                logger.info(f" - {s}")

        if technical:
            logger.info("\n🧩 Technical (ignored) links:")
            for t in technical:
                logger.info(f" - {t}")

    async def fetch_input(self, target: str) -> str:
        if target.startswith("http://") or target.startswith("https://"):
            logger.info(f"Fetching remote HTML from {target}")
            async with aiohttp.ClientSession() as session:
                async with session.get(target) as response:
                    response.raise_for_status()
                    return await response.text()
        else:
            logger.info(f"Reading local file: {target}")
            with open(target, "r", encoding="utf-8") as f:
                return f.read()

    async def process_site(self, target: str) -> None:
        html_content = await self.fetch_input(target)
        soup = BeautifulSoup(html_content, "html.parser")

        # Strip specific header tags
        for tag in soup.find_all("link", rel="preconnect"):
            tag.decompose()
        for tag in soup.find_all("link", rel="canonical"):
            tag["href"] = ""
        for tag in soup.find_all("meta", property="og:url"):
            tag["content"] = ""

        download_queue: Set[Tuple[str, str]] = set() # (url, folder)
        tag_replacements: List[Tuple[Any, str, str]] = [] # (tag_object, attribute, original_url)

        # 1. Base Attributes (src & href)
        for tag in soup.find_all(["link", "script", "img", "video", "source"]):
            attr = "href" if tag.name == "link" else "src"
            if tag.has_attr(attr) and tag[attr].startswith("http"):
                url = tag[attr]
                folder = self.classify_url(url)
                download_queue.add((url, folder))
                tag_replacements.append((tag, attr, url))

        # 2. Meta tags
        for tag in soup.find_all("meta"):
            if tag.has_attr("content") and tag["content"].startswith("http"):
                url = tag["content"]
                folder = self.classify_url(url)
                download_queue.add((url, folder))
                tag_replacements.append((tag, "content", url))

        # 3. 'srcset' parsing
        srcset_tasks: List[Tuple[Any, List[Dict[str, str]]]] = []
        for tag in soup.find_all(["img", "source"]):
            if tag.has_attr("srcset"):
                raw_urls = [u.strip() for u in tag["srcset"].split(",")]
                parsed_urls: List[Dict[str, Any]] = []
                for u in raw_urls:
                    parts = u.split()
                    if not parts:
                        continue
                    url = parts[0]
                    size = " ".join(parts[1:]) if len(parts) > 1 else ""
                    if url.startswith("http"):
                        folder = self.classify_url(url)
                        download_queue.add((url, folder))
                        parsed_urls.append({"url": url, "size": size, "original": u})
                    else:
                        parsed_urls.append({"url": url, "size": size, "original": u, "skip": True})
                srcset_tasks.append((tag, parsed_urls))

        # 4. Inline <style> blocks
        style_tasks: List[Tuple[Any, str, List[str]]] = []
        for style in soup.find_all("style"):
            if style.string and "url(" in style.string:
                css = style.string
                # Regex fetches any valid URL wrapped in url('...')
                urls = re.findall(r'url\([\'"]?(https?://[^\)\'"]+)[\'"]?\)', css)
                for url in urls:
                    folder = self.classify_url(url)
                    download_queue.add((url, folder))
                style_tasks.append((style, css, urls))

        # 5. Inline <script> blocks
        script_tasks: List[Tuple[Any, str, List[str]]] = []
        url_pattern = re.compile(r'https?://[^\s"\'<>]+')
        for script in soup.find_all("script"):
            if script.string and "http" in script.string:
                matches = url_pattern.findall(script.string)
                for match in matches:
                    folder = self.classify_url(match)
                    download_queue.add((match, folder))
                script_tasks.append((script, script.string, matches))

        logger.info(f"Identified {len(download_queue)} unique assets. Starting concurrent download phase...")

        # Initiate Concurrent Downloads
        url_to_local: Dict[str, str] = {}
        async with AsyncDownloader(self.output_dir) as downloader:
            queue_list = list(download_queue)
            tasks = [downloader.download_file(url, folder) for url, folder in queue_list]
            results = await asyncio.gather(*tasks)
            for (url, _), local_path in zip(queue_list, results):
                if local_path:
                    url_to_local[url] = local_path

        # Apply Tag Changes with local cache values
        for tag, attr, url in tag_replacements:
            if url in url_to_local:
                tag[attr] = url_to_local[url]

        for tag, parsed_urls in srcset_tasks:
            new_urls = []
            for item in parsed_urls:
                if item.get("skip") or item["url"] not in url_to_local:
                    new_urls.append(item["original"])
                else:
                    new_urls.append(f"{url_to_local[item['url']]} {item['size']}".strip())
            tag["srcset"] = ", ".join(new_urls)

        for style, css, urls in style_tasks:
            new_css = css
            for url in urls:
                if url in url_to_local:
                    new_css = new_css.replace(url, url_to_local[url])
            style.string.replace_with(new_css)

        for script, code, urls in script_tasks:
            new_code = code
            for match in urls:
                if match in url_to_local:
                    new_code = new_code.replace(match, url_to_local[match])
            script.string.replace_with(new_code)

        # Output the parsed offline document
        os.makedirs(self.output_dir, exist_ok=True)
        out_html = os.path.join(self.output_dir, "index_offline.html")
        with open(out_html, "w", encoding="utf-8") as f:
            f.write(str(soup.prettify()))

        logger.info(f"✅ Conversion complete! Offline site successfully saved to '{out_html}'")
        self.report_links(str(soup))
