#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.qidian.parser
--------------------------------------------
"""

from __future__ import annotations

import base64
import json
import logging
from html import unescape
from typing import Any

from lxml import html

from novel_downloader.infra.cookies import CookieStore
from novel_downloader.infra.paths import QD_DECRYPT_SCRIPT_PATH
from novel_downloader.libs.textutils import truncate_half_lines
from novel_downloader.plugins.base.parser import BaseParser
from novel_downloader.plugins.registry import registrar
from novel_downloader.plugins.utils.yuewen import (
    AssetSpec,
    NodeDecryptor,
    YuewenQDFontMixin,
    apply_css_text_rules,
)
from novel_downloader.schemas import (
    BookInfoDict,
    ChapterDict,
    ChapterInfoDict,
    ParserConfig,
    VolumeInfoDict,
)

logger = logging.getLogger(__name__)

QD_SCRIPT: AssetSpec = {
    "type": "local",
    "src": QD_DECRYPT_SCRIPT_PATH,
    "filename": "qidian_decrypt_node.js",
}
QD_ASSETS: list[AssetSpec] = [
    {
        "type": "remote",
        "url": "https://cococdn.qidian.com/coco/s12062024/4819793b.qeooxh.js",
        "filename": "4819793b.qeooxh.js",
    }
]


@registrar.register_parser()
class QidianParser(YuewenQDFontMixin, BaseParser):
    """
    Parser for 起点中文网 site.
    """

    site_name: str = "qidian"

    def __init__(self, config: ParserConfig, fuid: str = ""):
        """
        Initialize the QidianParser with the given configuration.
        """
        super().__init__(config)
        self._fuid = fuid
        self._cookie_store = CookieStore(self._cache_dir)
        script_dir = self._cache_dir / "scripts"
        self._decryptor = NodeDecryptor(
            script_dir=script_dir,
            script=QD_SCRIPT,
            assets=QD_ASSETS,
        )

    def parse_book_info(
        self,
        raw_pages: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if not raw_pages:
            return None

        doc = html.fromstring(raw_pages[0])

        # --- Book name ---
        book_name = self._first_str(doc.xpath('//h1[@id="bookName"]/text()'))
        if not book_name:
            book_name = self._first_str(
                doc.xpath('//meta[@property="og:novel:book_name"]/@content')
            )

        # --- Author ---
        author = self._first_str(doc.xpath('//a[@class="writer-name"]/text()'))
        if not author:
            author = self._first_str(
                doc.xpath('//meta[@property="og:novel:author"]/@content')
            )
        if not author:
            author = self._first_str(
                doc.xpath('//span[contains(@class,"author")]/text()'),
                replaces=[("作者:", "")],
            )

        # --- Book ID + cover ---
        book_id = doc.xpath('//a[@id="bookImg"]/@data-bid')[0]
        cover_url = f"https://bookcover.yuewen.com/qdbimg/349573/{book_id}/600.webp"

        # --- Update time ---
        update_time = self._first_str(
            doc.xpath('//span[@class="update-time"]/text()'),
            replaces=[("更新时间:", "")],
        )
        if not update_time:
            update_time = self._first_str(
                doc.xpath('//meta[@property="og:novel:update_time"]/@content')
            )

        # --- Status ---
        serial_status = self._first_str(
            doc.xpath('//p[@class="book-attribute"]/span[1]/text()')
        )
        if not serial_status:
            serial_status = self._first_str(
                doc.xpath('//meta[@property="og:novel:status"]/@content')
            )

        # --- Tags ---
        tags = [
            t.strip()
            for t in doc.xpath('//p[contains(@class,"all-label")]//a/text()')
            if t.strip()
        ]
        if not tags:
            # fallback meta category
            tag = self._first_str(
                doc.xpath('//meta[@property="og:novel:category"]/@content')
            )
            if tag:
                tags = [tag]

        # --- Word count ---
        word_count = self._first_str(doc.xpath('//p[@class="count"]/em[1]/text()'))

        # --- Summaries ---
        summary_brief = self._first_str(doc.xpath('//p[@class="intro"]/text()'))
        if not summary_brief:
            summary_brief = self._first_str(
                doc.xpath('//meta[@property="og:description"]/@content')
            )

        raw_lines = [
            s.strip()
            for s in doc.xpath('//p[@id="book-intro-detail"]//text()')
            if s.strip()
        ]
        summary = "\n".join(raw_lines) if raw_lines else summary_brief

        volumes = self._extract_volumes(doc)
        if not volumes:
            fragment = self._extract_div_block(raw_pages[0], 'id="allCatalog"')
            if not fragment:
                return None
            vol_tree = html.fromstring(fragment)
            volumes = self._extract_volumes(vol_tree)

        if not volumes:
            return None

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "update_time": update_time,
            "word_count": word_count,
            "serial_status": serial_status,
            "tags": tags,
            "summary_brief": summary_brief,
            "summary": summary,
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
            logger.warning("qidian parser: raw_pages is empty (chapter=%s)", chapter_id)
            return None
        try:
            ssr_data = self._find_ssr_page_context(raw_pages[0])
            chapter_info = self._extract_chapter_info(ssr_data)
        except Exception as e:
            logger.warning(
                "qidian parser: failed to locate ssr_pageContext (chapter=%s): %s",
                chapter_id,
                e,
            )
            return None

        if not chapter_info:
            logger.warning(
                "qidian parser: ssr_chapterInfo not found (chapter=%s)", chapter_id
            )
            return None

        if not self._can_view_chapter(chapter_info):
            logger.warning(
                "qidian parser: not purchased or inaccessible (chapter=%s)", chapter_id
            )
            return None

        duplicated = self._is_duplicated(chapter_info)
        encrypted = self._is_encrypted(chapter_info)

        title = chapter_info.get("chapterName", "Untitled")
        raw_html = chapter_info.get("content", "")
        cid = str(chapter_info.get("chapterId") or chapter_id)
        fkp = chapter_info.get("fkp", "")
        fuid = self._fuid or self._cookie_store.get("ywguid")
        author_say = chapter_info.get("authorSay", "").strip()
        modify_time = chapter_info.get("modifyTime", 0)
        word_count = chapter_info.get("actualWords", 0)

        if self._is_vip(chapter_info):
            raw_html = self._decryptor.decrypt(raw_html, cid, fkp, fuid)
            if raw_html is None:
                return None

        extra: dict[str, Any] = {
            "site": self.site_name,
            "author_say": author_say,
            "modify_time": modify_time,
            "word_count": word_count,
            "duplicated": duplicated,
            "encrypted": encrypted,
        }

        # Parse chapter content
        if encrypted:
            chapter_text, refl_list, resources = self._parse_font_encrypted(
                raw_html=raw_html,
                chapter_info=chapter_info,
                cid=cid,
            )
            if not self._enable_ocr:
                if refl_list:
                    extra["refl_list"] = refl_list
                if resources:
                    extra["resources"] = resources
        else:
            chapter_text = self._parse_normal(raw_html)

        if not chapter_text:
            logger.warning(
                "qidian parser: empty content after decryption/font-mapping (chapter=%s)",  # noqa: E501
                chapter_id,
            )
            return None

        if self._use_truncation and duplicated:
            chapter_text = truncate_half_lines(chapter_text)

        return {
            "id": cid,
            "title": title,
            "content": chapter_text,
            "extra": extra,
        }

    def _parse_normal(self, raw_html: str) -> str:
        """
        Extract structured chapter content from a normal Qidian page.
        """
        parts = raw_html.split("<p>")
        paragraphs = [unescape(p).strip() for p in parts if p.strip()]
        chapter_text = "\n".join(paragraphs)
        if not chapter_text:
            return ""
        return chapter_text

    def _parse_font_encrypted(
        self,
        raw_html: str,
        chapter_info: dict[str, Any],
        cid: str,
    ) -> tuple[str, list[str], list[dict[str, Any]]]:
        """
        Qidian font-encrypted chapter parsing.

        Behavior:
          * If self._enable_ocr is True:
              - Apply CSS + OCR decoding (decode_qdfont_text).
          * If self._enable_ocr is False:
              - Apply CSS only (apply_css_text_rules).
              - DO NOT decode fonts.
              - Emit font resources (fixed URL + random font base64) and refl_list.
        """
        css_str = chapter_info.get("css")
        random_font_str = chapter_info.get("randomFont")
        rf = json.loads(random_font_str) if isinstance(random_font_str, str) else None
        rf_data = rf.get("data") if rf else None
        fixed_font_url = chapter_info.get("fixedFontWoff2")

        if not css_str:
            logger.warning("qidian parser: missing CSS (chapter=%s)", cid)
            return "", [], []
        if not rf_data:
            logger.warning("qidian parser: randomFont.data missing (chapter=%s)", cid)
            return "", [], []
        if not fixed_font_url:
            logger.warning("qidian parser: fixedFontWoff2 missing (chapter=%s)", cid)
            return "", [], []

        # --- CSS extract ---
        paragraphs_str, refl_list = apply_css_text_rules(raw_html, css_str)

        # --- OCR path ---
        if self._enable_ocr:
            try:
                decoded = self._decode_qdfont(
                    text=paragraphs_str,
                    fixed_font_url=fixed_font_url,
                    random_font_data=bytes(rf_data),
                    reflected_chars=refl_list,
                )
                return decoded, [], []
            except Exception as e:
                logger.warning(
                    "qidian parser: OCR decoding failed (cid=%s): %s - falling back to font resources",  # noqa: E501
                    cid,
                    e,
                )

        # --- fallback: emit font resources ---
        random_bytes = bytes(rf_data)
        random_b64 = base64.b64encode(random_bytes).decode("ascii")
        resources: list[dict[str, Any]] = [
            {"type": "font", "url": fixed_font_url},
            {"type": "font", "base64": random_b64, "mime": "font/ttf"},
        ]

        return paragraphs_str, refl_list, resources

    @staticmethod
    def _extract_div_block(html_str: str, marker: str) -> str | None:
        """Extracts a balanced <div> block containing the given marker."""
        start = html_str.find(marker)
        if start == -1:
            return None

        div_start = html_str.rfind("<div", 0, start)
        if div_start == -1:
            return None

        depth = 0
        i = div_start
        n = len(html_str)

        while i < n:
            next_open = html_str.find("<div", i)
            next_close = html_str.find("</div", i)

            if next_close == -1:
                return None

            if next_open != -1 and next_open < next_close:
                depth += 1
                i = html_str.find(">", next_open)
                if i == -1:
                    return None
                i += 1
            else:
                depth -= 1
                close_end = html_str.find(">", next_close)
                if close_end == -1:
                    return None
                i = close_end + 1
                if depth == 0:
                    return html_str[div_start:i]

        return None

    def _extract_volumes(self, root: html.HtmlElement) -> list[VolumeInfoDict]:
        volumes: list[VolumeInfoDict] = []
        for vol in root.xpath('//div[@id="allCatalog"]//div[@class="catalog-volume"]'):
            vol_name = self._first_str(vol.xpath('.//h3[@class="volume-name"]/text()'))
            vol_name = vol_name.split(chr(183))[0].strip()
            chapters: list[ChapterInfoDict] = []
            for li in vol.xpath('.//ul[contains(@class,"volume-chapters")]/li'):
                title = self._first_str(li.xpath('.//a[@class="chapter-name"]/text()'))
                url = self._first_str(li.xpath('.//a[@class="chapter-name"]/@href'))
                cid = url.rstrip("/").split("/")[-1] if url else ""
                locked = bool(li.xpath('.//em[contains(@class, "chapter-locked")]'))
                chapters.append(
                    {
                        "title": title,
                        "url": url,
                        "chapterId": cid,
                        "accessible": not locked,
                    }
                )
            if chapters:
                volumes.append({"volume_name": vol_name, "chapters": chapters})
        return volumes

    @staticmethod
    def _find_ssr_page_context(html_str: str) -> dict[str, Any]:
        """Extract SSR JSON from <script id="vite-plugin-ssr_pageContext">."""
        tree = html.fromstring(html_str)
        script = tree.xpath('//script[@id="vite-plugin-ssr_pageContext"]/text()')
        return json.loads(script[0].strip()) if script else {}

    @staticmethod
    def _extract_chapter_info(ssr_data: dict[str, Any]) -> dict[str, Any]:
        """Extract the 'chapterInfo' dictionary from the SSR page context."""
        page_context = ssr_data.get("pageContext", {})
        page_props = page_context.get("pageProps", {})
        page_data = page_props.get("pageData", {})
        chapter_info = page_data.get("chapterInfo", {})
        return chapter_info if isinstance(chapter_info, dict) else {}

    @classmethod
    def _is_vip(cls, chapter_info: dict[str, Any]) -> bool:
        vip_flag = chapter_info.get("vipStatus", 0)
        fens_flag = chapter_info.get("fEnS", 0)
        return bool(vip_flag == 1 and fens_flag != 0)

    @classmethod
    def _can_view_chapter(cls, chapter_info: dict[str, Any]) -> bool:
        is_buy = chapter_info.get("isBuy", 0)
        vip_status = chapter_info.get("vipStatus", 0)
        return not (vip_status == 1 and is_buy == 0)

    @classmethod
    def _is_duplicated(cls, chapter_info: dict[str, Any]) -> bool:
        efw_flag = chapter_info.get("eFW", 0)
        return bool(efw_flag == 1)

    @classmethod
    def _is_encrypted(cls, chapter_info: dict[str, Any]) -> bool:
        """
        Chapter Encryption Status (cES):
          * 0: 内容是'明文'
          * 2: 字体加密
        """
        return int(chapter_info.get("cES", 0)) == 2
