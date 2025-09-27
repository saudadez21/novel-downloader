#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.piaotia.searcher
-----------------------------------------------

"""

import logging

from lxml import html

from novel_downloader.plugins.base.searcher import BaseSearcher
from novel_downloader.plugins.searching import register_searcher
from novel_downloader.schemas import SearchResult

logger = logging.getLogger(__name__)


@register_searcher()
class PiaotiaSearcher(BaseSearcher):
    site_name = "piaotia"
    priority = 30
    SEARCH_URL = "https://www.piaotia.com/modules/article/search.php"

    @classmethod
    async def _fetch_html(cls, keyword: str) -> str:
        # data = {
        #     "searchtype": "articlename",
        #     # "searchtype": "author",
        #     # "searchtype": "keywords",
        #     "searchkey": cls._quote(keyword, encoding="gbk", errors='replace'),
        #     "Submit": cls._quote(" 搜 索 ", encoding="gbk", errors='replace'),
        # }
        searchtype = "articlename"
        searchkey = cls._quote(keyword, encoding="gbk", errors="replace")
        submit = cls._quote(" 搜 索 ", encoding="gbk", errors="replace")
        body = f"searchtype={searchtype}&searchkey={searchkey}&Submit={submit}"
        headers = {
            "Origin": "https://www.piaotia.com",
            "Referer": "https://www.piaotia.com",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        try:
            async with cls._http_post(
                cls.SEARCH_URL, data=body, headers=headers
            ) as resp:
                resp.raise_for_status()
                return await cls._response_to_str(resp, encoding="gbk")
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
        rows = doc.xpath('//table[@class="grid"]//tr[td]')
        results: list[SearchResult] = []

        for idx, row in enumerate(rows):
            href = cls._first_str(row.xpath("./td[1]/a[1]/@href"))
            if not href:
                continue

            if limit is not None and idx >= limit:
                break

            # "https://www.piaotia.com/bookinfo/14/14767.html" -> "14-14767"
            book_id = href.rstrip(".html").split("bookinfo/")[-1].replace("/", "-")
            book_url = cls._abs_url(href)

            title = cls._first_str(row.xpath("./td[1]/a[1]//text()"))

            latest_chapter = cls._first_str(row.xpath("./td[2]/a[1]//text()")) or "-"

            author = cls._first_str(row.xpath("./td[3]//text()")) or "-"
            word_count = cls._first_str(row.xpath("./td[4]//text()")) or "-"
            update_date = cls._first_str(row.xpath("./td[5]//text()")) or "-"

            # Compute priority incrementally
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
