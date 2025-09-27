#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.xiguashuwu.parser
------------------------------------------------

"""

import base64
import hashlib
import json
import logging
import re
import urllib.parse
from typing import Any

import requests
from lxml import html

from novel_downloader.infra.fontocr import get_font_ocr
from novel_downloader.infra.http_defaults import DEFAULT_USER_HEADERS
from novel_downloader.infra.paths import XIGUASHUWU_MAP_PATH
from novel_downloader.libs.crypto.aes_util import aes_cbc_decrypt
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
class XiguashuwuParser(BaseParser):
    """
    Parser for 西瓜书屋 book pages.
    """

    site_name: str = "xiguashuwu"
    BASE_URL = "https://www.xiguashuwu.com"
    _CONF_THRESHOLD = 0.60
    _FONT_MAP: dict[str, str] = {}
    _GLYPH_CACHE: dict[str, str] = {}

    _CODEURL_PATTERN = re.compile(
        r"""var\s+codeurl\s*=\s*['"]?(\d+)['"]?;?""", re.IGNORECASE
    )

    _NRID_PATTERN = re.compile(
        r"""var\s+nrid\s*=\s*['"]?([A-Za-z0-9]+)['"]?;?""", re.IGNORECASE
    )

    _NEWCON_PATTERN = re.compile(
        r"""let\s+newcon\s*=\s*decodeURIComponent\(\s*['"](.+?)['"]\s*\);?""",
        re.IGNORECASE,
    )

    _D_CALL_PATTERN = re.compile(
        r"""d\(\s*[^,]+,\s*['"]([0-9A-Fa-f]{32})['"]\s*\);?""", re.IGNORECASE
    )

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        """
        Parse a book info page and extract metadata and chapter structure.

        :param html_list: Raw HTML of the book info page.
        :return: Parsed metadata and chapter structure as a dictionary.
        """
        if not html_list:
            return None
        info_tree = html.fromstring(html_list[0])

        book_name = self._first_str(info_tree.xpath('//p[@class="title"]/text()'))

        author = self._first_str(info_tree.xpath('//p[@class="author"]//a/text()'))

        cover_rel = info_tree.xpath(
            '//div[@class="BGsectionOne-top-left"]//img/@_src'
        ) or info_tree.xpath('//div[@class="BGsectionOne-top-left"]//img/@src')
        cover_url = self.BASE_URL + self._first_str(cover_rel)

        tags = [
            self._first_str(info_tree.xpath('//p[@class="category"]/span[1]/a/text()'))
        ]

        update_time = self._first_str(info_tree.xpath('//p[@class="time"]/span/text()'))

        paras = info_tree.xpath('//section[@id="intro"]//p')
        summary = "\n".join(p.xpath("string()").strip() for p in paras).strip()

        chapters: list[ChapterInfoDict] = []
        for catalog_html in html_list[1:]:
            cat_tree = html.fromstring(catalog_html)
            links = cat_tree.xpath(
                '//section[contains(@class,"BCsectionTwo")]'
                '[.//h3[text()="正文"]]//ol//li/a'
            )
            for a in links:
                title = a.xpath("string()").strip()
                href = a.get("href", "").strip()
                # chapterId is filename sans extension
                chapter_id = href.rsplit("/", 1)[-1].split(".", 1)[0]
                chapters.append(
                    ChapterInfoDict(
                        title=title,
                        url=self.BASE_URL + href,
                        chapterId=chapter_id,
                    )
                )

        volumes: list[VolumeInfoDict] = [
            VolumeInfoDict(volume_name="正文", chapters=chapters)
        ]

        return BookInfoDict(
            book_name=book_name,
            author=author,
            cover_url=cover_url,
            update_time=update_time,
            tags=tags,
            summary=summary,
            volumes=volumes,
            extra={},
        )

    def parse_chapter(
        self,
        html_list: list[str],
        chapter_id: str,
        **kwargs: Any,
    ) -> ChapterDict | None:
        """
        Parse chapter pages and extract clean text or simplified HTML.

        :param html_list: Raw HTML of the chapter page.
        :param chapter_id: Identifier of the chapter being parsed.
        :return: Cleaned chapter content as plain text or minimal HTML.
        """
        if not html_list:
            return None

        title_text = ""
        paragraphs: list[str] = []

        for page_idx, html_str in enumerate(html_list, start=1):
            if page_idx == 1:
                tree = html.fromstring(html_str)
                title_text = self._extract_chapter_title(tree)
                paragraphs.extend(self._parse_chapter_page1(tree))
            elif page_idx == 2:
                paragraphs.extend(self._parse_chapter_page2(html_str))
            else:
                paragraphs.extend(self._parse_chapter_page3plus(html_str))

        content = "\n".join(paragraphs).strip()
        if not content:
            return None

        return {
            "id": chapter_id,
            "title": title_text,
            "content": content,
            "extra": {"site": self.site_name},
        }

    @classmethod
    def _parse_chapter_page1(cls, tree: html.HtmlElement) -> list[str]:
        """
        Parse page 1 of the chapter: plain text, no encryption or obfuscation.

        This method extracts all visible text from the element with id="C0NTENT",
        removes known ad sections

        :param tree: Parsed HTML element tree of the chapter page.
        :return: List of text lines in reading order.
        """
        try:
            # note: 'C0NTENT' contains a zero, not the letter 'O'
            content_div = tree.xpath('//*[@id="C0NTENT"]')
            if not content_div:
                return []
            content_div = content_div[0]

            # Remove advertisement or irrelevant sections
            for ad in content_div.xpath('.//div[@class="s_m"]'):
                ad.getparent().remove(ad)

            lines = content_div.xpath(".//text()")
            return [line.strip() for line in lines if line.strip()]
        except Exception as e:
            logger.warning("Failed to parse chapter page 1: %s", e)
            return []

    def _parse_chapter_page2(self, html_str: str) -> list[str]:
        """
        Parse page 2 of the chapter: content order shuffled by JavaScript,
        and text replaced with images.

        :param html_str: Raw HTML string of the chapter page.
        :return: List of text lines extracted in correct reading order.
        """
        try:
            tree = html.fromstring(html_str)
            # Extract ordering metadata
            order_raw = self._parse_client_meta(tree)
            codeurl = self._parse_codeurl(html_str)
            nrid = self._parse_nrid(html_str)
            order_list = self._restore_order(order_raw, codeurl)

            # Extract paragraphs in raw order
            content_divs = tree.xpath(f'//*[@id="{nrid}"]')
            if not content_divs:
                return []
            paragraphs = self._rebuild_paragraphs(content_divs[0])

            # Reorder paragraphs
            reordered: list[str] = []
            for idx in order_list:
                if 0 <= idx < len(paragraphs):
                    reordered.append(paragraphs[idx])
            return reordered
        except Exception as e:
            logger.warning("Failed to parse chapter page 2: %s", e)
            return []

    def _parse_chapter_page3plus(self, html_str: str) -> list[str]:
        """
        Parse pages 3 and beyond of the chapter: AES-encrypted text
        replaced with images.

        :param html_str: Raw HTML string of the chapter page.
        :return: List of decrypted text lines in reading order.
        """
        try:
            newcon = self._parse_newcon(html_str)
            d_key = self._parse_d_key(html_str)
            full_html = self._decrypt_d(newcon, d_key)
            tree = html.fromstring(full_html)
            paragraphs = self._rebuild_paragraphs(tree)
            return paragraphs
        except Exception as e:
            logger.warning("Failed to parse chapter page 3+: %s", e)
            return []

    @classmethod
    def _extract_chapter_title(cls, tree: html.HtmlElement) -> str:
        """
        Extract the chapter title from the HTML tree.

        The title is expected to be located inside:
        <h1 id="chapterTitle">...</h1>

        :param tree: Parsed HTML element tree of the chapter page.
        :return: Chapter title as a string, or an empty string if not found.
        """
        return cls._first_str(tree.xpath('//h1[@id="chapterTitle"]/text()'))

    def _char_from_img(self, url: str) -> str:
        """
        Given an <img> src URL, return the mapped character if this image
        represents a single glyph.
        """
        if not self._FONT_MAP:
            self._FONT_MAP = json.loads(XIGUASHUWU_MAP_PATH.read_text(encoding="utf-8"))
        fname = url.split("/")[-1].split("?", 1)[0]
        char = self._FONT_MAP.get(fname)
        if char:
            return char
        if url in self._GLYPH_CACHE:
            return self._GLYPH_CACHE[url]
        if self._decode_font:
            char = self._recognize_glyph_from_url(url)
            if char:
                self._GLYPH_CACHE[url] = char
                return char
        return f'<img src="{url}" />'

    def _recognize_glyph_from_url(self, url: str) -> str | None:
        """
        Download the glyph image at `url` and run the font OCR on it.

        :param url: Fully-qualified <img src="..."> URL to a single-glyph image.
        :return: The recognized character (top-1) if OCR succeeds, otherwise None.
        """
        try:
            ocr = get_font_ocr(self._fontocr_cfg)
            if not ocr:
                return None

            resp = requests.get(url, headers=DEFAULT_USER_HEADERS, timeout=15)
            resp.raise_for_status()

            img_np = ocr.load_image_array_bytes(resp.content)

            char, score = ocr.predict([img_np])[0]

            return char if score >= self._CONF_THRESHOLD else None

        except Exception as e:
            logger.warning("Failed to ocr xiguashuwu glyph image %s: %s", url, e)
        return None

    @classmethod
    def _parse_codeurl(cls, text: str) -> int:
        """
        Extract the integer from `var codeurl="7";`.

        Raises ValueError if not found.
        """
        m = cls._CODEURL_PATTERN.search(text)
        if not m:
            raise ValueError("codeurl not found")
        return int(m.group(1))

    @classmethod
    def _parse_nrid(cls, text: str) -> str:
        """
        Extract the string from `var nrid="FGQSWYBCK";`.

        Raises ValueError if not found.
        """
        m = cls._NRID_PATTERN.search(text)
        if not m:
            raise ValueError("nrid not found")
        return m.group(1)

    @classmethod
    def _parse_newcon(cls, text: str) -> str:
        """
        Extract and decode the percent-encoded argument of
        `let newcon=decodeURIComponent("...");`.

        Raises ValueError if not found.
        """
        m = cls._NEWCON_PATTERN.search(text)
        if not m:
            raise ValueError("newcon not found")
        return urllib.parse.unquote(m.group(1))

    @classmethod
    def _parse_d_key(cls, text: str) -> str:
        """
        Extract the second argument (the hex key) from `d(newcon, "...");`.

        Raises ValueError if not found.
        """
        m = cls._D_CALL_PATTERN.search(text)
        if not m:
            raise ValueError("d() call with key not found")
        return m.group(1)

    @classmethod
    def _parse_client_meta(cls, tree: html.HtmlElement) -> str:
        """
        Given an lxml.html tree, return the `content` of
        <meta name="client" content="..."/> in <head>.

        Raises ValueError if missing.
        """
        vals = tree.xpath("//head/meta[@name='client']/@content")
        if not vals:
            raise ValueError("client meta not found")
        return str(vals[0])

    @staticmethod
    def _restore_order(raw_b64: str, code: int) -> list[int]:
        decoded = base64.b64decode(raw_b64).decode("utf-8")
        fragments = re.split(r"[A-Z]+%", decoded)

        order = [0] * len(fragments)
        for i, m in enumerate(fragments):
            # UpWz logic: k = ceil(parseInt(m) - ceil((i+1) % codeurl))
            k = int(m) - ((i + 1) % code)
            order[k] = i
        return order

    @staticmethod
    def _decrypt_d(a: str, b: str) -> str:
        digest = hashlib.md5(b.encode("utf-8")).hexdigest()  # 32 hex chars

        iv = digest[:16].encode("utf-8")
        key = digest[16:].encode("utf-8")

        ct = base64.b64decode(a)
        plaintext = aes_cbc_decrypt(key, iv, ct, block_size=32)

        return plaintext.decode("utf-8")

    def _rebuild_paragraphs(self, content_div: html.HtmlElement) -> list[str]:
        """
        Given a content container element, reconstruct each paragraph by
        interleaving normal text nodes and <img>-based glyphs.

        Uses `_char_from_img` to map image glyphs to characters.

        :param content_div: The HTML element containing <p> paragraphs.
        :return: List of reconstructed paragraph strings.
        """
        paragraphs: list[str] = []
        for p in content_div.xpath(".//p"):
            parts: list[str] = []

            # Leading text before any children
            if p.text and p.text.strip():
                parts.append(p.text.strip())

            for child in p:
                tag = child.tag.lower()
                if tag == "img":
                    src = (child.get("src") or "").strip()
                    full = src if src.startswith("http") else self.BASE_URL + src
                    parts.append(self._char_from_img(full))
                # Append any tail text after this child
                if child.tail and child.tail.strip():
                    parts.append(child.tail.strip())

            paragraph = "".join(parts).strip()
            paragraphs.append(paragraph)
        return paragraphs
