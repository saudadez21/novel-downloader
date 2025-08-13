#!/usr/bin/env python3
"""
novel_downloader.core.searchers.tongrenquan
-------------------------------------------

"""

import logging
import re
from urllib.parse import urljoin

from lxml import html

from novel_downloader.core.searchers.base import BaseSearcher
from novel_downloader.core.searchers.registry import register_searcher
from novel_downloader.models import SearchResult

logger = logging.getLogger(__name__)


@register_searcher(
    site_keys=["tongrenquan"],
)
class TongrenquanSearcher(BaseSearcher):
    site_name = "tongrenquan"
    priority = 30
    SEARCH_URL = "https://www.tongrenquan.org/e/search/indexstart.php"
    BASE_URL = "https://www.tongrenquan.org"

    @classmethod
    async def _fetch_html(cls, keyword: str) -> str:
        """
        Fetch raw HTML from Tongrenquan's search page.

        :param keyword: The search term to query on Tongrenquan.
        :return: HTML text of the search results page, or an empty string on fail.
        """
        keyboard = cls._quote(keyword, encoding="gbk", errors="replace")
        show = "title"
        classid = "0"
        body = f"keyboard={keyboard}&show={show}&classid={classid}"
        headers = {
            "Origin": "https://www.tongrenquan.cc",
            "Referer": "https://www.tongrenquan.cc/",
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
        Parse raw HTML from Tongrenquan search results into list of SearchResult.

        :param html_str: Raw HTML string from Tongrenquan search results page.
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
            book_id = m.group(2) if m else ""

            src_nodes = row.xpath('.//div[@class="pic"]//img/@src')
            rel_src = src_nodes[0].strip() if src_nodes else ""
            cover_url = urljoin(cls.BASE_URL, rel_src) if rel_src else ""

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
                    cover_url=cover_url,
                    title=title,
                    author=author,
                    latest_chapter="-",
                    update_date=update_date,
                    word_count="-",
                    priority=prio,
                )
            )
        return results
