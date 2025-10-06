import os
import re
import requests
from requests.adapters import HTTPAdapter, Retry
from bs4 import BeautifulSoup
from urllib.parse import urlparse, unquote

# ---- AYARLAR ----
INPUT_HTML = "index.html"
OUTPUT_DIR = "site_offline"

# Alt klasörler
DIRS = {
    "fonts": ["woff", "woff2", "ttf", "otf"],
    "images": ["png", "jpg", "jpeg", "gif", "svg", "ico", "webp"],
    "scripts": ["js", "mjs"],
    "css": ["css"],
    "json": ["json"],
    "videos": ["mp4", "webm"]
}

CONTENT_TYPE_MAP = {
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

# Domains/categories for reporting
SOCIAL_DOMAINS = [
    "x.com",
    "twitter.com",
    "instagram.com",
    "behance.net",
    "dribbble.com",
    "facebook.com",
    "linkedin.com",
    "framer.com"
]

TECHNICAL_PATTERNS = [
    "w3.org/2000/svg"
]

EXTERNAL_WHITELIST = []

session = requests.Session()
retries = Retry(total=2, backoff_factor=3, status_forcelist=[500, 502, 503, 504])
session.mount("http://", HTTPAdapter(max_retries=retries))
session.mount("https://", HTTPAdapter(max_retries=retries))

def prepare_folders():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for folder in DIRS:
        os.makedirs(os.path.join(OUTPUT_DIR, folder), exist_ok=True)

def guess_extension(content_type, fallback="bin"):
    if not content_type:
        return fallback
    for ctype, ext in CONTENT_TYPE_MAP.items():
        if content_type.startswith(ctype):
            return ext
    return fallback

def download_file(url, folder):
    try:
        parsed = urlparse(url)
        filename = unquote(os.path.basename(parsed.path)) or "file"
        if "?" in filename:
            filename = filename.split("?")[0]
        local_path = os.path.join(OUTPUT_DIR, folder, filename)
        if os.path.exists(local_path):
            print(f"[SKIP] {filename}")
            return f"{folder}/{filename}"
        r = session.get(url, timeout=60)
        if r.status_code == 200:
            if "." not in filename or filename.endswith("file"):
                ext = guess_extension(r.headers.get("Content-Type", ""))
                filename = filename + "." + ext
                local_path = os.path.join(OUTPUT_DIR, folder, filename)
            with open(local_path, "wb") as f:
                f.write(r.content)
            print(f"[OK] {filename}")
            return f"{folder}/{filename}"
        else:
            print(f"[ERR] {url} (status {r.status_code})")
    except Exception as e:
        print(f"[ERR] {url}: {e}")
    return None

def classify_url(url):
    lower = url.lower().split("?")[0]
    for folder, exts in DIRS.items():
        for ext in exts:
            if lower.endswith("." + ext):
                return folder
    if any(x in lower for x in [".mp4", ".webm"]):
        return "videos"
    if ".js" in lower or "events.framer.com" in lower:
        return "scripts"
    if ".css" in lower:
        return "css"
    if ".json" in lower:
        return "json"
    if any(x in lower for x in [".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"]):
        return "images"
    return "misc"

def process_attr(tag, attr):
    if tag.has_attr(attr):
        url = tag[attr]
        if url and url.startswith("http"):
            folder = classify_url(url)
            rel_path = download_file(url, folder)
            if rel_path:
                tag[attr] = rel_path

def find_all_external_urls(html_text):
    urls = re.findall(r'https?://[^\s"\'<>]+', html_text)
    seen, ordered = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u)
            ordered.append(u)
    return ordered

def categorize_url(url):
    lower = url.lower()
    for tech in TECHNICAL_PATTERNS:
        if tech in lower:
            return "technical"
    for dom in SOCIAL_DOMAINS:
        if dom in lower:
            return "social"
    return "external"

