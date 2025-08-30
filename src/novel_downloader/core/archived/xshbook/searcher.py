#!/usr/bin/env python3
"""
novel_downloader.core.archived.xshbook.searcher
-----------------------------------------------

"""

import logging

from lxml import html
from novel_downloader.core.searchers.base import BaseSearcher
from novel_downloader.models import SearchResult

# from novel_downloader.core.searchers.registry import register_searcher

logger = logging.getLogger(__name__)


# @register_searcher(
#     site_keys=["xshbook"],
# )
class XshbookSearcher(BaseSearcher):
    site_name = "xshbook"
    priority = 30
    BASE_URL = "https://www.xshbook.com"
    SEARCH_URL = "https://www.sososhu.com/"

    @classmethod
    async def _fetch_html(cls, keyword: str) -> str:
        params = {
            "q": keyword,
            "site": "xshbook",
        }
        try:
            async with (await cls._http_get(cls.SEARCH_URL, params=params)) as resp:
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
        rows = doc.xpath(
            "//div[contains(@class,'so_list')]//div[contains(@class,'hot')]//div[contains(@class,'item')]"
        )
        results: list[SearchResult] = []

        for idx, row in enumerate(rows):
            if limit is not None and idx >= limit:
                break
            a_nodes = row.xpath(".//dl/dt/a[1]")
            a = a_nodes[0] if a_nodes else None
            href = a.get("href") if a is not None else ""
            book_url = cls._abs_url(href)
            book_id = cls._book_id_from_url(book_url) if book_url else ""
            if not book_id:
                continue

            title = (a.text_content() if a is not None else "").strip()
            author = cls._first_str(row.xpath(".//dl/dt/span[1]/text()"))
            cover_url = cls._first_str(
                row.xpath(".//div[contains(@class,'image')]//img/@src")
            )

            # Compute priority
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

    @staticmethod
    def _book_id_from_url(url: str) -> str:
        tail = url.split("xshbook.com", 1)[-1]
        tail = tail.strip("/")
        return tail.replace("/", "-")
