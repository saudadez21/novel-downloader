#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.faloo.parser
-------------------------------------------
"""

import base64
import logging
from typing import Any

from lxml import html
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
class FalooParser(BaseParser):
    """
    Parser for 飞卢小说网 book pages.
    """

    site_name: str = "faloo"

    def parse_book_info(
        self,
        raw_pages: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if not raw_pages:
            return None

        tree = html.fromstring(raw_pages[0])

        # Book metadata
        book_name = self._first_str(
            tree.xpath("//meta[@property='og:novel:book_name']/@content")
        )
        if not book_name:
            book_name = self._first_str(tree.xpath("//h1[@id='novelName']/text()"))

        author = self._first_str(
            tree.xpath("//meta[@property='og:novel:author']/@content")
        )
        if not author:
            author = self._first_str(
                tree.xpath("//a[contains(@class,'colorQianHui')]/text()")
            )

        serial_status = self._first_str(
            tree.xpath("//meta[@property='og:novel:status']/@content")
        )

        update_time = self._first_str(
            tree.xpath("//meta[@property='og:novel:update_time']/@content")
        )
        if not update_time:
            update_time = self._first_str(
                tree.xpath("//span[contains(text(),'更新时间')]/span/text()")
            )

        cover_url = self._first_str(tree.xpath("//meta[@property='og:image']/@content"))
        if not cover_url:
            cover_url = self._first_str(
                tree.xpath("//div[@class='T-L-T-Img']//img/@src")
            )

        tags: list[str] = []

        category = self._first_str(
            tree.xpath("//meta[@property='og:novel:category']/@content")
        )
        if category:
            tags.append(category)

        tag_nodes = tree.xpath("//a[contains(@class, 'LXbq')]/text()")
        for t in tag_nodes:
            if t.strip():
                tags.append(t.strip())

        summary_paras = tree.xpath("//div[@class='T-L-T-C-Box1']/p/text()")
        summary = self._join_strs(summary_paras)
        if not summary:
            summary = self._first_str(
                tree.xpath("//meta[@property='og:description']/@content")
            )

        # --- Volumes & Chapters ---
        # Faloo layout:
        #  * 作品相关 (optional)
        #  * 正文     (required)
        #  * VIP正文  (optional)
        volumes: list[VolumeInfoDict] = []

        related_box = tree.xpath("//div[contains(@class,'C-Fo-Z-Zuoping')]")
        if related_box:
            chaps = self._extract_chapters_in_box(related_box[0])
            if chaps:
                volumes.append(
                    {
                        "volume_name": "作品相关",
                        "chapters": chaps,
                    }
                )

        main_box = tree.xpath("//div[@id='mulu']")
        if main_box:
            chaps = self._extract_chapters_in_box(main_box[0])
            if chaps:
                volumes.append(
                    {
                        "volume_name": "正文",
                        "chapters": chaps,
                    }
                )

        vip_h2 = tree.xpath("//div[contains(@class,'DivVip')]")
        if vip_h2:
            vip_box = vip_h2[0].getparent()
            chaps = self._extract_chapters_in_box(vip_box)
            if chaps:
                volumes.append(
                    {
                        "volume_name": "VIP正文",
                        "chapters": chaps,
                    }
                )

        if not volumes:
            return None

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "serial_status": serial_status,
            "update_time": update_time,
            "summary": summary,
            "tags": tags,
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

        html_page = raw_pages[0]

        # check if chapter is locked
        if "您还没有订阅本章节" in html_page:
            return None
        if "您还没有登录，请登录后在继续阅读本部小说" in html_page:
            return None

        tree = html.fromstring(html_page)
        resources: list[MediaResource] = []
        paragraphs: list[str] = []

        title = self._first_str(tree.xpath('//div[@class="c_l_title"]//h1/text()'))

        # Extract <img> images that appear BEFORE paragraphs
        html_imgs = tree.xpath('//div[@id="con_imginfo"]//img')
        for img in html_imgs:
            url = img.get("src") or img.get("data-original")
            if not url:
                continue

            resources.append(
                {
                    "type": "image",
                    "paragraph_index": 0,
                    "url": url,
                    "alt": img.get("alt") or "",
                }
            )

        raw_paras = tree.xpath('//div[@class="noveContent"]//p')
        idx = 0
        for p in raw_paras:
            text = p.text_content().strip()

            # skip empty
            if not text:
                continue

            paragraphs.append(text)
            idx += 1

        is_vip = "image_do3" in html_page
        vip_b64_images = raw_pages[1:]

        if is_vip and not vip_b64_images:
            logger.warning("faloo chapter %s :: VIP images missing", chapter_id)

        for img_b64 in vip_b64_images:
            img_b64 = img_b64.strip()
            if not img_b64:
                continue

            if not self._enable_ocr:
                logger.warning(
                    "faloo chapter %s :: VIP chapter not decoded "
                    "(enable enable_ocr to OCR)",
                    chapter_id,
                )
                resources.append(
                    {
                        "type": "image",
                        "paragraph_index": idx,
                        "base64": img_b64,
                        "mime": "image/gif",
                    }
                )
            else:
                parsed = self.parse_image_chapter(img_b64)
                paragraphs.extend(parsed)
                idx += len(parsed)

        if not (paragraphs or resources):
            return None

        content = "\n".join(paragraphs)

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {
                "site": self.site_name,
                "vip": is_vip,
                "resources": resources,
            },
        }

    def parse_image_chapter(self, img_base64: str) -> list[str]:
        from novel_downloader.libs import imagekit

        img_bytes = base64.b64decode(img_base64)
        paragraphs: list[str] = []
        cache: list[str] = []

        img_arr = imagekit.load_image_array_bytes(img_bytes)
        img_lines = imagekit.split_by_white_lines(img_arr)

        preds = self._extract_text_from_image(img_lines, batch_size=self._batch_size)
        for line, (text, _) in zip(img_lines, preds, strict=False):
            if cache and imagekit.is_new_paragraph(line, paragraph_threshold=30):
                paragraphs.append("".join(cache))
                cache.clear()

            if s := text.strip():
                cache.append(s)

        # flush cache
        if cache:
            paragraphs.append("".join(cache))

        return paragraphs

    def _extract_chapters_in_box(
        self, box_elem: html.HtmlElement
    ) -> list[ChapterInfoDict]:
        chapters: list[ChapterInfoDict] = []

        # All <a> inside DivTable -> DivTr -> DivTd*
        for a in box_elem.xpath(".//div[contains(@class,'DivTable')]//a"):
            href = a.get("href", "").strip()
            if not href:
                continue

            # Convert protocol-relative //b.faloo.com/... to https:
            if href.startswith("//"):
                href = "https:" + href

            title = a.get("title") or a.text_content().strip()

            # Extract chapter id: "/1482723_53.html" -> "53"
            chapter_id = href.rsplit("_", 1)[-1].split(".", 1)[0]

            chapters.append(
                {
                    "title": title,
                    "url": href,
                    "chapterId": chapter_id,
                }
            )

        return chapters