def check_external_links_with_categories(html_file):
    with open(html_file, "r", encoding="utf-8") as f:
        html = f.read()
    urls = find_all_external_urls(html)
    technical, social, external = [], [], []
    for u in urls:
        if any(w in u for w in EXTERNAL_WHITELIST):
            continue
        cat = categorize_url(u)
        if cat == "technical":
            technical.append(u)
        elif cat == "social":
            social.append(u)
        else:
            external.append(u)
    print("\n⚙️ Dış Link Raporu")
    if external:
        print("\n🌐 Gerçek dış bağlantılar (indirilmeyecek veya özel):")
        for e in external:
            print(" -", e)
    else:
        print("\n🌐 Gerçek dış bağlantı yok.")
    if social:
        print("\n📱 Sosyal medya linkleri (korundu):")
        for s in social:
            print(" -", s)
    else:
        print("\n📱 Sosyal medya linki yok.")
    if technical:
        print("\n🧩 Teknik (yok sayılan) bağlantılar:")
        for t in technical:
            print(" -", t)
    else:
        print("\n🧩 Teknik bağlantı yok.")

def main():
    if not os.path.exists(INPUT_HTML):
        print(f"❌ {INPUT_HTML} bulunamadı. Lütfen bu dosyayı aynı klasöre koy.")
        return
    prepare_folders()
    with open(INPUT_HTML, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    for tag in soup.find_all("link", rel="preconnect"):
        tag.decompose()
    for tag in soup.find_all("link", rel="canonical"):
        tag["href"] = ""
    for tag in soup.find_all("meta", property="og:url"):
        tag["content"] = ""

    for tag in soup.find_all(["link", "script", "img", "video", "source"]):
        attr = "href" if tag.name == "link" else "src"
        process_attr(tag, attr)

    for tag in soup.find_all("meta"):
        process_attr(tag, "content")

    for tag in soup.find_all(["img", "source"]):
        if tag.has_attr("srcset"):
            urls = [u.strip() for u in tag["srcset"].split(",")]
            new_urls = []
            for u in urls:
                parts = u.split()
                url = parts[0]
                size = " ".join(parts[1:]) if len(parts) > 1 else ""
                if url.startswith("http"):
                    folder = classify_url(url)
                    rel_path = download_file(url, folder)
                    if rel_path:
                        new_urls.append(f"{rel_path} {size}".strip())
                    else:
                        new_urls.append(u)
                else:
                    new_urls.append(u)
            tag["srcset"] = ", ".join(new_urls)

    for style in soup.find_all("style"):
        if style.string and "url(" in style.string:
            css = style.string
            parts = css.split("url(")
            new_css = parts[0]
            for part in parts[1:]:
                url = part.split(")")[0].strip("'\\\"")
                rest = ")".join(part.split(")")[1:])
                if url.startswith("http"):
                    folder = classify_url(url)
                    rel_path = download_file(url, folder)
                    if rel_path:
                        new_css += f"url({rel_path}){rest}"
                    else:
                        new_css += f"url({url}){rest}"
                else:
                    new_css += f"url({url}){rest}"
            style.string.replace_with(new_css)

    url_pattern = re.compile(r'https?://[^\s"\'<>]+')
    for script in soup.find_all("script"):
        if script.has_attr("src"):
            process_attr(script, "src")
        if script.string and "http" in script.string:
            new_code = script.string
            for match in url_pattern.findall(script.string):
                folder = classify_url(match)
                rel_path = download_file(match, folder)
                if rel_path:
                    new_code = new_code.replace(match, rel_path)
            script.string.replace_with(new_code)

    out_html = os.path.join(OUTPUT_DIR, "index_offline.html")
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(str(soup.prettify()))

    print("\n✅ İşlem tamamlandı! 'site_offline/index_offline.html' dosyasını açabilirsin.")
    check_external_links_with_categories(out_html)

if __name__ == "__main__":
    main()
