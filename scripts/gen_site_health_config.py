#!/usr/bin/env python3
"""
Generate site_health_config.json from Markdown doc.

Extracts:
  * Table rows with site name / URL / key
  * Detail list items with main, book, and chapter URLs
  * Ignores archived sites (under '#### 已归档站点')

Usage:
  python scripts/gen_site_health_config.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.progress import track

# ----------------------------
# Config
# ----------------------------

DOC_PATH = Path("./docs/4-supported-sites.md")
OUTPUT_PATH = Path(__file__).parent / "data" / "site_health_config.json"

# sites that require curl_cffi impersonation/http2
SPECIAL_SITES: set[str] = {"wenku8", "n69shuba"}

# sites to ignore manually (optional)
IGNORED_SITES: set[str] = {"linovel"}

console = Console()

# ----------------------------
# Regex patterns
# ----------------------------

TABLE_ROW_RE = re.compile(
    r"^\|\s*\[([^\]]+)\]\((https?://[^\s)]+)\)\s*\|\s*([a-zA-Z0-9_]+)\s*\|",
    re.M,
)

LIST_BLOCK_RE = re.compile(
    r"^\*\s*\*\*[^*]+?\(([a-zA-Z0-9_]+)\)\*\*.*?"
    r"书籍:\s*`(https?://[^\s`]+)`.*?"
    r"章节:\s*`(https?://[^\s`]+)`",
    re.S | re.M,
)

ARCHIVE_SECTION_RE = re.compile(r"####\s*已归档站点", re.M)

# ----------------------------
# Helpers
# ----------------------------


def split_active_and_archived(md_text: str) -> tuple[str, str]:
    """Split markdown into (active_part, archived_part)."""
    m = ARCHIVE_SECTION_RE.search(md_text)
    if not m:
        return md_text, ""
    idx = m.start()
    return md_text[:idx], md_text[idx:]


def parse_table(md_text: str) -> dict[str, str]:
    """Return mapping of site_key -> homepage URL from the table."""
    sites = {}
    for m in TABLE_ROW_RE.finditer(md_text):
        name, url, key = m.groups()
        sites[key] = url
    return sites


def parse_list(md_text: str) -> dict[str, tuple[str, str]]:
    """Return mapping of site_key -> (book_url, chapter_url)."""
    data = {}
    for m in LIST_BLOCK_RE.finditer(md_text):
        key, book, chapter = m.groups()
        data[key] = (book, chapter)
    return data


def build_config(
    table_sites: dict[str, str],
    list_sites: dict[str, tuple[str, str]],
    ignored: set[str],
) -> dict[str, Any]:
    """Merge and build final JSON config structure."""
    sites_block: dict[str, Any] = {}

    all_keys = sorted(set(table_sites) | set(list_sites))
    for key in track(all_keys, description="[cyan]Building site configs..."):
        if key in ignored:
            continue
        homepage = table_sites.get(key)
        book, chap = list_sites.get(key, (None, None))

        urls = [u for u in (homepage, book, chap) if u]
        if not urls:
            continue

        site_entry: dict[str, Any] = {"urls": urls}

        if key in SPECIAL_SITES:
            site_entry.update({"impersonate": "chrome136", "http2": True})

        sites_block[key] = site_entry

    config = {
        "max_concurrent": 12,
        "timeout": 20,
        "retries": 1,
        "speed_levels": {"slow": 2.0, "very_slow": 5.0},
        "sites": sites_block,
    }
    return config


def main() -> None:
    if not DOC_PATH.is_file():
        raise SystemExit(f"Markdown file not found: {DOC_PATH}")

    md_text = DOC_PATH.read_text(encoding="utf-8")

    # 1. Split active / archived sections
    active_md, archived_md = split_active_and_archived(md_text)
    archived_table_sites = parse_table(archived_md)
    archived_keys = set(archived_table_sites.keys())
    ignored = archived_keys | IGNORED_SITES

    # 2. Parse both sections
    table_sites = parse_table(active_md)
    list_sites = parse_list(md_text)

    # 3. Build config
    config = build_config(table_sites, list_sites, ignored)

    # 4. Output
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    console.print(
        f"[green]Generated:[/green] {OUTPUT_PATH}\n"
        f"Active sites: [cyan]{len(config['sites'])}[/cyan], "
        f"Ignored archived: [yellow]{len(ignored)}[/yellow]"
    )


if __name__ == "__main__":
    main()
