#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.shuhaige.searcher
------------------------------------------------

"""

import logging
import time

from lxml import html

from novel_downloader.plugins.base.searcher import BaseSearcher
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import SearchResult

logger = logging.getLogger(__name__)


@registrar.register_searcher()
class ShuhaigeSearcher(BaseSearcher):
    site_name = "shuhaige"
    priority = 30
    BASE_URL = "https://www.shuhaige.net"
    SEARCH_URL = "https://www.shuhaige.net/search.html"

    async def _fetch_html(self, keyword: str) -> str:
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
            async with self._http_post(
                self.SEARCH_URL, data=data, headers=headers
            ) as resp:
                resp.raise_for_status()
                return await self._response_to_str(resp)
        except Exception:
            logger.error(
                "Failed to fetch HTML for keyword '%s' from '%s'",
                keyword,
                self.SEARCH_URL,
            )
            return ""

    def _parse_html(
        self, html_str: str, limit: int | None = None
    ) -> list[SearchResult]:
        doc = html.fromstring(html_str)
        rows = doc.xpath('//div[@id="sitembox"]/dl')
        results: list[SearchResult] = []

        for idx, row in enumerate(rows):
            href = self._first_str(row.xpath("./dt/a[1]/@href")) or self._first_str(
                row.xpath("./dd/h3/a[1]/@href")
            )
            if not href:
                continue

            if limit is not None and idx >= limit:
                break

            book_id = href.strip("/").split("/")[0]
            book_url = self._abs_url(href)

            title = self._first_str(
                row.xpath("./dd/h3/a[1]//text()")
            ) or self._first_str(row.xpath("./dt/a[1]/img[1]/@alt"))

            cover_rel = self._first_str(row.xpath("./dt/a[1]/img[1]/@src"))
            cover_url = self._abs_url(cover_rel) if cover_rel else ""

            author = (
                self._first_str(
                    row.xpath("./dd[@class='book_other'][1]/span[1]/text()")
                )
                or "-"
            )
            word_count = (
                self._first_str(
                    row.xpath("./dd[@class='book_other'][1]/span[4]/text()")
                )
                or "-"
            )

            latest_chapter = (
                self._first_str(
                    row.xpath("./dd[@class='book_other'][last()]/a[1]//text()")
                )
                or "-"
            )
            update_date = (
                self._first_str(
                    row.xpath("./dd[@class='book_other'][last()]/span[1]//text()")
                )
                or "-"
            )

            # Compute priority
            prio = self.priority + idx

            results.append(
                SearchResult(
                    site=self.site_name,
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
