#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.quanben5.searcher
------------------------------------------------

"""

import json
import logging
import random
import time

from lxml import html

from novel_downloader.plugins.base.searcher import BaseSearcher
from novel_downloader.plugins.searching import register_searcher
from novel_downloader.schemas import SearchResult

logger = logging.getLogger(__name__)


@register_searcher()
class Quanben5Searcher(BaseSearcher):
    site_name = "quanben5"
    priority = 30
    BASE_URL = "https://quanben5.com"
    SEARCH_URL = "https://quanben5.com/"

    STATIC_CHARS = "PXhw7UT1B0a9kQDKZsjIASmOezxYG4CHo5Jyfg2b8FLpEvRr3WtVnlqMidu6cN"

    @classmethod
    async def _fetch_html(cls, keyword: str) -> str:
        t = str(int(time.time() * 1000))
        uri_keyword = cls._quote(keyword)
        b_raw = cls._base64(uri_keyword)
        b = cls._quote(b_raw)

        params = {
            "c": "book",
            "a": "search.json",
            "callback": "search",
            "t": t,
            "keywords": uri_keyword,
            "b": b,
        }
        full_url = cls._build_url(cls.SEARCH_URL, params)

        headers = {
            "Host": "quanben5.com",
            "Referer": "https://quanben5.com/search.html",
        }

        try:
            async with cls._http_get(full_url, headers=headers) as resp:
                resp.raise_for_status()
                return await cls._response_to_str(resp)
        except Exception:
            logger.error(
                "Failed to fetch HTML for keyword '%s' from '%s'",
                keyword,
                cls.SEARCH_URL,
            )
            return ""

    @classmethod
    def _parse_html(cls, html_str: str, limit: int | None = None) -> list[SearchResult]:
        # Unwrap JSONP: search({...});
        prefix, suffix = "search(", ");"
        json_str = (
            html_str[len(prefix) : -len(suffix)]
            if html_str.startswith(prefix) and html_str.endswith(suffix)
            else html_str
        )

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            return []

        content_html = data.get("content", "")
        if not content_html:
            return []

        doc = html.fromstring(content_html)
        rows = doc.xpath('//div[@class="pic_txt_list"]')
        results: list[SearchResult] = []

        for idx, row in enumerate(rows):
            href = cls._first_str(row.xpath(".//h3/a/@href"))
            if not href:
                continue

            if limit is not None and idx >= limit:
                break

            # '/n/douposanqian/' -> "douposanqian"
            book_id = href.rstrip("/").split("/")[-1]
            book_url = cls._abs_url(href)

            cover_rel = cls._first_str(row.xpath(".//div[@class='pic']//img/@src"))
            cover_url = cls._abs_url(cover_rel) if cover_rel else ""

            title = "".join(
                t.strip()
                for t in row.xpath(".//h3/a/span[@class='name']//text()")
                if t and t.strip()
            )

            author = cls._first_str(
                row.xpath(".//p[@class='info']//span[contains(@class,'author')]/text()")
            )

            # Bump priority by result index
            prio = cls.priority + idx

            results.append(
                SearchResult(
                    site=cls.site_name,
                    book_id=book_id,
                    book_url=book_url,
                    cover_url=cover_url,
                    title=title,
                    author=author,
                    latest_chapter="-",
                    update_date="-",
                    word_count="-",
                    priority=prio,
                )
            )
        return results

    @classmethod
    def _base64(cls, s: str) -> str:
        out = []
        for ch in s:
            idx = cls.STATIC_CHARS.find(ch)
            code = cls.STATIC_CHARS[(idx + 3) % 62] if idx != -1 else ch
            n1 = int(random.random() * 62)
            n2 = int(random.random() * 62)
            out.append(cls.STATIC_CHARS[n1])
            out.append(code)
            out.append(cls.STATIC_CHARS[n2])
        return "".join(out)
