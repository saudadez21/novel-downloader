#!/usr/bin/env python3
"""
novel_downloader.core.archived.qidian.searcher
----------------------------------------------

"""

import logging

from lxml import html
from novel_downloader.core.searchers.base import BaseSearcher
from novel_downloader.models import SearchResult

logger = logging.getLogger(__name__)


# @register_searcher(
#     site_keys=["qidian", "qd"],
# )
class QidianSearcher(BaseSearcher):
    """
    TODO: 现在默认没有 cookie 会跳转
    """

    site_name = "qidian"
    priority = 0
    SEARCH_URL = "https://www.qidian.com/so/{query}.html"

    @classmethod
    async def _fetch_html(cls, keyword: str) -> str:
        url = cls.SEARCH_URL.format(query=cls._quote(keyword))
        try:
            async with (await cls._http_get(url)) as resp:
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

        base_prio = getattr(cls, "priority", 0)
        for idx, item in enumerate(items):
            if limit is not None and idx >= limit:
                break
            book_id = item.get("data-bid")
            if not book_id:
                continue
            title_elem = item.xpath('.//h3[@class="book-info-title"]/a')[0]
            title = title_elem.text_content().strip()
            author_nodes = item.xpath(
                './/p[@class="author"]/a[@class="name"] | .//p[@class="author"]/i'
            )
            author = author_nodes[0].text_content().strip() if author_nodes else ""
            prio = base_prio + idx
            results.append(
                SearchResult(
                    site=cls.site_name,
                    book_id=book_id,
                    book_url="",
                    cover_url="",
                    title=title,
                    author=author,
                    latest_chapter="-",
                    update_date="-",
                    word_count="-",
                    priority=prio,
                )
            )
        return results
