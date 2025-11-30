#!/usr/bin/env python3
"""
Generate docs/supported-sites/*

Usage:
    python scripts/gen_site_docs.py --overwrite
    python scripts/gen_site_docs.py --clean
"""

from __future__ import annotations

import argparse
import json
import tomllib
from pathlib import Path
from typing import Literal, NotRequired, TypedDict

# ================================
# Path constants
# ================================

PROJECT_ROOT = Path(__file__).parent.parent
DOC_DIR = PROJECT_ROOT / "docs" / "supported-sites"
CONFIG_PATH = PROJECT_ROOT / "scripts" / "data" / "supported_sites.toml"
LANGUAGE_MAP_PATH = PROJECT_ROOT / "scripts" / "data" / "language_map.json"
LANGUAGE_MAP = json.loads(LANGUAGE_MAP_PATH.read_text(encoding="utf-8"))


# ================================
# Templates
# ================================

TAGS_TEMPLATE = """\
# 标签索引 (站点)

<!-- material/tags { scope: true } -->
"""

INDEX_TEMPLATE = """\
# Supported Sites / 支持站点

!!! info "说明"
    本页面列出了 NovelDownloader 当前支持的站点, 并提供各站点的功能支持情况概览。

    点击站点名称进入详情页, 可查看 **URL 示例、站点状态、功能支持级别** 等信息。

---

## 标签分类 (Tags)

参见：[标签索引](./tags.md)

---

## 支持站点总览 (Overview)

下表展示各站点的基础支持情况:

* :material-check: = 支持
* :material-close: = 不支持
* :material-help-circle: = 部分支持
* :material-open-in-new: = 站点原生支持 (需站内操作)

| 站点名称    | 标识符  | 分卷  | 图片  | 登录 | 搜索  |
| ---------- | ------- | ----- | ---- | ---- | ---- |
{table}
"""


DETAIL_TEMPLATE = """\
---
title: {name}
tags:
{tags}
---

{description}

## 基本信息

* 标识符: `{id}`
* 主页: {homepage}{alt_domains}
* 语言: {languages}
* 站点状态: {status}
* 支持分卷: {volumes}
* 支持插图: {images}
* 支持登录: {login}
* 支持搜索: {search}

---

## URL 示例

{url_examples}

{notes}
"""


# ================================
# Mapping
# ================================

STATUS_MAP = {
    "active": (":green_circle:", "Active"),
    "unstable": (":orange_circle:", "Unstable"),
    "archived": (":red_circle:", "Archived"),
}

SUPPORT_MAP = {
    "yes": (":material-check:", "是"),
    "no": (":material-close:", "否"),
    "partial": (":material-help-circle:", "部分支持"),
    "external": (":material-open-in-new:", "站点支持，需站内操作"),
}


# ================================
# TypedDicts
# ================================


class SupportDict(TypedDict):
    volumes: Literal["yes", "no", "partial", "external"]
    images: Literal["yes", "no", "partial", "external"]
    login: Literal["yes", "no", "partial", "external"]
    search: Literal["yes", "no", "partial", "external"]


class LoginNotes(TypedDict):
    content: str


class UrlExample(TypedDict):
    title: str
    url: str
    hidden: bool
    book_id: NotRequired[str]
    chapter_id: NotRequired[str]


class NoteItem(TypedDict):
    title: str
    content: str


class SiteConfig(TypedDict):
    id: str
    name: str
    homepage: str
    alt_domains: list[str]
    site_status: Literal["active", "unstable", "archived"]
    description: str
    languages: list[str]
    tags: list[str]
    supports: SupportDict
    login_notes: LoginNotes
    url_examples: list[UrlExample]
    notes: list[NoteItem]


# ================================
# Utility
# ================================


def lang_to_cn(code: str) -> str:
    normalized = code.strip().lower()
    return LANGUAGE_MAP.get(normalized, code)


def render_status(value: str, *, icon_only: bool = False) -> str:
    icon, txt = STATUS_MAP.get(value, (":material-help-circle:", value))
    return icon if icon_only else f"{icon} {txt}"


def render_support(value: str, *, icon_only: bool = False) -> str:
    icon, txt = SUPPORT_MAP.get(value, (":material-help-circle:", value))
    return icon if icon_only else f"{icon} {txt}"


def load_site_configs(path: Path) -> list[SiteConfig]:
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    result: list[SiteConfig] = []
    for sid, cfg in raw.get("sites", {}).items():
        cfg["id"] = sid
        result.append(cfg)  # type: ignore
    return result


