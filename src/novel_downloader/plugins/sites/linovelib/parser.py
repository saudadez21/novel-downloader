#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.linovelib.parser
-----------------------------------------------

"""

import json
import logging
import re
from typing import Any

from lxml import html

from novel_downloader.infra.paths import LINOVELIB_MAP_PATH
from novel_downloader.plugins.base.parser import BaseParser
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import (
    BookInfoDict,
    ChapterDict,
    ChapterInfoDict,
    VolumeInfoDict,
)

logger = logging.getLogger(__name__)


@registrar.register_parser()
class LinovelibParser(BaseParser):
    """
    Parser for 哔哩轻小说 book pages.
    """

    site_name: str = "linovelib"

    _PCTHEMA_MAP: dict[str, str] = {}

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if not html_list:
            return None

        tree = html.fromstring(html_list[0])

        book_name = (
            self._first_str(
                tree.xpath("//meta[@property='og:novel:book_name']/@content")
            )
            or self._first_str(tree.xpath("//meta[@property='og:title']/@content"))
            or self._first_str(tree.xpath("//h1[contains(@class,'book-name')]/text()"))
        )
        author = (
            self._first_str(tree.xpath("//meta[@property='og:novel:author']/@content"))
            or self._first_str(tree.xpath("//meta[@name='author']/@content"))
            or self._first_str(
                tree.xpath(
                    "//div[contains(@class,'book-author')]"
                    "//div[contains(@class,'au-name')]//a[1]/text()"
                )
            )
        )
        cover_url = (
            self._first_str(tree.xpath("//meta[@property='og:image']/@content"))
            or self._first_str(tree.xpath("//meta[@name='pic']/@content"))
            or self._first_str(
                tree.xpath("//div[contains(@class,'book-img')]//img/@src")
            )
        )
        serial_status = self._first_str(
            tree.xpath("//meta[@property='og:novel:status']/@content")
        ) or self._first_str(
            tree.xpath(
                "//div[contains(@class,'book-label')]//a[contains(@class,'state')]/text()"
            )
        )

        summary = self._first_str(
            tree.xpath("//meta[@property='og:description']/@content")
        )
        if not summary:
            summary = self._join_strs(
                tree.xpath("//div[contains(@class,'book-dec')]//p//text()")
            )

        word_count = self._first_str(
            tree.xpath(
                "//div[contains(@class,'nums')]/span[contains(., '字数')]/text()"
            ),  # noqa: E501
            replaces=[("字数：", "")],
        )
        update_time = (
            self._first_str(
                tree.xpath("//meta[@property='og:novel:update_time']/@content")
            )
            or self._first_str(tree.xpath("//meta[@name='update']/@content"))
            or self._first_str(
                tree.xpath(
                    "//div[contains(@class,'nums')]/span[contains(., '最后更新')]/text()"  # noqa: E501
                ),
                replaces=[("最后更新：", "")],
            )
        )

        # --- volume pages ---
        vol_pages = html_list[1:]
        volumes: list[VolumeInfoDict] = []
        for vol_page in vol_pages:
            vol_tree = html.fromstring(vol_page)

            vol_full_title = self._first_str(
                vol_tree.xpath("//meta[@property='og:title']/@content")
            ) or self._first_str(
                vol_tree.xpath("//h1[contains(@class,'book-name')]/text()")
            )
            # Remove leading book name if present
            volume_name = vol_full_title
            if book_name and volume_name.startswith(book_name):
                volume_name = volume_name[len(book_name) :].lstrip(" ：:·-—")

            volume_cover = self._first_str(
                vol_tree.xpath("//meta[@property='og:image']/@content")
            ) or self._first_str(
                vol_tree.xpath("//div[contains(@class,'book-img')]//img/@src")
            )

            vol_update_time = self._first_str(
                vol_tree.xpath("//meta[@property='og:novel:update_time']/@content")
            ) or self._first_str(
                vol_tree.xpath(
                    "//div[contains(@class,'nums')]/span[contains(., '最后更新')]/text()"  # noqa: E501
                ),
                replaces=[("最后更新：", "")],
            )
            vol_word_count = self._first_str(
                vol_tree.xpath(
                    "//div[contains(@class,'nums')]/span[contains(., '字数')]/text()"
                ),
                replaces=[("字数：", "")],
            )

            volume_intro = self._join_strs(
                vol_tree.xpath("//div[contains(@class,'book-dec')]//p//text()")
            )

            chapters: list[ChapterInfoDict] = [
                {
                    "title": (a.text or "").strip(),
                    "url": (a.get("href") or "").strip(),
                    # '/novel/4668/276082.html' -> '276082'
                    "chapterId": (a.get("href") or "")
                    .rsplit("/", 1)[-1]
                    .split(".", 1)[0],
                }
                for a in vol_tree.xpath("//div[contains(@class,'book-new-chapter')]//a")
            ]

            volumes.append(
                {
                    "volume_name": volume_name,
                    "volume_cover": volume_cover,
                    "update_time": vol_update_time,
                    "word_count": vol_word_count,
                    "volume_intro": volume_intro,
                    "chapters": chapters,
                }
            )

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "serial_status": serial_status,
            "word_count": word_count,
            "summary": summary,
            "update_time": update_time,
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

        try:
            cid_int = int(chapter_id)
        except (TypeError, ValueError):
            cid_int = 0

        title: str = ""
        paragraphs: list[str] = []
        image_positions: dict[int, list[str]] = {}
        image_idx = 0

        for curr_html in html_list:
            tree = html.fromstring(curr_html)

            if not title:
                title = self._first_str(
                    tree.xpath("//div[@id='mlfy_main_text']/h1/text()")
                )

            tcs = tree.xpath("//div[@id='TextContent']")
            if not tcs:
                continue
            tc = tcs[0]

            use_substitution = self._has_subst(curr_html)
            use_shuffle = self._has_shuffle(curr_html)

            p_texts: list[str] = []
            page_lines: list[str] = []

            for node in tc.xpath("./p | ./img"):
                tag = node.tag.lower()

                if tag == "p":
                    txt = "".join(node.xpath(".//text()"))
                    if self._SPACE_RE.sub("", txt) == "":
                        continue

                    if use_substitution:
                        txt = self._map_subst(txt)

                    txt = self._norm_space(txt)

                    p_texts.append(txt)
                    image_idx += 1

                elif tag == "img":
                    src = node.get("data-src") or node.get("src", "")
                    if not src:
                        continue
                    image_positions.setdefault(image_idx, []).append(src)

            if not p_texts and not page_lines:
                continue

            if use_shuffle and p_texts:
                order = self._chapterlog_order(len(p_texts), cid_int)
                reordered_p = [""] * len(p_texts)
                for i, p in enumerate(p_texts):
                    reordered_p[order[i]] = p
            else:
                reordered_p = p_texts

            page_content = "\n".join(p for p in reordered_p if p.strip())
            if page_content:
                paragraphs.append(page_content)

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

    @staticmethod
    def _has_shuffle(html_str: str) -> bool:
        """
        Determine whether the HTML likely applies paragraph shuffling.
        """
        return LinovelibParser._check_script(
            html_str,
            "/scripts/chapterlog.js",
            "v1006b8-5",
            "chapter shuffling",
        )

    @staticmethod
    def _has_subst(html_str: str) -> bool:
        """
        Determine whether the HTML likely applies PC theme character substitution
        """
        if "yuedu()" not in html_str:
            return False
        return LinovelibParser._check_script(
            html_str,
            "/themes/zhpc/js/pctheme.js",
            "v0917",
            "character substitution",
        )

    @classmethod
    def _map_subst(cls, text: str) -> str:
        """
        Apply PC theme character substitution to the input text.
        """
        if not cls._PCTHEMA_MAP:
            cls._PCTHEMA_MAP = json.loads(
                LINOVELIB_MAP_PATH.read_text(encoding="utf-8")
            )

        return "".join(cls._PCTHEMA_MAP.get(c, c) for c in text)

    @staticmethod
    def _chapterlog_order(n: int, cid: int) -> list[int]:
        """
        Compute the paragraph reordering index sequence used by /scripts/chapterlog.js.

        :param n: Total number of non-empty paragraphs in the chapter.
        :param cid: Chapter ID (used as the seed for the shuffle).
        """
        if n <= 0:
            return []
        if n <= 20:
            return list(range(n))

        fixed = list(range(20))
        rest = list(range(20, n))

        # Seeded Fisher-Yates
        m = 233_280
        a = 9_302
        c = 49_397
        s = cid * 127 + 235  # seed
        for i in range(len(rest) - 1, 0, -1):
            s = (s * a + c) % m
            # floor((s / m) * (i + 1)) == (s * (i + 1)) // m
            j = (s * (i + 1)) // m
            rest[i], rest[j] = rest[j], rest[i]

        return fixed + rest

    @staticmethod
    def _check_script(
        html_str: str, script_path: str, expected_version: str, issue_type: str
    ) -> bool:
        """
        Generic helper for detecting site scripts and checking version consistency.
        """
        if script_path not in html_str:
            return False

        matches = re.findall(rf"{re.escape(script_path)}\?([a-zA-Z0-9._-]+)", html_str)

        if not matches:
            logger.warning(
                "linovelib script check: no version found for %s", script_path
            )
            return True

        found_version = matches[0]
        if found_version != expected_version:
            logger.warning(
                "linovelib script check: Detected %s version mismatch. "
                "This may cause the content to be incorrect. "
                "Please report this issue so the handler can be updated.\n"
                "Script: %s\nFound version: %s\nExpected version: %s",
                issue_type,
                script_path,
                found_version,
                expected_version,
            )

        return True
