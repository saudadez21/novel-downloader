#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.kadokado.parser
----------------------------------------------
"""

import json
from typing import Any

from lxml import html
from novel_downloader.plugins.base.parser import BaseParser
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import (
    BookInfoDict,
    ChapterDict,
    ChapterInfoDict,
    VolumeInfoDict,
)


@registrar.register_parser()
class KadokadoParser(BaseParser):
    """
    Parser for KadoKado book pages.
    """

    site_name: str = "kadokado"
    BASE_URL = "https://www.kadokado.com.tw"

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if len(html_list) < 2:
            return None

        info = json.loads(html_list[0])
        catalog = json.loads(html_list[1])

        book_name = info.get("displayName", "")
        author = info.get("ownerDisplayName", "")
        summary = info.get("logline", "") or info.get("oneLineIntro", "")
        tags = info.get("tags", [])
        cover_urls = info.get("coverUrls") or []
        cover_url = cover_urls[0] if cover_urls else ""
        word_count = str(info.get("wordCount", "")) if info.get("wordCount") else ""
        update_time = ""

        volumes: list[VolumeInfoDict] = []

        for idx, vol in enumerate(catalog, start=1):
            vol_name = vol.get("collectionDisplayName") or f"未命名卷 {idx}"
            chapters_data = vol.get("chapters") or []
            vol_chaps: list[ChapterInfoDict] = []

            for ch in chapters_data:
                chap_id = str(ch.get("chapterId", ""))
                title = ch.get("chapterDisplayName", "").strip()
                accessible = bool(ch.get("isFree") or ch.get("isPurchased"))

                vol_chaps.append(
                    {
                        "title": title,
                        "url": f"{self.BASE_URL}/chapter/{chap_id}",
                        "chapterId": chap_id,
                        "accessible": accessible,
                    }
                )

            volumes.append(
                {
                    "volume_name": vol_name,
                    "chapters": vol_chaps,
                }
            )

        if not volumes:
            return None

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "update_time": update_time,
            "word_count": word_count,
            "summary": summary,
            "tags": tags,
            "volumes": volumes,
            "extra": {},
        }

    def parse_chapter(
        self,
        html_list: list[str],
        chapter_id: str,
        **kwargs: Any,
    ) -> ChapterDict | None:
        if not html_list:
            return None

        info = json.loads(html_list[0])
        content_resp = json.loads(html_list[1])
        raw_content = content_resp.get("content")
        if not raw_content:
            return None

        tree = html.fromstring(raw_content)

        title = info.get("chapterDisplayName") or ""

        paragraphs: list[str] = []
        image_positions: dict[int, list[dict[str, Any]]] = {}
        image_idx = 0

        for elem in tree.iter():
            tag = str(elem.tag).lower() if elem.tag is not None else ""
            if tag == "p":
                text = elem.text_content().strip()
                if text:
                    paragraphs.append(text)
                    image_idx += 1
            elif tag == "img":
                src = elem.get("src")
                if src:
                    if src.startswith("//"):
                        src = "https:" + src
                    image_positions.setdefault(image_idx, []).append(
                        {
                            "type": "url",
                            "data": src,
                        }
                    )

        # After content
        extra_imgs = content_resp.get("imageUrls") or []
        for url in extra_imgs:
            if isinstance(url, str) and url.strip():
                image_positions.setdefault(image_idx, []).append(
                    {
                        "type": "url",
                        "data": url.strip(),
                    }
                )

        if not (paragraphs or image_positions):
            return None

        content = "\n".join(paragraphs)

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {
                "site": self.site_name,
                "image_positions": image_positions,
            },
        }
