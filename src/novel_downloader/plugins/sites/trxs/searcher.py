#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.trxs.searcher
--------------------------------------------

"""

import logging

from lxml import html

from novel_downloader.plugins.base.searcher import BaseSearcher
from novel_downloader.plugins.searching import register_searcher
from novel_downloader.schemas import SearchResult

logger = logging.getLogger(__name__)


@register_searcher()
class TrxsSearcher(BaseSearcher):
    site_name = "trxs"
    priority = 30
    SEARCH_URL = "https://www.trxs.cc/e/search/index.php"
    BASE_URL = "https://www.trxs.cc/"

    @classmethod
    async def _fetch_html(cls, keyword: str) -> str:
        keyboard = cls._quote(keyword, encoding="gbk", errors="replace")
        show = "title"
        classid = "0"
        body = f"keyboard={keyboard}&show={show}&classid={classid}"
        headers = {
            "Origin": "https://www.trxs.cc",
            "Referer": "https://www.trxs.cc/",
            "Content-Type": "application/x-www-form-urlencoded",
        }
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
        rows = doc.xpath('//div[@class="books m-cols"]/div[@class="bk"]')
        results: list[SearchResult] = []

        for idx, row in enumerate(rows):
            href = cls._first_str(row.xpath(".//h3/a[1]/@href"))
            if not href:
                continue

            if limit is not None and idx >= limit:
                break

            # '/tongren/9302.html' -> "9302"
            book_id = href.split("/")[-1].split(".")[0]
            book_url = cls._abs_url(href)

            cover_rel = cls._first_str(
                row.xpath("./div[@class='pic']/a[1]/img[1]/@src")
            )
            cover_url = cls._abs_url(cover_rel) if cover_rel else ""

            title = cls._first_str(
                row.xpath("./div[@class='bk_right']/h3/a[1]//text()")
            )

            author = (
                cls._first_str(
                    row.xpath("./div[@class='bk_right']/div[@class='booknews']/text()"),
                    replaces=[("作者：", "")],
                )
                or "-"
            )

            update_date = cls._first_str(
                row.xpath(
                    "./div[@class='bk_right']/div[@class='booknews']/label[@class='date']/text()"
                )
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
                    update_date=update_date,
                    word_count="-",
                    priority=prio,
                )
            )
        return results
