#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.esjzone.parser
---------------------------------------------

"""

import base64
import logging
import re
from collections import defaultdict
from typing import Any
from urllib.parse import unquote

from lxml import etree, html

from novel_downloader.infra.fontocr import get_font_ocr
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
class EsjzoneParser(BaseParser):
    """
    Parser for esjzone book pages.
    """

    site_name: str = "esjzone"

    _VALID_TITLE_RE = re.compile(r"[^\W_]", re.UNICODE)
    _FONT_FAMILY_RE = re.compile(r"font-family\s*:\s*'([^']+)'")
    _BASE64_RE = re.compile(r"base64,([A-Za-z0-9+/=]+)")

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        """
        Parse a book info page and extract metadata and chapter structure.

        注: 由于网站使用了多种不同的分卷格式, 已经尝试兼容常见情况,
        但仍可能存在未覆盖的 cases

        :param html_list: Raw HTML of the book info page.
        :return: Parsed metadata and chapter structure as a dictionary.
        """
        if not html_list or self._is_forum_page(html_list):
            return None

        tree = html.fromstring(html_list[0])

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

    def parse_chapter(
        self,
        html_list: list[str],
        chapter_id: str,
        **kwargs: Any,
    ) -> ChapterDict | None:
        if not html_list:
            return None
        if self._is_forum_page(html_list):
            logger.warning("esjzone chapter %s :: please login to access", chapter_id)
            return None
        if self._is_encrypted_chapter(html_list[0]):
            logger.warning("esjzone chapter %s :: chapter is encrypted", chapter_id)
            return None

        tree = html.fromstring(html_list[0])
        title = self._first_str(tree.xpath("//h2/text()"))

        # Collect embedded font bytes (for obfuscated glyph decoding)
        font_bytes_map: dict[str, bytes] = {}
        for link in tree.xpath(
            '//div[contains(@class, "forum-content")]//link[@rel="stylesheet"]'
        ):
            style_href = link.get("href")
            if style_href:
                font_name, font_bytes = self._extract_font_info(style_href)
                if font_name and font_bytes:
                    font_bytes_map[font_name] = font_bytes

        font_mappings: dict[str, dict[str, str]] = {}

        # Walk the forum content and produce plain text lines + image map
        all_lines: list[str] = []
        image_positions: dict[int, list[str]] = {}
        for root in tree.xpath('//div[contains(@class, "forum-content")]'):
            lines, img_map = self._collect_lines_and_images(
                root,
                font_bytes_map=font_bytes_map,
                font_mappings=font_mappings,
            )

            # Merge image maps, re-indexing by current length prior to this root
            if img_map:
                base = len(all_lines)
                for k, urls in img_map.items():
                    image_positions.setdefault(k + base, []).extend(urls)

            all_lines.extend(lines)

        if not (all_lines or image_positions):
            return None

        content = "\n".join(all_lines)
        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {
                "site": self.site_name,
                "image_positions": image_positions,
            },
        }

    def _collect_lines_and_images(
        self,
        node: etree._Element,
        *,
        font_bytes_map: dict[str, bytes],
        font_mappings: dict[str, dict[str, str]],
    ) -> tuple[list[str], dict[int, list[str]]]:
        lines: list[str] = []
        image_positions: dict[int, list[str]] = defaultdict(list)
        buf: list[str] = []

        def apply_map(s: str, active_map: dict[str, str] | None) -> str:
            if not active_map:
                return s
            return "".join(active_map.get(ch, ch) for ch in s)

        def flush_line() -> None:
            text = "".join(buf).strip()
            if text:
                lines.append(text)
            buf.clear()

        def add_img(src: str) -> None:
            if buf:
                flush_line()
            # 1-based: images after paragraph N -> key N
            idx = len(lines)
            image_positions[idx].append(src)

        def build_section_map(section: etree._Element) -> dict[str, str] | None:
            style_attr = section.get("style", "")
            fam = self._FONT_FAMILY_RE.search(style_attr)
            if not fam:
                return None
            font_name = fam.group(1)
            if not self._decode_font:
                return font_mappings.get(font_name)
            if font_name not in font_bytes_map:
                return font_mappings.get(font_name)

            raw_text = section.xpath("string(.)")
            char_set = set(raw_text) - {" ", "\n", "\u3000"}
            mapping = self._build_font_mapping(
                font_bytes_map[font_name],
                char_set,
                mapped=font_mappings.get(font_name, {}),
            )
            if mapping:
                font_mappings[font_name] = mapping
            return mapping or None

        BLOCK_TAGS = {"p"}

        def walk(n: etree._Element, active_map: dict[str, str] | None) -> None:
            tag = n.tag.lower() if isinstance(n.tag, str) else ""

            # Skip non-content
            if tag in {"script", "style", "link", "meta"}:
                return

            if tag == "section":
                local_map = build_section_map(n) or active_map
                # text before first child
                if n.text and n.text.strip():
                    buf.append(apply_map(n.text, local_map))
                for child in n:
                    walk(child, local_map)
                    if child.tail and child.tail.strip():
                        buf.append(apply_map(child.tail, local_map))
                return

            if tag in BLOCK_TAGS:
                if n.text and n.text.strip():
                    buf.append(apply_map(n.text, active_map))
                for child in n:
                    walk(child, active_map)
                    if child.tail and child.tail.strip():
                        buf.append(apply_map(child.tail, active_map))
                flush_line()
                return

            if tag == "br":
                flush_line()
                return

            if tag == "img":
                src = n.get("src", "") or ""
                if src:
                    add_img(src)
                return

            if n.text and n.text.strip():
                buf.append(apply_map(n.text, active_map))
            for child in n:
                walk(child, active_map)
                if child.tail and child.tail.strip():
                    buf.append(apply_map(child.tail, active_map))

        walk(node, active_map=None)
        flush_line()

        # Convert defaultdict to plain dict
        return lines, dict(image_positions)

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
    def _extract_font_info(cls, style_href: str) -> tuple[str, bytes]:
        """
        Extract font family name and raw font bytes from a CSS data URI.

        :param style_href: href attribute value from <link rel="stylesheet">.
        :return: (font_name, font_bytes) or ("", b"") if not found.
        """
        if not style_href.startswith("data:text/css"):
            return "", b""

        try:
            css_text = unquote(style_href.split(",", 1)[1])

            font_name_match = cls._FONT_FAMILY_RE.search(css_text)
            if not font_name_match:
                return "", b""
            font_name = font_name_match.group(1)

            font_data_match = cls._BASE64_RE.search(css_text)
            if not font_data_match:
                return font_name, b""

            font_bytes = base64.b64decode(font_data_match.group(1))
            return font_name, font_bytes
        except Exception as e:
            logger.warning("esjzone: Failed to extract font info: %s", e)
            return "", b""

    def _build_font_mapping(
        self,
        font_bytes: bytes,
        char_set: set[str],
        mapped: dict[str, str] | None = None,
    ) -> dict[str, str]:
        """
        Build a mapping from obfuscated glyphs to real characters.

        :param font_bytes: Raw TTF/OTF/WOFF2 font bytes.
        :param char_set: Subset of characters actually present in the text.
        :param mapped: Optional partial mapping cache (already-known mappings).
        :return: Mapping dict (obfuscated_char -> real_char).
        """
        if not font_bytes or not char_set:
            return mapped or {}

        ocr = get_font_ocr(self._fontocr_cfg)
        if ocr is None:
            return mapped or {}

        mapping = dict(mapped or {})

        try:
            remaining = char_set - mapping.keys()
            if not remaining:
                return mapping
            font_chars = ocr.extract_font_charset_bytes(font_bytes)
            font = ocr.load_render_font_bytes(font_bytes)
            remaining &= font_chars
            if not remaining:
                return mapping

            rendered = [(ch, ocr.render_char_image_array(ch, font)) for ch in remaining]

            imgs_to_query = [img for _, img in rendered]
            fused = ocr.predict(imgs_to_query, batch_size=self._batch_size)
            for (ch, _), preds in zip(rendered, fused, strict=False):
                if not preds:
                    continue
                real_char, _ = preds
                mapping[ch] = real_char

            return mapping
        except Exception as e:
            logger.warning("esjzone: Failed to build font mapping: %s", e)
            return {}
