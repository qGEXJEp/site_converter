# 🧩 Site Converter — Make Any Website Work Offline

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue?logo=python" alt="Python Version">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/Status-Stable-success" alt="Status">
</p>

**Site Converter** is a Python tool that automatically scans any website, detects all embedded resources (images, videos, fonts, CSS, JS, etc.), downloads them to your computer, and updates all links inside the HTML file so the website can work **completely offline**.

Perfect for archiving, research, or creating backups of static websites. 🌍💾

---

## 🚀 Features

- 🌐 Automatically detects **all embedded links and assets**  
- 💾 Downloads images, fonts, CSS, JS, and media to local folders  
- 🔗 Rewrites HTML references to **local paths**  
- 🧠 Smart file renaming system prevents duplication or conflicts  
- ⚡ Simple command-line interface  
- 💻 Works cross-platform (Windows, macOS, Linux)

---

## ⚙️ Installation

Make sure you have **Python 3.8+** installed.

```bash
# Install required libraries
pip install requests beautifulsoup4 tqdm

# Clone the repository
git clone https://github.com/iemirakman/site-converter.git
cd site-converter
```

---

## 🧭 Usage

Convert any online website into a fully offline version with one command:

```bash
python site_converter.py https://www.example.com
```

When finished, you’ll find the offline site inside a folder named `site_offline/`.

### Example Output
```
[INFO] Starting download from https://example.com
[✔] Downloaded: 34 images, 8 CSS files, 5 JS scripts
✅ Done! Open 'site_offline/index_offline.html' in your browser.
```

---

## 🗂️ Folder Structure

```
site_offline/
│
├── index_offline.html      # Offline-ready HTML
├── images/                 # All image assets
├── scripts/                # JavaScript files
└── styles/                 # CSS stylesheets
```

---

## ⚠️ Known Issues

| Issue | Description |
|-------|--------------|
| 🌀 Dynamic Frameworks | React / Vue / Angular apps may not render offline correctly |
| 🔐 Protected Assets | CORS or login-protected files may fail to download |
| ⏳ Large Websites | For very large sites, downloading might take a long time |

---

## 💡 Tips & Tricks

- Open `index_offline.html` in your browser to test the offline version  
- If some assets aren’t appearing, edit `base_url` or the `replace_links()` function in the source code  
- For automation, you can easily wrap this tool into your own scripts or schedulers  

---

## ⚖️ Legal Notice

> **Disclaimer:**  
> This tool is intended for **personal, educational, or authorized use only**.  
> Do **not** use it to download, copy, or redistribute copyrighted websites or content without permission.  
> The developer assumes **no responsibility** for any misuse or violation of terms of service by third parties.  
>  
> ✅ You are free to use this tool to:
> - Back up your own websites  
> - Work on authorized or open-source projects  
> - Study or test static site structures  
>  
> 🚫 Do not use it to:
> - Copy or mirror commercial or copyrighted websites  
> - Circumvent login systems, paywalls, or digital protections  
> - Redistribute downloaded content publicly

---

## 🤝 Contributing

Contributions, ideas, and pull requests are always welcome!  
To report bugs or suggest features, open an issue here:  
👉 [https://github.com/iemirakman/site-converter/issues](https://github.com/qGEXJEp/site-converter/issues)

Please follow standard [GitHub Flow](https://guides.github.com/introduction/flow/) for contributions.

---

### ✨ Author

Created by **İbrahim Emir Akman**  
📧 Email: i.emir.ak01@gmail.com  
🐙 GitHub: [https://github.com/iemirakman](https://github.com/iemirakman)

---

⭐ If you find this project useful, don’t forget to **star** the repository!
