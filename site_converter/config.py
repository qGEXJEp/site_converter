from typing import Dict, List

DIRS: Dict[str, List[str]] = {
    "fonts": ["woff", "woff2", "ttf", "otf"],
    "images": ["png", "jpg", "jpeg", "gif", "svg", "ico", "webp"],
    "scripts": ["js", "mjs"],
    "css": ["css"],
    "json": ["json"],
    "videos": ["mp4", "webm"]
}

CONTENT_TYPE_MAP: Dict[str, str] = {
    "application/javascript": "js",
    "text/javascript": "js",
    "application/x-javascript": "js",
    "text/css": "css",
    "application/json": "json",
    "font/woff2": "woff2",
    "font/woff": "woff",
    "font/ttf": "ttf",
    "font/otf": "otf",
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/svg+xml": "svg",
    "image/gif": "gif",
    "image/webp": "webp",
    "video/mp4": "mp4",
    "video/webm": "webm"
}

SOCIAL_DOMAINS: List[str] = [
    "x.com",
    "twitter.com",
    "instagram.com",
    "behance.net",
    "dribbble.com",
    "facebook.com",
    "linkedin.com",
    "framer.com"
]

TECHNICAL_PATTERNS: List[str] = [
    "w3.org/2000/svg"
]

EXTERNAL_WHITELIST: List[str] = []
