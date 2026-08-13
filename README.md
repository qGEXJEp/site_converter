# Site Converter

[![Python Version](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://img.shields.io/pypi/v/site-converter?color=orange)](https://pypi.org/project/site-converter/)

## Overview
**Site Converter** is a production-ready, highly concurrent command-line utility designed to archive web pages and convert them into fully functional, offline-ready static assets. The engine automatically traverses a given URL, downloads all embedded resources (images, stylesheets, scripts, and fonts), and rewrites HTML references to local paths.

This version marks a complete architectural rewrite, moving from synchronous blocking scripts to a fully asynchronous, `lxml`-powered parser for maximum performance and zero memory leakage.

---

## Features

- **Asynchronous Engine:** Built on `asyncio` and `aiofiles` for blazing-fast, non-blocking I/O operations.
- **Deep Asset Detection:** Automatically parses and extracts embedded links, scripts, stylesheets, and media files.
- **Local Path Rewriting:** Modifies DOM elements in the HTML to point exclusively to downloaded local assets.
- **CLI Native:** Globally installable package that acts as a native terminal command.

---

## Installation

Ensure you have **Python 3.8 or higher** installed. Since `v2.0.0`, Site Converter is officially available on PyPI. Install it globally with a single command:

    pip install site-converter

---

## Usage

You no longer need to clone the repository or run python scripts manually. Just execute the native command from anywhere in your terminal:

    site-converter [https://www.example.com](https://www.example.com)

Upon completion, the offline version of the site will be generated in the `site_offline/` directory in your current working path. Open `site_offline/index_offline.html` in any web browser to view the result.

### Directory Structure

    site_offline/
    ├── index_offline.html      # Processed, offline-ready HTML file
    ├── images/                 # Downloaded image assets
    ├── scripts/                # Extracted JavaScript files
    └── styles/                 # Downloaded CSS stylesheets

---

## Limitations

| Constraint | Description |
| :--- | :--- |
| **Dynamic Frameworks** | Applications heavily reliant on Client-Side Rendering (React, Vue, Angular) may not render correctly offline. |
| **Authentication & CORS** | Assets protected by paywalls, login sessions, or strict CORS policies will fail to download. |

---

## Legal Notice & Disclaimer

This software is provided for **educational, personal archiving, and authorized research purposes only**. 

The developer assumes **no responsibility** for any misuse, copyright infringement, or violation of terms of service committed by third parties. You are explicitly prohibited from using this tool to bypass authentication mechanisms, digital rights management (DRM), or to illegally mirror and redistribute commercial properties. 

---

## Contributing

Contributions are welcome. If you find a bug or have a feature request, please follow standard GitHub Flow and open an issue:

- **Issue Tracker:** [https://github.com/iemirakman/site-converter/issues](https://github.com/iemirakman/site-converter/issues)

---

## License & Author

- **Author:** İbrahim Emir Akman
- **Email:** iemirakman@icloud.com
- **GitHub:** [@iemirakman](https://github.com/iemirakman)

Distributed under the MIT License. See `LICENSE` for more information.