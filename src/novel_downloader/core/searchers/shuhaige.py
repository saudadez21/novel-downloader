#!/usr/bin/env python3
"""
novel_downloader.core.searchers.shuhaige
----------------------------------------

"""

import logging
import time
from urllib.parse import urljoin

from lxml import html

from novel_downloader.core.searchers.base import BaseSearcher
from novel_downloader.core.searchers.registry import register_searcher
from novel_downloader.models import SearchResult

logger = logging.getLogger(__name__)


@register_searcher(
    site_keys=["shuhaige"],
)
class ShuhaigeSearcher(BaseSearcher):
    site_name = "shuhaige"
    priority = 30
    BASE_URL = "https://www.shuhaige.net"
    SEARCH_URL = "https://www.shuhaige.net/search.html"

    @classmethod
    async def _fetch_html(cls, keyword: str) -> str:
        """
        Fetch raw HTML from Shuhaige's search page.

        :param keyword: The search term to query on Shuhaige.
        :return: HTML text of the search results page, or an empty string on fail.
        """
        data = {
            "searchtype": "all",
            "searchkey": keyword,
        }
        ts = int(time.time())
        # baidu cookie format: f"Hm_lpvt_{site_id}={timestamp}"
        cookie_str = (
            f"Hm_lpvt_3094b20ed277f38e8f9ac2b2b29d6263={ts}; "
            f"Hm_lpvt_c3da01855456ad902664af23cc3254cb={ts}"
        )
        headers = {
            "Origin": "https://www.shuhaige.net",
            "Referer": "https://www.shuhaige.net/",
            "Cookie": cookie_str,
        }
        try:
            async with (
                await cls._http_post(cls.SEARCH_URL, data=data, headers=headers)
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
        Parse raw HTML from Shuhaige search results into list of SearchResult.

        :param html_str: Raw HTML string from Shuhaige search results page.
        :param limit: Maximum number of results to return, or None for all.
        :return: List of SearchResult dicts.
        """
        doc = html.fromstring(html_str)
        rows = doc.xpath('//div[@id="sitembox"]/dl')
        results: list[SearchResult] = []

        for idx, row in enumerate(rows):
            if limit is not None and idx >= limit:
                break

            # Book main link & cover
            cover_a = row.xpath("./dt/a")[0]
            book_url = urljoin(cls.BASE_URL, cover_a.get("href"))
            cover_img = cover_a.xpath("./img")[0]
            cover_url = cover_img.get("src")
            title = cover_img.get("alt")

            # Book ID from URL
            book_id = cover_a.get("href").strip("/").split("/")[0]

            # h3 title link (sometimes same as cover link)
            h3_title = row.xpath("./dd/h3/a/text()")
            if h3_title:
                title = h3_title[0].strip()

            # Other info: author, status, category, word count
            other_dd = row.xpath('./dd[@class="book_other"]')[0]
            author = other_dd.xpath(".//span")[0].text.strip()
            # status = other_dd.xpath('.//span')[1].text.strip()
            # category = other_dd.xpath('.//span')[2].text.strip()
            word_count = other_dd.xpath(".//span")[3].text.strip()

            # Latest chapter & update date
            latest_dd = row.xpath('./dd[@class="book_other"]')[-1]
            latest_chapter_link = latest_dd.xpath(".//a")[0]
            latest_chapter = latest_chapter_link.text.strip()
            update_date = latest_dd.xpath(".//span/text()")[0].strip()

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
                    latest_chapter=latest_chapter,
                    update_date=update_date,
                    word_count=word_count,
                    priority=prio,
                )
            )
        return results
