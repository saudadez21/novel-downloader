#!/usr/bin/env python3
"""
novel_downloader.core.parsers.eightnovel
----------------------------------------

"""

import re
from typing import Any

from lxml import html

from novel_downloader.core.parsers.base import BaseParser
from novel_downloader.core.parsers.registry import register_parser
from novel_downloader.models import (
    BookInfoDict,
    ChapterDict,
    ChapterInfoDict,
    VolumeInfoDict,
)


@register_parser(
    site_keys=["eightnovel", "8novel"],
)
class EightnovelParser(BaseParser):
    """
    Parser for 无限轻小说 book pages.
    """

    BASE_URL = "https://www.8novel.com"
    _SPLIT_STR_PATTERN = re.compile(
        r'["\']([^"\']+)["\']\s*\.split\s*\(\s*["\']\s*,\s*["\']\s*\)', re.DOTALL
    )
    _RE_AUTHOR = re.compile(r"作者[:：]?\s*")
    _RE_UPDATE = re.compile(r"更新[:：]?\s*")

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if not html_list:
            return None

        tree = html.fromstring(html_list[0])

        # --- Basic metadata ---
        book_name = self._first_str(tree.xpath("//li[contains(@class,'h2')]/text()"))

        author_raw = self._first_str(
            tree.xpath("//span[contains(@class,'item-info-author')]/text()")
        )
        author = self._RE_AUTHOR.sub("", author_raw)

        cover_url = self.BASE_URL + self._first_str(
            tree.xpath("//div[contains(@class,'item-cover')]//img/@src")
        )

        update_raw = self._first_str(
            tree.xpath("//span[contains(@class,'item-info-date')]/text()")
        )
        update_time = self._RE_UPDATE.sub("", update_raw)

        counts = tree.xpath(
            "//li[@class='small text-gray']//span[contains(@class,'item-info-num')]/text()"  # noqa: E501
        )
        word_count = counts[1].strip() + "萬字" if len(counts) >= 2 else ""

        tags = tree.xpath("//meta[@property='og:novel:category']/@content")

        # --- Summary ---
        summary_nodes = tree.xpath(
            "//li[contains(@class,'full_text') and contains(@class,'mt-2')]"
        )
        if summary_nodes:
            texts = [t.strip() for t in summary_nodes[0].itertext()]
            summary = "\n".join(line for line in texts if line)
        else:
            summary = ""

        # --- Chapters / Volumes ---
        volumes: list[VolumeInfoDict] = []
        for vol_div in tree.xpath("//div[contains(@class,'folder') and @pid]"):
            # Volume title
            h3 = vol_div.xpath(".//div[contains(@class,'vol-title')]//h3")
            vol_name = (
                h3[0].text_content().split("/")[0].strip() if h3 else "Unnamed Volume"
            )

            # Chapters
            chapters: list[ChapterInfoDict] = []
            for a in vol_div.xpath(
                ".//a[contains(@class,'episode_li') and contains(@class,'d-block')]"
            ):
                title = (a.text_content() or "").strip()
                href = a.get("href") or ""
                if not href or not title:
                    continue
                url = href if href.startswith("http") else self.BASE_URL + href
                chapter_id = href.split("?")[-1]  # "/read/3355/?270015" -> "270015"
                chapters.append({"title": title, "url": url, "chapterId": chapter_id})

            volumes.append({"volume_name": vol_name, "chapters": chapters})

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "update_time": update_time,
            "word_count": word_count,
            "tags": tags,
            "summary": summary,
            "volumes": volumes,
            "extra": {},
        }

    def parse_chapter(
        self,
        html_list: list[str],
        chapter_id: str,
        **kwargs: Any,
    ) -> ChapterDict | None:
        if len(html_list) < 2:
            return None

        try:
            id_title_map = self._build_id_title_map(html_list[0])
            title = id_title_map.get(chapter_id) or ""
        except Exception:
            title = ""

        wrapper = html.fromstring(f"<div>{html_list[1]}</div>")

        segments: list[str] = []

        self._append_segment(segments, wrapper.text)

        for node in wrapper:
            tag = node.tag.lower() if isinstance(node.tag, str) else ""

            # A picture‑gallery block
            if tag == "div" and "content-pics" in (node.get("class") or ""):
                for img in node.xpath(".//img"):
                    src = img.get("src")
                    full = src if not src.startswith("/") else self.BASE_URL + src
                    segments.append(f'<img src="{full}" />')
                self._append_segment(segments, node.tail)

            # Standalone <img>
            elif tag == "img":
                src = node.get("src")
                if not src:
                    continue
                full = src if not src.startswith("/") else self.BASE_URL + src
                segments.append(f'<img src="{full}" />')
                self._append_segment(segments, node.tail)

            # Line break -> text in .tail is next paragraph
            elif tag == "br":
                self._append_segment(segments, node.tail)

            # Any other element -> get its text content
            else:
                self._append_segment(segments, node.text_content())
                self._append_segment(segments, node.tail)

        # Remove final ad line if present
        if segments and segments[-1] and segments[-1][0] in ("8", "⑧", "⒏"):
            segments.pop()

        content = "\n".join(segments).strip()
        if not content.strip():
            return None

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": "eightnovel"},
        }

    @staticmethod
    def _append_segment(segments: list[str], text: str | None) -> None:
        """
        Strip, filter out the '8novel' ad, and append non-empty text to segments.
        """
        if not text:
            return
        cleaned = text.strip()
        if cleaned:
            segments.append(cleaned)

    @classmethod
    def _build_id_title_map(cls, html_str: str) -> dict[str, str]:
        """
        Extracts two comma-split lists from html_str:
        - A numeric list of IDs (one element longer)
        - A list of titles
        """
        id_list = None
        title_list = None

        for content in cls._SPLIT_STR_PATTERN.findall(html_str):
            items = [s.strip() for s in content.split(",")]
            if items == [""]:
                # skip bids=""
                continue
            if all(item.isdigit() for item in items):
                id_list = items
            else:
                title_list = items

            if id_list and title_list:
                break

        if not id_list or not title_list:
            raise ValueError("Could not locate both ID and title lists")
        if len(id_list) != len(title_list) + 1:
            raise ValueError(
                "ID list must be exactly one element longer than title list"
            )

        return dict(zip(id_list[:-1], title_list, strict=False))
