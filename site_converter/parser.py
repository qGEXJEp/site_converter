import os
import re
import asyncio
import logging
import aiofiles
import aiohttp
import lxml.html
from typing import List, Tuple, Set, Dict, Any, Optional

from .config import DIRS, SOCIAL_DOMAINS, TECHNICAL_PATTERNS, EXTERNAL_WHITELIST
from .downloader import AsyncDownloader

logger = logging.getLogger(__name__)

def _parse_and_transform_html(
    html_content: str, url_to_local: Optional[Dict[str, str]] = None
) -> Tuple[str, Set[Tuple[str, str]]]:
    """
    CPU-bound synchronous worker function for parsing HTML using lxml.
    Performs single-pass DOM traversal over all elements.

    If url_to_local is None, returns (html_content_unchanged, download_queue).
    If url_to_local is provided, updates attributes/content in DOM and returns (serialized_html, download_queue).
    """
    try:
        doc = lxml.html.fromstring(html_content)
    except Exception as e:
        logger.error(f"Failed to parse HTML with lxml: {e}")
        return html_content, set()

    download_queue: Set[Tuple[str, str]] = set()

    # Pre-compile URL regex for inline scripts and styles if needed
    url_pattern = re.compile(r'https?://[^\s"\'<>]+')
    style_url_pattern = re.compile(r'url\([\'"]?(https?://[^\)\'"]+)[\'"]?\)')

    # 1. Single-pass iteration over all DOM elements
    for elem in doc.iter():
        tag = elem.tag
        if not isinstance(tag, str):
            # Comments, processing instructions, etc.
            continue

        tag_name = tag.lower()

        # Handle specific header tags cleaning
        if tag_name == "link":
            rel = elem.get("rel", "")
            if isinstance(rel, str) and rel.lower() == "preconnect":
                parent = elem.getparent()
                if parent is not None:
                    parent.remove(elem)
                continue
            if isinstance(rel, str) and rel.lower() == "canonical":
                elem.set("href", "")

        elif tag_name == "meta":
            prop = elem.get("property", "")
            if isinstance(prop, str) and prop.lower() == "og:url":
                elem.set("content", "")
            elif "content" in elem.attrib and elem.attrib["content"].startswith("http"):
                url = elem.attrib["content"]
                folder = _classify_url_static(url)
                download_queue.add((url, folder))
                if url_to_local and url in url_to_local:
                    elem.attrib["content"] = url_to_local[url]

        # Handle src and href attributes for standard tags
        if tag_name in ("link", "script", "img", "video", "source"):
            attr = "href" if tag_name == "link" else "src"
            if attr in elem.attrib and elem.attrib[attr].startswith("http"):
                url = elem.attrib[attr]
                folder = _classify_url_static(url)
                download_queue.add((url, folder))
                if url_to_local and url in url_to_local:
                    elem.attrib[attr] = url_to_local[url]

        # Handle srcset attribute
        if tag_name in ("img", "source") and "srcset" in elem.attrib:
            srcset_val = elem.attrib["srcset"]
            raw_entries = [u.strip() for u in srcset_val.split(",") if u.strip()]
            new_entries = []

            for entry in raw_entries:
                parts = entry.split()
                if not parts:
                    continue
                url = parts[0]
                size = " ".join(parts[1:]) if len(parts) > 1 else ""

                if url.startswith("http"):
                    folder = _classify_url_static(url)
                    download_queue.add((url, folder))

                    if url_to_local and url in url_to_local:
                        local_url = url_to_local[url]
                        new_entries.append(f"{local_url} {size}".strip())
                    else:
                        new_entries.append(entry)
                else:
                    new_entries.append(entry)

            if url_to_local and new_entries:
                elem.attrib["srcset"] = ", ".join(new_entries)

        # Handle inline <style> elements
        if tag_name == "style" and elem.text:
            css_text = elem.text
            if "url(" in css_text:
                matches = style_url_pattern.findall(css_text)
                for url in matches:
                    folder = _classify_url_static(url)
                    download_queue.add((url, folder))

                if url_to_local:
                    new_css = css_text
                    for url in matches:
                        if url in url_to_local:
                            new_css = new_css.replace(url, url_to_local[url])
                    elem.text = new_css

        # Handle inline <script> elements
        if tag_name == "script" and elem.text:
            js_text = elem.text
            if "http" in js_text:
                matches = url_pattern.findall(js_text)
                for match in matches:
                    folder = _classify_url_static(match)
                    download_queue.add((match, folder))

                if url_to_local:
                    new_js = js_text
                    for match in matches:
                        if match in url_to_local:
                            new_js = new_js.replace(match, url_to_local[match])
                    elem.text = new_js

    # Serialize back to HTML string safely
    serialized_html = lxml.html.tostring(doc, encoding="utf-8", method="html").decode("utf-8")
    return serialized_html, download_queue

def _classify_url_static(url: str) -> str:
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

class SiteParser:
    def __init__(self, output_dir: str):
        self.output_dir: str = output_dir

    def classify_url(self, url: str) -> str:
        return _classify_url_static(url)

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

        # 1. Parse HTML and extract download queue in a thread pool (Event Loop Isolation)
        _, download_queue = await asyncio.to_thread(_parse_and_transform_html, html_content, None)

        logger.info(f"Identified {len(download_queue)} unique assets. Starting concurrent download phase.")

        # 2. Initiate Concurrent Downloads
        url_to_local: Dict[str, str] = {}
        async with AsyncDownloader(self.output_dir) as downloader:
            queue_list = list(download_queue)
            tasks = [downloader.download_file(url, folder) for url, folder in queue_list]
            results = await asyncio.gather(*tasks)
            for (url, _), local_path in zip(queue_list, results):
                if local_path:
                    url_to_local[url] = local_path

        # 3. Apply local URL replacements and serialize in a thread pool (Event Loop Isolation)
        transformed_html, _ = await asyncio.to_thread(_parse_and_transform_html, html_content, url_to_local)

        # 4. Output the parsed offline document
        os.makedirs(self.output_dir, exist_ok=True)
        out_html = os.path.join(self.output_dir, "index_offline.html")
        with open(out_html, "w", encoding="utf-8") as f:
            f.write(transformed_html)

        logger.info(f"✅ Conversion complete! Offline site successfully saved to '{out_html}'")
        self.report_links(transformed_html)