#!/usr/bin/env python3
"""
novel_downloader.core.searchers.ttkan
-------------------------------------

"""

import logging

from lxml import html

from novel_downloader.core.searchers.base import BaseSearcher
from novel_downloader.core.searchers.registry import register_searcher
from novel_downloader.models import SearchResult

logger = logging.getLogger(__name__)


@register_searcher(
    site_keys=["ttkan"],
)
class TtkanSearcher(BaseSearcher):
    site_name = "ttkan"
    priority = 100
    BASE_URL = "https://www.ttkan.co"
    SEARCH_URL = "https://www.ttkan.co/novel/search"

    @classmethod
    async def _fetch_html(cls, keyword: str) -> str:
        """
        Fetch raw HTML from Ttkan's search page.

        :param keyword: The search term to query on Ttkan.
        :return: HTML text of the search results page, or an empty string on fail.
        """
        params = {"q": keyword}
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
        """
        Parse raw HTML from Ttkan search results into list of SearchResult.

        :param html_str: Raw HTML string from Ttkan search results page.
        :param limit: Maximum number of results to return, or None for all.
        :return: List of SearchResult dicts.
        """
        doc = html.fromstring(html_str)
        items = doc.xpath(
            '//div[contains(@class,"frame_body")]//div[@class="pure-g"]/div[contains(@class,"novel_cell")]'
        )
        if not items:
            items = doc.xpath('//div[contains(@class,"novel_cell")]')
        results: list[SearchResult] = []

        for idx, item in enumerate(items):
            if limit is not None and len(results) >= limit:
                break

            # link -> /novel/chapters/<book_id>
            hrefs = item.xpath(".//a[@href]/@href")
            href = hrefs[0].strip() if hrefs else ""
            book_id = href.strip("/").split("/")[-1] if href else ""
            if not book_id:
                continue
            book_url = cls.BASE_URL + href

            cover_nodes = item.xpath(".//amp-img/@src")
            cover_url = cover_nodes[0].strip() if cover_nodes else ""

            # title -> <h3> inside that link
            titles = item.xpath(".//h3/text()")
            title = titles[0].strip() if titles else ""

            # author -> <li> whose text starts with "作者："
            author = item.xpath('.//li[starts-with(normalize-space(.),"作者")]/text()')
            author_str = ""
            if author:
                txt = author[0].strip()
                # split off the "作者：" label
                author_str = txt.split("：", 1)[1].strip() if "：" in txt else txt

            prio = cls.priority + idx
            results.append(
                SearchResult(
                    site=cls.site_name,
                    book_id=book_id,
                    book_url=book_url,
                    cover_url=cover_url,
                    title=title,
                    author=author_str,
                    latest_chapter="-",
                    update_date="-",
                    word_count="-",
                    priority=prio,
                )
            )
        return results
