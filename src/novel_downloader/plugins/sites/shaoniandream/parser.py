#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.shaoniandream.parser
---------------------------------------------------
"""

import base64
import json
import re
from typing import Any

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
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
class ShaoniandreamParser(BaseParser):
    """
    Parser for 少年梦 book-info pages.
    """

    site_name: str = "shaoniandream"

    _RE_TAG_I = re.compile(r"<i[^>]*>.*?</i>", re.DOTALL)

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if len(html_list) < 2:
            return None

        info_tree = html.fromstring(html_list[0])
        catalog_data = json.loads(html_list[1])
        data = catalog_data.get("data", {})
        readdir = data.get("readdir", [])

        # --- parse main info ---
        book_name = self._first_str(
            info_tree.xpath(
                '//div[@class="bookdetail-name"]/span[@class="title"]/text()'
            )
        )
        author = self._first_str(
            info_tree.xpath('//span[contains(@class,"penName")]//a/text()')
        )
        cover_url = self._first_str(
            info_tree.xpath('//div[@class="cover"]/img/@data-original')
        )
        update_time = self._first_str(
            info_tree.xpath('//div[@class="bookdetial-newchapter"]//span/text()'),
            replaces=[("● ", "")],
        )
        word_count = self._first_str(
            info_tree.xpath('//div[@class="font-list"]/span[1]/text()')
        )
        serial_status = self._first_str(
            info_tree.xpath('//div[@class="bookdetail-name"]/i/text()')
        )
        tags = info_tree.xpath('//div[@class="label-list"]/span/text()')
        summary = self._join_strs(
            info_tree.xpath('//div[@class="bookdetial-jianjie"]//text()')
        )

        # --- parse volumes & chapters ---
        volumes: list[VolumeInfoDict] = []
        for v in readdir:
            volume_name = v.get("title", "")
            chapters: list[ChapterInfoDict] = []
            for c in v.get("list", []):
                chapters.append(
                    {
                        "title": c.get("title", ""),
                        "url": c.get("url", ""),
                        "chapterId": str(c.get("id", "")),
                        "accessible": "lock_fill" not in c.get("class", ""),
                    }
                )
            volumes.append(
                {
                    "volume_name": volume_name,
                    "volume_intro": v.get("miaoshu", ""),
                    "chapters": chapters,
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
            "serial_status": serial_status,
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
        if not html_list:
            return None

        raw_json = json.loads(html_list[0])
        if raw_json.get("status") != 1:
            raise ValueError("Invalid chapter response")

        data = raw_json["data"]
        title = data.get("title", "")
        img_prefix = data.get("imgPrefix", "")
        encryt_keys = data.get("encryt_keys", [])
        show_content = data.get("show_content", [])
        chapter_pics = data.get("chapterpic", [])

        # --- decode AES key/iv ---
        key = base64.b64decode(encryt_keys[0])
        iv = base64.b64decode(encryt_keys[1])

        def decrypt(cipher_b64: str) -> str:
            cipher_bytes = base64.b64decode(cipher_b64)
            cipher = AES.new(key, AES.MODE_CBC, iv)
            decrypted = cipher.decrypt(cipher_bytes)
            try:
                res: str = unpad(decrypted, AES.block_size).decode("utf-8")
            except ValueError:
                res = decrypted.decode("utf-8", errors="ignore")
            return res

        paragraphs: list[str] = []
        for p in show_content:
            para_enc = p.get("content", "")
            if not para_enc:
                continue
            paragraphs.append(self._RE_TAG_I.sub("", decrypt(para_enc)).strip())

        postscript = ""
        miaoshu_enc = data.get("miaoshu")
        if miaoshu_enc:
            try:
                postscript = self._RE_TAG_I.sub("", decrypt(miaoshu_enc)).strip()
                if postscript:
                    paragraphs.append(postscript)
            except Exception:
                pass

        image_positions: dict[int, list[dict[str, Any]]] = {}
        if chapter_pics:
            img_objs = []
            for pic in chapter_pics:
                url = pic.get("url")
                if not url:
                    continue
                full_url = img_prefix + url
                img_objs.append({"type": "url", "data": full_url})
            if img_objs:
                image_positions[len(paragraphs)] = img_objs

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