# ================================
# Builder
# ================================


class SupportedSiteBuilder:
    def __init__(self):
        self.rows: list[tuple[str, str]] = []  # (site_id, table_row_str)
        self.detail_pages: dict[str, str] = {}  # "site-details/<id>.md" -> md

    def add_site(self, site: SiteConfig) -> None:
        """
        Add a single site. This immediately constructs:
        * table row
        * detail page content
        """
        sid = site["id"]
        self.rows.append((sid, self._make_overview_row(site)))
        self.detail_pages[f"site-details/{sid}.md"] = self._make_detail_page(site)

    def build(self, target_dir: Path, overwrite: bool = False) -> None:
        """Write index.md + detail pages into target_dir."""
        target_dir.mkdir(parents=True, exist_ok=True)

        # 1. sort rows by site_id
        sorted_rows = [row for _, row in sorted(self.rows, key=lambda x: x[0].lower())]

        # 2. index page
        index_md = INDEX_TEMPLATE.format(table="\n".join(sorted_rows))
        self._write_file(target_dir / "index.md", index_md, overwrite)

        # 3. tags.md
        self._write_file(target_dir / "tags.md", TAGS_TEMPLATE, overwrite)

        # 4. detail pages
        for rel, content in self.detail_pages.items():
            self._write_file(target_dir / rel, content, overwrite)

    def _write_file(self, path: Path, content: str, overwrite: bool) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and not overwrite:
            print(f"[skip] {path}")
            return
        path.write_text(content, encoding="utf-8", newline="\n")
        print(f"[write] {path}")

    def _make_overview_row(self, site: SiteConfig) -> str:
        sid = site["id"]
        s = site["supports"]
        return (
            f"| [{site['name']}](./site-details/{sid}.md)"
            f" | `{sid}`"
            f" | {render_support(s['volumes'], icon_only=True)}"
            f" | {render_support(s['images'], icon_only=True)}"
            f" | {render_support(s['login'], icon_only=True)}"
            f" | {render_support(s['search'], icon_only=True)} |"
        )

    def _make_detail_page(self, site: SiteConfig) -> str:
        sid = site["id"]
        supports = site["supports"]

        # alt_domains
        if site["alt_domains"]:
            alt_lines = ["\n* 备用域名:"]
            for d in site["alt_domains"]:
                alt_lines.append(f"    * {d}")
            alt_domains_block = "\n".join(alt_lines)
        else:
            alt_domains_block = ""

        url_blocks = []
        for ex in site["url_examples"]:
            if ex["hidden"]:
                continue

            blk = f"### {ex['title']}\n\nURL:\n\n```\n{ex['url']}\n```\n"
            if bid := ex.get("book_id"):
                blk += f"\n* Book ID: `{bid}`"
            if cid := ex.get("chapter_id"):
                blk += f"\n* Chapter ID: `{cid}`"

            url_blocks.append(blk)

        notes = []
        for note in site.get("notes", []):
            notes.append(f"## {note['title']}\n\n{note['content'].strip()}")

        # tags = languages + explicit tags
        all_tags = [lang_to_cn(x) for x in site["languages"]] + site["tags"]

        all_notes = "---\n\n" + "\n\n".join(notes) if notes else ""

        result = DETAIL_TEMPLATE.format(
            name=site["name"],
            id=sid,
            homepage=site["homepage"],
            alt_domains=alt_domains_block,
            description=site["description"].strip(),
            languages=", ".join(lang_to_cn(x) for x in site["languages"]),
            status=render_status(site["site_status"]),
            volumes=render_support(supports["volumes"]),
            images=render_support(supports["images"]),
            login=render_support(supports["login"]),
            search=render_support(supports["search"]),
            tags="".join(f"  - {t}\n" for t in all_tags),
            url_examples="\n\n".join(url_blocks),
            notes=all_notes,
        )
        return result.rstrip() + "\n"


# ================================
# Main
# ================================


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    parser.add_argument("--target", type=Path, default=DOC_DIR)
    args = parser.parse_args()

    if args.clean and args.target.exists():
        import shutil

        shutil.rmtree(args.target)
        print(f"[clean] removed {args.target}")

    sites = load_site_configs(args.config)
    builder = SupportedSiteBuilder()
    for site in sites:
        builder.add_site(site)
    builder.build(args.target, overwrite=args.overwrite)


if __name__ == "__main__":
    main()
