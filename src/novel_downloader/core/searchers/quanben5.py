#!/usr/bin/env python3
"""
novel_downloader.core.searchers.quanben5
----------------------------------------

"""

import json
import logging
import random
import re
import time

from lxml import html

from novel_downloader.core.searchers.base import BaseSearcher
from novel_downloader.core.searchers.registry import register_searcher
from novel_downloader.models import SearchResult

logger = logging.getLogger(__name__)


@register_searcher(
    site_keys=["quanben5"],
)
class Quanben5Searcher(BaseSearcher):
    site_name = "quanben5"
    priority = 30
    SEARCH_URL = "https://quanben5.com/"

    STATIC_CHARS = "PXhw7UT1B0a9kQDKZsjIASmOezxYG4CHo5Jyfg2b8FLpEvRr3WtVnlqMidu6cN"

    @classmethod
    def _fetch_html(cls, keyword: str) -> str:
        """
        Fetch raw HTML from Quanben5's search page.

        :param keyword: The search term to query on Quanben5.
        :return: HTML text of the search results page, or an empty string on fail.
        """
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
            response = cls._http_get(full_url, headers=headers)
            return response.text
        except Exception:
            logger.error(
                "Failed to fetch HTML for keyword '%s' from '%s'",
                keyword,
                cls.SEARCH_URL,
                exc_info=True,
            )
            return ""

    @classmethod
    def _parse_html(cls, html_str: str, limit: int | None = None) -> list[SearchResult]:
        """
        Parse raw HTML from Quanben5 search results into list of SearchResult.

        :param html_str: Raw HTML string from Quanben5 search results page.
        :param limit: Maximum number of results to return, or None for all.
        :return: List of SearchResult dicts.
        """
        prefix, suffix = "search(", ");"
        if html_str.startswith(prefix) and html_str.endswith(suffix):
            json_str = html_str[len(prefix) : -len(suffix)]
        else:
            json_str = html_str

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            return []

        content_html = data.get("content", "")
        doc = html.fromstring(content_html)
        rows = doc.xpath('//div[@class="pic_txt_list"]')
        results: list[SearchResult] = []

        for idx, row in enumerate(rows):
            if limit is not None and idx >= limit:
                break

            href = row.xpath("string(.//h3/a/@href)")
            m = re.match(r"/n/([^/]+)/", href or "")
            if not m:
                continue
            book_id = m.group(1)

            title_parts = row.xpath('.//span[@class="name"]//text()')
            title = "".join(p.strip() for p in title_parts if p.strip())

            author = cls._first_str(
                row.xpath('.//p[@class="info"]//span[@class="author"]/text()')
            )

            # Bump priority by result index
            prio = cls.priority + idx

            results.append(
                SearchResult(
                    site=cls.site_name,
                    book_id=book_id,
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
