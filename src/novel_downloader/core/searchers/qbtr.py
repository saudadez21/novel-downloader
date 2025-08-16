#!/usr/bin/env python3
"""
novel_downloader.core.searchers.qbtr
------------------------------------

"""

import logging
import re

from lxml import html

from novel_downloader.core.searchers.base import BaseSearcher
from novel_downloader.core.searchers.registry import register_searcher
from novel_downloader.models import SearchResult

logger = logging.getLogger(__name__)


@register_searcher(
    site_keys=["qbtr"],
)
class QbtrSearcher(BaseSearcher):
    site_name = "qbtr"
    priority = 30
    BASE_URL = "https://www.qbtr.cc"
    SEARCH_URL = "https://www.qbtr.cc/e/search/index.php"

    @classmethod
    async def _fetch_html(cls, keyword: str) -> str:
        """
        Fetch raw HTML from Qbtr's search page.

        :param keyword: The search term to query on Qbtr.
        :return: HTML text of the search results page, or an empty string on fail.
        """
        keyboard = cls._quote(keyword, encoding="gbk", errors="replace")
        show = "title"
        classid = "0"
        body = f"keyboard={keyboard}&show={show}&classid={classid}"
        headers = {
            "Origin": "https://www.qbtr.cc",
            "Referer": "https://www.qbtr.cc/",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        try:
            async with (
                await cls._http_post(cls.SEARCH_URL, data=body, headers=headers)
            ) as resp:
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
        """
        Parse raw HTML from Qbtr search results into list of SearchResult.

        :param html_str: Raw HTML string from Qbtr search results page.
        :param limit: Maximum number of results to return, or None for all.
        :return: List of SearchResult dicts.
        """
        doc = html.fromstring(html_str)
        rows = doc.xpath('//div[@class="books m-cols"]/div[@class="bk"]')
        results: list[SearchResult] = []

        for idx, row in enumerate(rows):
            if limit is not None and idx >= limit:
                break
            # Title and book_id
            link_elem = row.xpath(".//h3/a")[0]
            href = link_elem.get("href", "").strip()
            m = re.match(r"^/([^/]+)/(\d+)\.html$", href)
            book_id = f"{m.group(1)}-{m.group(2)}" if m else ""
            if not book_id:
                continue
            book_url = cls.BASE_URL + href

            title = link_elem.text_content().strip()

            author_text = row.xpath('string(.//div[@class="booknews"]/text())').strip()
            author = author_text.replace("作者：", "").strip()

            update_date = row.xpath(
                'string(.//div[@class="booknews"]/label[@class="date"])'
            ).strip()

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
                    latest_chapter="-",
                    update_date=update_date,
                    word_count="-",
                    priority=prio,
                )
            )
        return results
