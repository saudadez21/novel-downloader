#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.qidian.searcher
----------------------------------------------

"""

import base64
import hashlib
import json
import logging
import random
import time

from lxml import html

from novel_downloader.libs.crypto.rc4 import rc4_init, rc4_stream
from novel_downloader.plugins.base.searcher import BaseSearcher
from novel_downloader.plugins.searching import register_searcher
from novel_downloader.schemas import SearchResult

logger = logging.getLogger(__name__)


@register_searcher()
class QidianSearcher(BaseSearcher):
    site_name = "qidian"
    priority = 0
    SEARCH_URL = "https://www.qidian.com/so/{query}.html"
    _E1_VAL = {"l6": "", "l7": "", "l1": "", "l3": "", "pid": "qd_p_qidian", "eid": ""}

    @classmethod
    async def _fetch_html(cls, keyword: str) -> str:
        url = cls.SEARCH_URL.format(query=cls._quote(keyword))
        try:
            cookies = cls._calc_cookies(url)
            async with cls._http_get(url, cookies=cookies) as resp:
                resp.raise_for_status()
                return await cls._response_to_str(resp)
        except Exception:
            logger.error(
                "Failed to fetch HTML for keyword '%s' from '%s'",
                keyword,
                url,
            )
            return ""

    @classmethod
    def _parse_html(cls, html_str: str, limit: int | None = None) -> list[SearchResult]:
        doc = html.fromstring(html_str)
        items = doc.xpath(
            '//div[@id="result-list"]//li[contains(@class, "res-book-item")]'
        )
        results: list[SearchResult] = []

        for idx, item in enumerate(items):
            book_id = cls._first_str(item.xpath("./@data-bid"))
            book_url = cls._first_str(
                item.xpath('.//h3[contains(@class,"book-info-title")]//a/@href')
            )
            if not book_id or not book_url:
                continue
            if limit is not None and idx >= limit:
                break

            cover_url = cls._first_str(
                item.xpath('.//div[contains(@class,"book-img-box")]//img/@src')
            )
            book_url = cls._abs_url(book_url)
            cover_url = cls._abs_url(cover_url)

            title = cls._first_str(
                item.xpath('.//h3[contains(@class,"book-info-title")]//a/@title'),
                replaces=[("在线阅读", "")],
            )
            author = cls._first_str(
                item.xpath(
                    './/p[contains(@class,"author")]//a[contains(@class,"name")]/text()'
                    ' | .//p[contains(@class,"author")]//i/text()'
                )
            )
            latest_chapter = cls._first_str(
                item.xpath('.//p[contains(@class,"update")]//a/text()'),
                replaces=[("最新更新", "")],
            )
            update_date = cls._first_str(
                item.xpath('.//p[contains(@class,"update")]//span/text()')
            )
            word_count = cls._first_str(
                item.xpath(
                    './/div[contains(@class,"book-right-info")]//div[contains(@class,"total")]/p[1]/span/text()'
                )
            )

            results.append(
                SearchResult(
                    site=cls.site_name,
                    book_id=book_id,
                    book_url=book_url,
                    cover_url=cover_url,
                    title=title,
                    author=author,
                    latest_chapter=latest_chapter,
                    update_date=update_date,
                    word_count=word_count,
                    priority=cls.priority + idx,
                )
            )
        return results

    @classmethod
    def _calc_cookies(cls, new_uri: str) -> dict[str, str]:
        s_init = rc4_init(cls._d2("dGcwOUl0Myo5aA=="))
        _fp_val = hashlib.md5(str(random.random()).encode()).hexdigest()
        loadts = int(time.time() * 1000)
        duration = max(300, min(1000, int(random.normalvariate(600, 150))))
        timestamp = loadts + duration
        comb = f"{new_uri}{loadts}{_fp_val}"
        ck_val = hashlib.md5(comb.encode("utf-8")).hexdigest()
        new_payload = {
            cls._d("bG9hZHRz"): loadts,
            cls._d("dGltZXN0YW1w"): timestamp,
            cls._d("ZmluZ2VycHJpbnQ="): _fp_val,
            cls._d("YWJub3JtYWw="): "0" * 32,
            cls._d("Y2hlY2tzdW0="): ck_val,
        }
        plain_bytes = json.dumps(new_payload, separators=(",", ":")).encode("utf-8")
        cipher_bytes = rc4_stream(s_init, plain_bytes)
        return {
            "e1": cls._quote(json.dumps(cls._E1_VAL)),
            cls._d("d190c2Zw"): base64.b64encode(cipher_bytes).decode("utf-8"),
        }

    @staticmethod
    def _d(b: str) -> str:
        return base64.b64decode(b).decode()

    @staticmethod
    def _d2(b: str) -> bytes:
        return base64.b64decode(b)
