#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.esjzone.parser
---------------------------------------------

"""

import logging
import re
from typing import Any
from urllib.parse import unquote

from lxml import etree, html

from novel_downloader.plugins.base.parser import BaseParser
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import (
    BookInfoDict,
    ChapterDict,
    ChapterInfoDict,
    MediaResource,
    VolumeInfoDict,
)

logger = logging.getLogger(__name__)


@registrar.register_parser()
class EsjzoneParser(BaseParser):
    """
    Parser for esjzone book pages.
    """

    site_name: str = "esjzone"

    _VALID_TITLE_RE = re.compile(r"[^\W_]", re.UNICODE)
    _FONT_FAMILY_RE = re.compile(r"font-family\s*:\s*'([^']+)'")
    _BASE64_RE = re.compile(r"base64,([A-Za-z0-9+/=]+)")
    _DATA_URL_RE = re.compile(r"^data:(?P<mime>[^;]+);base64,(?P<data>.+)$")

    def parse_book_info(
        self,
        raw_pages: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        """
        Parse a book info page and extract metadata and chapter structure.

        注: 由于网站使用了多种不同的分卷格式, 已经尝试兼容常见情况,
        但仍可能存在未覆盖的 cases

        :param raw_pages: Raw HTML of the book info page.
        :return: Parsed metadata and chapter structure as a dictionary.
        """
        if not raw_pages or self._is_forum_page(raw_pages):
            return None

        tree = html.fromstring(raw_pages[0])

        # --- Basic metadata ---
        book_name = self._first_str(
            tree.xpath('//h2[contains(@class,"text-normal")]/text()')
        )
        author = self._first_str(tree.xpath('//li[strong[text()="作者:"]]/a/text()'))
        cover_url = self._first_str(
            tree.xpath('//div[contains(@class,"product-gallery")]//img/@src')
        )
        update_time = self._first_str(
            tree.xpath('//li[strong[text()="更新日期:"]]/text()')
        )  # noqa: E501
        word_count = self._first_str(
            tree.xpath('//span[@id="txt"]/text()'), replaces=[(",", "")]
        )
        book_type = self._first_str(tree.xpath('//li[strong[text()="類型:"]]/text()'))

        # Summary paragraphs
        paras = tree.xpath('//div[@class="description"]/p')
        texts = [p.xpath("string()").strip() for p in paras]
        summary = "\n".join(t for t in texts if t)

        # --- Chapter volumes & listings ---
        volumes: list[VolumeInfoDict] = []
        vol_idx: int = 1
        vol_name: str | None = None
        vol_desc: list[str] = []
        vol_chaps: list[ChapterInfoDict] = []

        def flush_volume() -> None:
            nonlocal vol_idx, vol_name, vol_chaps, vol_desc
            if not vol_chaps:
                return

            # Try to infer volume name from description if not set
            vol_name = vol_name or next(
                (line for line in vol_desc if self._is_valid_title(line)), None
            )

            volumes.append(
                {
                    "volume_name": vol_name or f"未命名卷 {vol_idx}",
                    "volume_intro": "\n".join(vol_desc).strip(),
                    "chapters": vol_chaps,
                }
            )

            vol_name = None
            vol_chaps = []
            vol_desc = []
            vol_idx += 1

        def _chapter_from_a(a: etree._Element) -> ChapterInfoDict | None:
            href = a.get("href", "") or ""
            if not href:
                return None
            title = a.get("data-title") or ""
            title = self._norm_space(title) if title else ""
            if not title:
                title = self._norm_space(a.xpath("string(.//p)")) or self._norm_space(
                    a.xpath("string(.)")
                )
            if not title:
                return None
            # "https://www.esjzone.cc/forum/12345/543.html" -> "543"
            cid = (
                href.split("/")[-1].split(".", 1)[0] if "www.esjzone.cc" in href else ""
            )
            return {"title": title, "url": href, "chapterId": cid}

        def walk(node: etree._Element) -> None:
            nonlocal vol_name, vol_desc, vol_chaps

            tag = node.tag.lower() if isinstance(node.tag, str) else ""
            if tag in {"script", "style", "link", "meta"}:
                return

            if tag == "details":
                flush_volume()

                # Volume name from <summary>
                name_text = self._norm_space(node.xpath("string(./summary)"))
                if name_text:
                    vol_name = name_text

                # Chapters inside details
                for a in node.xpath(".//a"):
                    chap = _chapter_from_a(a)
                    if chap:
                        vol_chaps.append(chap)

                flush_volume()
                return

            if tag == "a":
                chap = _chapter_from_a(node)
                if chap:
                    vol_chaps.append(chap)
                return

            if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
                if not node.xpath(".//details"):
                    name_text = self._norm_space(node.xpath("string(.)"))
                    if name_text:
                        if vol_chaps:
                            flush_volume()
                        vol_name = name_text

            elif tag == "summary":
                name_text = self._norm_space(node.xpath("string(.)"))
                if name_text:
                    if vol_chaps:
                        flush_volume()
                    vol_name = name_text

            elif tag == "p":
                if node.xpath("ancestor::a[1]"):
                    return
                text = self._norm_space(node.xpath("string(.)"))
                if not text:
                    return
                if vol_chaps:
                    flush_volume()
                vol_desc.append(text)

            # Recurse
            for child in node:
                walk(child)

        # Walk the chapter list container recursively
        chap_roots = tree.xpath('//div[@id="chapterList"]')
        if chap_roots:
            walk(chap_roots[0])
        flush_volume()

        if not volumes:
            return None

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "word_count": word_count,
            "update_time": update_time,
            "summary": summary,
            "tags": [book_type] if book_type else [],
            "volumes": volumes,
            "extra": {},
        }

    def parse_chapter_content(
        self,
        raw_pages: list[str],
        chapter_id: str,
        **kwargs: Any,
    ) -> ChapterDict | None:
        if not raw_pages:
            return None
        if self._is_forum_page(raw_pages):
            logger.warning("esjzone chapter %s :: please login to access", chapter_id)
            return None
        if self._is_encrypted_chapter(raw_pages[0]):
            logger.warning("esjzone chapter %s :: chapter is encrypted", chapter_id)
            return None

        tree = html.fromstring(raw_pages[0])
        title = self._first_str(tree.xpath("//h2/text()"))

        # Collect embedded font base64 data
        font_base64_map: dict[str, str] = {}
        for link in tree.xpath(
            '//div[contains(@class, "forum-content")]//link[@rel="stylesheet"]'
        ):
            style_href = link.get("href")
            if style_href:
                font_name, font_b64 = self._extract_font_info(style_href)
                if font_name and font_b64:
                    font_base64_map[font_name] = font_b64

        paragraphs: list[str] = []
        resources: list[MediaResource] = []

        buf: list[str] = []  # current paragraph buffer
        current_paragraph_no: int = 0
        current_paragraph_fonts: set[str] = set()

        open_font_spans: dict[str, dict[str, int]] = {}

        def add_font_resource(font_name: str, start: int, end: int) -> None:
            if start <= 0 or end < start:
                return
            b64 = font_base64_map.get(font_name)
            if not b64:
                return

            resources.append(
                {
                    "type": "font",
                    "range": {"start": start, "end": end},
                    "base64": b64,
                    "mime": "font/woff2",
                }
            )

        def flush_paragraph() -> None:
            nonlocal current_paragraph_no

            text = "".join(buf).strip()
            if not text:
                buf.clear()
                current_paragraph_fonts.clear()
                return

            paragraphs.append(text)
            current_paragraph_no += 1
            paragraph_no = current_paragraph_no

            paragraph_fonts = set(current_paragraph_fonts)

            for font_name in list(open_font_spans.keys()):
                if font_name not in paragraph_fonts:
                    span = open_font_spans.pop(font_name)
                    start = span["start"]
                    end = span.get("end", start)
                    if end < start:
                        end = start
                    add_font_resource(font_name, start, end)

            for font_name in paragraph_fonts:
                if font_name in open_font_spans:
                    open_font_spans[font_name]["end"] = paragraph_no
                else:
                    open_font_spans[font_name] = {
                        "start": paragraph_no,
                        "end": paragraph_no,
                    }

            buf.clear()
            current_paragraph_fonts.clear()

        def add_text_segment(raw: str, active_font: str | None) -> None:
            if not raw or not raw.strip():
                return
            buf.append(raw)
            if active_font and active_font in font_base64_map:
                current_paragraph_fonts.add(active_font)

        def add_img_node(img_el: etree._Element) -> None:
            nonlocal current_paragraph_no

            src = img_el.get("src", "") or ""
            if not src:
                return

            if buf:
                flush_paragraph()

            paragraph_index = current_paragraph_no

            if src.startswith("//"):
                src = "https:" + src

            res: MediaResource = {
                "type": "image",
                "paragraph_index": paragraph_index,
            }

            m = self._DATA_URL_RE.match(src)
            if m:
                res["mime"] = m.group("mime")
                res["base64"] = m.group("data")
            else:
                res["url"] = src

            alt = img_el.get("alt")
            if alt:
                res["alt"] = alt.strip()

            resources.append(res)

        def get_section_font(
            section: etree._Element, inherited_font: str | None
        ) -> str | None:
            style_attr = section.get("style", "")
            fam = self._FONT_FAMILY_RE.search(style_attr)
            if not fam:
                return inherited_font
            return fam.group(1)

        BLOCK_TAGS = {"p"}

        def walk(n: etree._Element, active_font: str | None) -> None:
            tag = n.tag.lower() if isinstance(n.tag, str) else ""

            if tag in {"script", "style", "link", "meta"}:
                return

            # SECTION = font change context
            if tag == "section":
                local_font = get_section_font(n, active_font)

                if n.text and n.text.strip():
                    add_text_segment(n.text, local_font)

                for child in n:
                    walk(child, local_font)
                    if child.tail and child.tail.strip():
                        add_text_segment(child.tail, local_font)
                return

            # Paragraph-like block
            if tag in BLOCK_TAGS:
                if n.text and n.text.strip():
                    add_text_segment(n.text, active_font)
                for child in n:
                    walk(child, active_font)
                    if child.tail and child.tail.strip():
                        add_text_segment(child.tail, active_font)
                flush_paragraph()
                return

            # Line break
            if tag == "br":
                flush_paragraph()
                return

            # Images
            if tag == "img":
                add_img_node(n)
                return

            # Generic inline
            if n.text and n.text.strip():
                add_text_segment(n.text, active_font)

            for child in n:
                walk(child, active_font)
                if child.tail and child.tail.strip():
                    add_text_segment(child.tail, active_font)

        for root in tree.xpath('//div[contains(@class, "forum-content")]'):
            walk(root, active_font=None)

        flush_paragraph()

        # Close all remaining font spans
        for font_name, span in list(open_font_spans.items()):
            start = span["start"]
            end = span.get("end", current_paragraph_no)
            add_font_resource(font_name, start, end)

        if not (paragraphs or resources):
            return None
        content = "\n".join(paragraphs)

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {
                "site": self.site_name,
                "resources": resources,
            },
        }

    def _is_forum_page(self, html_str: list[str]) -> bool:
        if not html_str:
            return False

        tree = html.fromstring(html_str[0])
        page_title = self._first_str(
            tree.xpath('//div[@class="page-title"]//h1/text()')
        )
        if page_title != "論壇":
            return False

        breadcrumb = [
            s.strip()
            for s in tree.xpath(
                '//div[@class="page-title"]//ul[@class="breadcrumbs"]/li//text()'
            )
            if s.strip()
        ]
        return breadcrumb == ["Home", "/", "論壇"]

    @classmethod
    def _is_valid_title(cls, title: str) -> bool:
        """
        Check if the title contains at least one valid character.

        :param title: The title string to validate.
        :return: True if valid, False otherwise.
        """
        return bool(cls._VALID_TITLE_RE.search(title))

    @staticmethod
    def _is_encrypted_chapter(html_str: str) -> bool:
        """
        Check whether the given HTML string corresponds to an encrypted chapter.

        :param html_str: Raw HTML content as a string.
        :return: True if both markers are found, otherwise False.
        """
        return "/assets/img/oops_art.jpg" in html_str and "btn-send-pw" in html_str

    @classmethod
    def _extract_font_info(cls, style_href: str) -> tuple[str, str]:
        """
        Extract font family name and base64 string from CSS data URI.

        :param style_href: href attribute value from <link rel="stylesheet">.
        :return: (font_name, font_bytes) or ("", "") if not found.
        """
        if not style_href.startswith("data:text/css"):
            return "", ""

        try:
            parts = style_href.split(",", 1)
            if len(parts) < 2:
                return "", ""
            css_text = unquote(parts[1])

            font_name_match = cls._FONT_FAMILY_RE.search(css_text)
            if not font_name_match:
                return "", ""
            font_name = font_name_match.group(1)

            font_data_match = cls._BASE64_RE.search(css_text)
            if not font_data_match:
                return font_name, ""

            return font_name, font_data_match.group(1)
        except Exception as e:
            logger.warning("esjzone: Failed to extract font info: %s", e)
            return "", ""
