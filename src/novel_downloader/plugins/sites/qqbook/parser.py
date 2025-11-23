#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.qqbook.parser
--------------------------------------------
"""

from __future__ import annotations

import base64
import json
import logging
import re
from typing import Any

from lxml import html
from novel_downloader.infra.paths import QQ_DECRYPT_SCRIPT_PATH
from novel_downloader.plugins.base.parser import BaseParser
from novel_downloader.plugins.registry import registrar
from novel_downloader.plugins.utils.js_eval import JsEvaluator
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

QQ_SCRIPT: AssetSpec = {
    "type": "local",
    "src": QQ_DECRYPT_SCRIPT_PATH,
    "filename": "qq_decrypt_node.js",
}
QQ_ASSETS: list[AssetSpec] = [
    {
        "type": "remote",
        "url": "https://imgservices-1252317822.image.myqcloud.com/coco/s10192022/cefc2a5d.pz1phw.js",
        "filename": "cefc2a5d.pz1phw.js",
    }
]


@registrar.register_parser()
class QqbookParser(YuewenQDFontMixin, BaseParser):
    """
    Parser for QQ 阅读 site.
    """

    site_name: str = "qqbook"

    _NUXT_BLOCK_RE = re.compile(
        r"window\.__NUXT__\s*=\s*([\s\S]*?);?\s*<\/script>",
        re.S,
    )

    def __init__(self, config: ParserConfig) -> None:
        """
        Initialize the QidianParser with the given configuration.
        """
        super().__init__(config)
        script_dir = self._cache_dir / "scripts"
        self._decryptor = NodeDecryptor(
            script_dir=script_dir,
            script=QQ_SCRIPT,
            assets=QQ_ASSETS,
        )
        self._evaluator = JsEvaluator(script_dir=script_dir)

    def parse_book_info(
        self,
        raw_pages: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        """
        Parse a book info page and extract metadata and chapter structure.

        Order: [info, catalog]

        :param raw_pages: Raw HTML of the book info page.
        :return: Parsed metadata and chapter structure as a dictionary.
        """
        if len(raw_pages) < 2:
            return None

        info_tree = html.fromstring(raw_pages[0])
        catalog_dict = json.loads(raw_pages[1])

        book_name = self._first_str(
            info_tree.xpath('//meta[@property="og:novel:book_name"]/@content')
        ) or self._first_str(
            info_tree.xpath('//h1[contains(@class, "book-title")]/text()')
        )
        author = self._first_str(
            info_tree.xpath('//meta[@property="og:novel:author"]/@content')
        ) or self._first_str(
            info_tree.xpath(
                '//div[contains(@class,"book-meta")]//a[contains(@class,"author")]/text()'
            ),
            replaces=[(" 著", ""), ("著", "")],
        )
        cover_url = self._first_str(
            info_tree.xpath('//meta[@property="og:image"]/@content')
        ) or self._first_str(
            info_tree.xpath('//div[contains(@class,"book-cover")]//img/@src')
        )
        update_time = self._first_str(
            info_tree.xpath('//meta[@property="og:novel:update_time"]/@content')
        ) or self._first_str(
            info_tree.xpath('//div[contains(@class,"update-time")]/text()'),
            replaces=[("更新时间：", "")],
        )
        serial_status = self._first_str(
            info_tree.xpath('//meta[@property="og:novel:status"]/@content')
        )
        # tags
        tags = [
            t.strip()
            for t in info_tree.xpath(
                '//div[contains(@class,"book-tags")]//a[contains(@class,"tag")]/text()'
            )
            if t.strip()
        ]
        # summary
        summary_raw = "\n".join(
            info_tree.xpath('//div[contains(@class,"book-intro")]//text()')
        )
        summary = (
            self._norm_space(summary_raw)
            if summary_raw
            else self._first_str(
                info_tree.xpath('//meta[@property="og:description"]/@content')
            )
        )

        # book_id for chapter URLs
        read_url = self._first_str(
            info_tree.xpath('//meta[@property="og:novel:read_url"]/@content')
        ) or self._first_str(info_tree.xpath('//meta[@property="og:url"]/@content'))
        book_id = ""
        if read_url:
            book_id = read_url.rstrip("/").split("/")[-1]

        # Chapters from the book_list
        data = catalog_dict.get("data") or []
        chapters: list[ChapterInfoDict] = []
        for item in data:
            cid = str(item.get("cid"))
            title = str(item.get("chapterName", "")).strip()
            accessible = bool(item.get("free") or item.get("purchased"))
            chap: ChapterInfoDict = {
                "title": title,
                "chapterId": cid,
                "url": f"/book-read/{book_id}/{cid}" if book_id and cid else "",
                "accessible": accessible,
            }
            chapters.append(chap)

        if not chapters:
            return None

        volumes: list[VolumeInfoDict] = [{"volume_name": "正文", "chapters": chapters}]

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "update_time": update_time,
            "serial_status": serial_status,
            "tags": tags,
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
            logger.warning("QQbook chapter %s :: raw_pages is empty", chapter_id)
            return None
        try:
            nuxt_block = self._find_nuxt_block(raw_pages[0])
            if not isinstance(nuxt_block, dict):
                return None
            data_list = nuxt_block.get("data")
            if not data_list:
                return None
            data_block = data_list[0]
        except Exception as e:
            logger.warning(
                "QQbook chapter %s :: failed to locate Nuxt block: %s",
                chapter_id,
                e,
            )
            return None

        curr_content = data_block.get("currentContent") or {}
        if not curr_content:
            logger.warning(
                "QQbook chapter %s :: currentContent missing or empty", chapter_id
            )
            return None

        content = curr_content.get("content", "")
        if not content:
            logger.warning(
                "QQbook chapter %s :: raw 'content' missing or empty", chapter_id
            )
            return None

        title = data_block.get("chapterTitle", "Untitled")
        cid = str(data_block.get("cid") or chapter_id)
        bk_cfg = data_block.get("fkConfig") or {}
        encrypt = curr_content.get("encrypt", False)
        font_encrypt = bool(curr_content.get("fontEncrypt"))
        font_resp = curr_content.get("fontResponse") or {}

        update_time = curr_content.get("updateTime") or ""
        word_count = curr_content.get("totalWords") or ""

        logger.debug(
            "QQbook chapter %s :: meta title=%r encrypt=%s font_encrypt=%s",
            chapter_id,
            title,
            encrypt,
            font_encrypt,
        )

        if encrypt:
            try:
                content = self._parse_encrypted(content=content, cid=cid, bk_cfg=bk_cfg)
                if content is None:
                    return None
            except Exception as e:
                logger.warning(
                    "QQbook chapter %s :: encrypted content decryption failed: %s",
                    chapter_id,
                    e,
                )
                return None

        extra: dict[str, Any] = {
            "site": self.site_name,
            "updated_at": update_time,
            "word_count": word_count,
            "encrypt": encrypt,
            "font_encrypt": font_encrypt,
        }

        if font_encrypt:
            content, refl_list, resources = self._parse_font_encrypted(
                content=content,
                font_resp=font_resp,
                cid=cid,
            )

            if not self._enable_ocr:
                if refl_list:
                    extra["refl_list"] = refl_list
                if resources:
                    extra["resources"] = resources

        if not content:
            logger.warning(
                "QQbook chapter %s :: content empty after decryption/font-mapping",
                chapter_id,
            )
            return None

        return {
            "id": cid,
            "title": title,
            "content": content,
            "extra": extra,
        }

    def _parse_encrypted(
        self,
        content: str,
        cid: str,
        bk_cfg: dict[str, Any],
    ) -> str | None:
        fkp = bk_cfg.get("fkp", "")
        fuid = bk_cfg.get("fuid", "")
        return self._decryptor.decrypt(
            ciphertext=content,
            chapter_id=cid,
            fkp=fkp,
            fuid=fuid,
        )

    def _parse_font_encrypted(
        self,
        content: str,
        font_resp: dict[str, Any],
        cid: str,
    ) -> tuple[str, list[str], list[dict[str, Any]]]:
        """
        QQ font encryption pipeline.

        Behavior:
          * If self._enable_ocr is True:
              - Apply CSS + OCR decoding (decode_qdfont_text).
              - DO NOT emit font resources.
          * If self._enable_ocr is False:
              - Apply CSS only (apply_css_text_rules).
              - DO NOT decode fonts.
              - Emit font resources (fixed URL + random font base64) and refl_list.
        """
        css_str = font_resp.get("css")
        random_font = font_resp.get("randomFont") or {}
        rf_data = random_font.get("data") if isinstance(random_font, dict) else None
        fixed_font_url = font_resp.get("fixedFontWoff2")

        if not css_str:
            logger.warning("QQbook chapter %s :: css missing or empty", cid)
            return "", [], []
        if not rf_data:
            logger.warning("QQbook chapter %s :: randomFont.data missing or empty", cid)
            return "", [], []
        if not fixed_font_url:
            logger.warning("QQbook chapter %s :: fixedFontWoff2 missing or empty", cid)
            return "", [], []

        # --- CSS extract ---
        paragraphs_str, refl_list = apply_css_text_rules(content, css_str)

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
                    "qqbook parser: OCR decoding failed (cid=%s): %s - falling back to font resources",  # noqa: E501
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

    def _find_nuxt_block(self, html_str: str) -> dict[str, Any] | None:
        m = self._NUXT_BLOCK_RE.search(html_str)
        if not m:
            return {}
        js_code = m.group(1).rstrip()  # RHS only
        result: dict[str, Any] | None = self._evaluator.eval(js_code)
        return result
