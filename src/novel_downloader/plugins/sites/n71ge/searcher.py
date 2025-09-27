#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.n71ge.searcher
---------------------------------------------

"""

import contextlib
import logging

from lxml import html

from novel_downloader.plugins.base.searcher import BaseSearcher
from novel_downloader.plugins.searching import register_searcher
from novel_downloader.schemas import SearchResult

logger = logging.getLogger(__name__)


@register_searcher()
class N71geSearcher(BaseSearcher):
    site_name = "n71ge"
    priority = 20
    BASE_URL = "https://www.71ge.com"
    SEARCH_URL = "https://www.71ge.com/search.php"

    @classmethod
    async def _fetch_html(cls, keyword: str) -> str:
        headers = {
            "Dnt": "1",
            "Origin": "https://www.71ge.com",
            "Referer": "https://www.71ge.com/search.php",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        with contextlib.suppress(Exception):
            async with cls._http_get(cls.SEARCH_URL, headers=headers) as resp:
                await resp.read()
        searchkey = cls._quote(keyword, encoding="gbk", errors="replace")
        login = "login"
        submit = cls._quote(
            "&#160;搜&#160;&#160;索&#160;", encoding="gbk", errors="replace"
        )
        body = f"s={searchkey}&action={login}&submit={submit}"
        try:
            async with cls._http_post(
                cls.SEARCH_URL, data=body, headers=headers
            ) as resp:
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
        doc = html.fromstring(html_str)
        rows = doc.xpath("//tr[td/a]")
        results: list[SearchResult] = []

        for idx, row in enumerate(rows):
            title_a = row.xpath("./td[1]/a")
            href = cls._first_str([a.get("href") for a in title_a])
            title = cls._first_str([a.text_content() for a in title_a])
            if not href:
                continue

            if limit is not None and idx >= limit:
                break

            # '/341_341309/' -> "341_341309"
            book_id = href.strip("/")
            book_url = cls._abs_url(href)

            latest_chapter = cls._first_str(row.xpath("./td[2]/a/text()"))
            author = cls._first_str(row.xpath("./td[3]/text()"))
            word_count = cls._first_str(row.xpath("./td[4]/text()"))
            update_date = cls._first_str(row.xpath("./td[5]/text()"))

            # Compute priority
            prio = cls.priority + idx

            results.append(
                SearchResult(
                    site=cls.site_name,
                    book_id=book_id,
                    book_url=book_url,
                    cover_url="",
                    title=title,
                    author=author,
                    latest_chapter=latest_chapter,
                    update_date=update_date,
                    word_count=word_count,
                    priority=prio,
                )
            )
        return results
