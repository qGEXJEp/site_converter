import pytest
import os
import asyncio
from bs4 import BeautifulSoup
from unittest.mock import patch, MagicMock, AsyncMock

from site_converter.parser import SiteParser
from site_converter.downloader import AsyncDownloader

class TestSiteParser:
    @pytest.fixture
    def parser(self):
        return SiteParser(output_dir="test_offline")

    def test_classify_url(self, parser):
        assert parser.classify_url("http://example.com/image.png") == "images"
        assert parser.classify_url("http://example.com/style.css") == "css"
        assert parser.classify_url("http://example.com/script.js") == "scripts"
        assert parser.classify_url("http://example.com/font.woff2") == "fonts"
        assert parser.classify_url("http://example.com/data.json") == "json"
        assert parser.classify_url("http://example.com/video.mp4") == "videos"
        assert parser.classify_url("http://events.framer.com/special") == "scripts"
        assert parser.classify_url("http://example.com/unknown.xyz") == "misc"
        assert parser.classify_url("http://example.com/image.png?v=123") == "images"

    def test_categorize_external_url(self, parser):
        assert parser.categorize_external_url("http://w3.org/2000/svg") == "technical"
        assert parser.categorize_external_url("https://twitter.com/elonmusk") == "social"
        assert parser.categorize_external_url("https://google.com") == "external"

    @pytest.mark.asyncio
    async def test_fetch_input_local(self, parser, tmp_path):
        target = tmp_path / "test.html"
        target.write_text("<html><body>test</body></html>", encoding="utf-8")
        content = await parser.fetch_input(str(target))
        assert content == "<html><body>test</body></html>"

    @pytest.mark.asyncio
    @patch("site_converter.parser.aiohttp.ClientSession.get")
    async def test_fetch_input_remote(self, mock_get, parser):
        # We must use AsyncMock for the return value of response.text() because the parser does `await response.text()`
        mock_response = MagicMock()
        mock_response.text = AsyncMock(return_value="<html><body>remote test</body></html>")
        mock_response.raise_for_status = MagicMock()

        # Async context manager mock setup for `async with session.get(...)`
        mock_get.return_value.__aenter__.return_value = mock_response

        content = await parser.fetch_input("http://example.com")
        assert content == "<html><body>remote test</body></html>"
        mock_response.raise_for_status.assert_called_once()

class TestAsyncDownloader:
    @pytest.fixture
    def downloader(self):
        return AsyncDownloader(output_dir="test_offline")

    def test_guess_extension(self, downloader):
        assert downloader._guess_extension("image/png") == "png"
        assert downloader._guess_extension("application/json") == "json"
        assert downloader._guess_extension("text/css") == "css"
        assert downloader._guess_extension("application/unknown") == "bin"
        assert downloader._guess_extension(None) == "bin"