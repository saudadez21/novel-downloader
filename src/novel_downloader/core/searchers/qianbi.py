#!/usr/bin/env python3
"""
novel_downloader.core.searchers.qianbi
--------------------------------------

"""

import logging
import re

from lxml import html

from novel_downloader.core.searchers.base import BaseSearcher
from novel_downloader.core.searchers.registry import register_searcher
from novel_downloader.models import SearchResult

logger = logging.getLogger(__name__)


@register_searcher(
    site_keys=["qianbi"],
)
class QianbiSearcher(BaseSearcher):
    site_name = "qianbi"
    priority = 10
    BASE_URL = "https://www.23qb.com/"
    SEARCH_URL = "https://www.23qb.com/search.html"

    @classmethod
    async def _fetch_html(cls, keyword: str) -> str:
        """
        Fetch raw HTML from Qianbi's search page.

        :param keyword: The search term to query on Qianbi.
        :return: HTML text of the search results page, or an empty string on fail.
        """
        params = {"searchkey": keyword}
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
        Parse raw HTML from Qianbi search results into list of SearchResult.

        :param html_str: Raw HTML string from Qianbi search results page.
        :param limit: Maximum number of results to return, or None for all.
        :return: List of SearchResult dicts.
        """
        if html_str.find('<meta property="og:url"') != -1:
            return cls._parse_detail_html(html_str)
        return cls._parse_search_list_html(html_str, limit)

    @classmethod
    def _parse_detail_html(cls, html_str: str) -> list[SearchResult]:
        """
        Parse a single-book detail page, detected via <meta property="og:url">.

        :param html_str: Raw HTML of the book detail page.
        :return: A single-element list with the book's SearchResult.
        """
        doc = html.fromstring(html_str)
        url = doc.xpath('//meta[@property="og:url"]/@content')
        if not url:
            return []

        # extract book_id via regex
        m = re.search(r"/book/(\d+)/", url[0])
        book_id = m.group(1) if m else ""
        if not book_id:
            return []

        cover_nodes = doc.xpath('//div[contains(@class,"novel-cover")]//img/@data-src')
        if not cover_nodes:
            cover_nodes = doc.xpath('//div[contains(@class,"novel-cover")]//img/@src')
        cover_url = cover_nodes[0].strip() if cover_nodes else ""

        # title from <h1 class="page-title">
        title = (doc.xpath('//h1[@class="page-title"]/text()') or [""])[0].strip()
        author = (doc.xpath('//a[contains(@href,"/author/")]/@title') or [""])[
            0
        ].strip()

        latest_elem = doc.xpath(
            '//div[@class="module-row-info"]//a[@class="module-row-text"]'
        )
        latest_chapter = (
            latest_elem[0].get("title", "-").strip() if latest_elem else "-"
        )

        time_text = doc.xpath('//div[@class="module-heading newchapter"]/time/text()')
        if time_text:
            update_date = time_text[0].replace("更新时间：", "-").strip()
        else:
            update_date = "-"

        wc_text = doc.xpath('//span[contains(text(), "字")]/text()')
        word_count = wc_text[0].strip() if wc_text else ""

        return [
            SearchResult(
                site=cls.site_name,
                book_id=book_id,
                book_url=url[0],
                cover_url=cover_url,
                title=title,
                author=author,
                latest_chapter=latest_chapter,
                update_date=update_date,
                word_count=word_count,
                priority=cls.priority,
            )
        ]

    @classmethod
    def _parse_search_list_html(
        cls, html_str: str, limit: int | None
    ) -> list[SearchResult]:
        """
        Parse a multi-item search result page.

        :param html_str: Raw HTML of the search-results page.
        :param limit: Maximum number of items to return, or None for all.
        :return: List of SearchResult.
        """
        doc = html.fromstring(html_str)
        items = doc.xpath('//div[contains(@class,"module-search-item")]')
        results: list[SearchResult] = []

        for idx, item in enumerate(items):
            if limit is not None and idx >= limit:
                break
            # Title and book_id
            link = item.xpath('.//div[@class="novel-info-header"]/h3/a')[0]
            title = link.text_content().strip()
            href = link.get("href", "").strip("/")
            book_id = href.replace("book/", "").strip("/")
            if not book_id:
                continue
            book_url = cls.BASE_URL + href
            cover_nodes = item.xpath(
                './/div[contains(@class,"module-item-pic")]//img/@data-src'
            )
            if not cover_nodes:
                cover_nodes = item.xpath(
                    './/div[contains(@class,"module-item-pic")]//img/@src'
                )
            cover_url = cover_nodes[0].strip() if cover_nodes else ""

            # Compute priority
            prio = cls.priority + idx

            results.append(
                SearchResult(
                    site=cls.site_name,
                    book_id=book_id,
                    book_url=book_url,
                    cover_url=cover_url,
                    title=title,
                    author="-",  # Author is not present on the page
                    latest_chapter="-",
                    update_date="-",
                    word_count="-",
                    priority=prio,
                )
            )
        return results
