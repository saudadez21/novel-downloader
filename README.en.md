# novel-downloader

[![PyPI](https://img.shields.io/pypi/v/novel-downloader.svg)](https://pypi.org/project/novel-downloader/)
[![Python](https://img.shields.io/pypi/pyversions/novel-downloader.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/saudadez21/novel-downloader/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/saudadez21/novel-downloader/actions/workflows/ci.yml)
[![Hits-of-Code](https://hitsofcode.com/github/saudadez21/novel-downloader?branch=main&label=Hits-of-Code)](https://hitsofcode.com/github/saudadez21/novel-downloader/view?branch=main&label=Hits-of-Code)

[中文](./README.md) | [English](./README.en.md)

Asynchronous, modular, and extensible toolkit for downloading and processing online novels.

Supports resumable crawling, multi-format exporting, text processing pipeline, CLI, and optional Web UI.

**Documentation**: [Project Documentation](https://saudadez21.github.io/novel-downloader/)

**Requirements**: Python 3.11+ (development tested on Python 3.13)

---

## Features

* Asynchronous and high-performance crawling
* Resumable downloads (checkpoint recovery)
* Pluggable HTTP backends: `aiohttp`, `httpx`, `curl_cffi`
* Export to TXT, EPUB, and HTML
* Text processing pipeline: ad removal, zh conversion, translation, etc.
* Optional support for image chapters and obfuscated content
* Plugin system for site parsers, exporters, and processing pipelines
* CLI and optional Web GUI

See the full feature list in the documentation: [Full Feature Overview](https://saudadez21.github.io/novel-downloader/)

---

## Installation

Install the latest stable release:

```bash
pip install -U novel-downloader
```

Install with Web UI support:

```bash
pip install novel-downloader[web-ui]
```

For all optional features (Web UI, OCR, image-to-text, extra backends, exporters, etc.), refer to the [Full Installation Guide](https://saudadez21.github.io/novel-downloader/guide/installation/).

---

## Quick Start (CLI)

```bash
# Set preferred interface language
novel-cli config set-lang en_US

# Download a novel
novel-cli download https://www.example.com/book/123/

# Using site + book ID
novel-cli download --site n23qb 12282
```

More examples: [CLI Examples](https://saudadez21.github.io/novel-downloader/guide/cli-examples/)

---

## Programmatic API

```python
import asyncio
from novel_downloader.plugins import registrar
from novel_downloader.schemas import BookConfig, ClientConfig

async def main() -> None:
    site = "n23qb"
    book = BookConfig(book_id="12282")

    cfg = ClientConfig(request_interval=0.5)
    client = registrar.get_client(site, cfg)

    async with client:
        await client.download_book(book)

    client.export_book(book, formats=["txt", "epub"])

if __name__ == "__main__":
    asyncio.run(main())
```

More examples: [API Examples](https://saudadez21.github.io/novel-downloader/reference/api-examples/)

---

## Development

```bash
git clone https://github.com/saudadez21/novel-downloader.git
cd novel-downloader

pip install .
# Optional:
# pip install .[all]
# pip install -e .[dev,all]
```

Translations (optional):

```bash
pip install babel
pybabel compile -d src/novel_downloader/locales
```

PRs and issues are welcome.

---

## Notes

* Site structures may change. If parsing issues occur, please open an issue or submit a patch.
* Login support depends on site policies. Cookies or manual account setup may be required.
* Configure request intervals responsibly to avoid rate limiting or IP blocking.

---

## Disclaimer

This project is for learning and research purposes only.

Do not use it for commercial or illegal activities.

Users are responsible for complying with target sites' `robots.txt` and local regulations.
The author assumes no liability for misuse.
