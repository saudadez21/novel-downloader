#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.novelpia.parser
----------------------------------------------
"""

import json
import re
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
class NovelpiaParser(BaseParser):
    """
    Parser for ノベルピア book pages.
    """

    site_name: str = "novelpia"

    IMG_SRC_PATTERN = re.compile(r'src="([^"]+)"')

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if len(html_list) < 2:
            return None

        info = json.loads(html_list[0])
        novel = info.get("novel", {})
        if not novel:
            return None

        # --- base info ---
        book_name = novel.get("novel_name", "").strip()
        author = novel.get("writer_nick", "").strip()
        cover_url = novel.get("cover_img") or novel.get("novel_img_all", "")
        if cover_url and cover_url.startswith("//"):
            cover_url = "https:" + cover_url

        update_time = novel.get("last_write_date") or novel.get("status_date", "")
        tags = novel.get("novel_genre_arr", [])

        summary = novel.get("novel_story", "") or ""
        summary = summary.replace("\r", "").replace("\n", "")
        summary = summary.replace("<br />", "\n").replace("<br>", "\n")

        # --- Chapter volumes & listings ---
        chapters: list[ChapterInfoDict] = []
        for curr_html in html_list[1:]:
            t = html.fromstring(curr_html)
            rows = t.xpath("//tr[contains(@class,'ep_style5')]")
            for r in rows:
                chapter_id = r.xpath(
                    ".//td[contains(@class,'font12')]/@data-content-no"
                )
                if not chapter_id:
                    continue
                cid = chapter_id[0].strip()

                b_elem = r.xpath(".//td[contains(@class,'font12')]//b")[0]
                title = "".join(b_elem.itertext()).strip()
                title = title.replace("無料", "").strip()

                url = f"https://novelpia.jp/viewer/{cid}"
                chapters.append(
                    {
                        "chapterId": cid,
                        "title": title,
                        "url": url,
                    }
                )

        if not chapters:
            return None

        volumes: list[VolumeInfoDict] = [{"volume_name": "正文", "chapters": chapters}]

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "update_time": update_time,
            "tags": tags,
            "summary": summary,
            "volumes": volumes,
            "extra": {"novel_id": novel.get("novel_no")},
        }

    def parse_chapter(
        self,
        html_list: list[str],
        chapter_id: str,
        **kwargs: Any,
    ) -> ChapterDict | None:
        if not html_list:
            return None

        data = json.loads(html_list[0])
        s: list[dict[str, str]] = data.get("s", [])
        if not s:
            return None

        html_fragments: list[str] = []
        for p in s:
            text = (p.get("text") or "").strip()
            if not text or "<div class='cover-wrapper'>" in text:
                continue
            html_fragments.append(f"<p>{text}</p>")

        html_doc = "<root>" + "".join(html_fragments) + "</root>"
        doc = html.fromstring(html_doc)

        paragraphs: list[str] = []
        image_positions: dict[int, list[dict[str, Any]]] = {}
        image_idx = 0

        for p_elem in doc.xpath(".//p"):
            # ---- collect images ----
            for src in p_elem.xpath(".//img/@src"):
                src = src.strip()
                if not src:
                    continue
                if src.startswith("//"):
                    src = "https:" + src
                image_positions.setdefault(image_idx, []).append(
                    {
                        "type": "url",
                        "data": src,
                    }
                )

            for ruby in p_elem.xpath(".//ruby"):
                base = "".join(ruby.xpath(".//text()[not(parent::rt)]")).strip()
                rt_text = "".join(ruby.xpath(".//rt/text()")).strip()
                tail = ruby.tail or ""
                replacement_text = (
                    f"{base}({rt_text}){tail}" if rt_text else f"{base}{tail}"
                )

                parent = ruby.getparent()
                if parent is not None:
                    pos = parent.index(ruby)
                    parent.remove(ruby)
                    if pos == 0:
                        parent.text = (parent.text or "") + replacement_text
                    else:
                        prev = parent[pos - 1]
                        prev.tail = (prev.tail or "") + replacement_text

            text_content = p_elem.text_content().strip()
            if text_content:
                paragraphs.append(text_content)
                image_idx += 1

        if not (paragraphs or image_positions):
            return None

        content = "\n".join(paragraphs)

        return {
            "id": chapter_id,
            "title": "",
            "content": content,
            "extra": {
                "site": self.site_name,
                "image_positions": image_positions,
            },
        }
