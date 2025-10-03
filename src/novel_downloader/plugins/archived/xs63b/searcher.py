#!/usr/bin/env python3
"""
novel_downloader.plugins.archived.xs63b.searcher
------------------------------------------------

"""

import logging

from lxml import html
from novel_downloader.plugins.base.searcher import BaseSearcher
from novel_downloader.schemas import SearchResult

logger = logging.getLogger(__name__)


class Xs63bSearcher(BaseSearcher):
    site_name = "xs63b"
    priority = 30
    BASE_URL = "https://www.xs63b.com"
    SEARCH_URL = "https://www.xs63b.com/search/"

    async def _fetch_html(self, keyword: str) -> str:
        headers = {
            "Host": "www.xs63b.com",
            "Origin": "https://www.xs63b.com",
            "Referer": "https://www.xs63b.com/",
        }
        try:
            async with self._http_get(self.BASE_URL, headers=headers) as resp:
                resp.raise_for_status()
                base_html = await self._response_to_str(resp)
            data = {
                "_token": self._parse_token(base_html),
                "kw": keyword,
            }
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
        rows = doc.xpath("//div[@class='toplist']/ul/li")
        results: list[SearchResult] = []

        for idx, row in enumerate(rows):
            href = self._first_str(row.xpath(".//p[@class='s1']/a[1]/@href"))
            if not href:
                continue

            if limit is not None and idx >= limit:
                break

            # 'https://www.xs63b.com/{catalog}/{name}/' -> "{catalog}-{name}"
            book_id = href.split("xs63b.com", 1)[-1].strip(" /").replace("/", "-")
            book_url = self._abs_url(href)

            title = "".join(row.xpath(".//p[@class='s1']//a//text()"))

            latest_chapter = (
                self._first_str(row.xpath(".//p[@class='s2']//a/text()")) or "-"
            )
            author = self._first_str(row.xpath(".//p[@class='s3']/text()")) or "-"
            word_count = self._first_str(row.xpath(".//p[@class='s4']/text()")) or "-"
            update_date = self._first_str(row.xpath(".//p[@class='s6']/text()")) or "-"

            # Compute priority
            prio = self.priority + idx

            results.append(
                SearchResult(
                    site=self.site_name,
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

    @staticmethod
    def _parse_token(html_str: str) -> str:
        doc = html.fromstring(html_str)
        vals = doc.xpath("//div[@id='search']//input[@name='_token']/@value")
        return vals[0].strip() if vals else ""
