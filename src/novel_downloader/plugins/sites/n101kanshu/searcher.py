#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.n101kanshu.searcher
--------------------------------------------------
"""

import logging

from lxml import html
from novel_downloader.plugins.base.searcher import BaseSearcher
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import SearchResult

logger = logging.getLogger(__name__)


@registrar.register_searcher()
class N101kanshuSearcher(BaseSearcher):
    site_name = "n101kanshu"
    priority = 20
    BASE_URL = "https://101kanshu.com/"
    SEARCH_URL = "https://101kanshu.com/search"

    async def _fetch_html(self, keyword: str) -> str:
        data = {"searchkey": keyword, "searchtype": "all"}
        try:
            async with self.session.post(self.SEARCH_URL, data=data) as resp:
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
        rows = doc.xpath("//ul[@id='article_list_content']/li")
        results: list[SearchResult] = []
        count = 0

        for row in rows:
            book_url = self._first_str(row.xpath(".//a[@class='imgbox']/@href"))
            if not book_url:
                continue

            if limit is not None and count > limit:
                break

            book_id = book_url.rstrip("/").rsplit("/", 1)[-1].split(".", 1)[0]
            cover_url = self._first_str(
                row.xpath(".//img/@data-src")
            ) or self._first_str(row.xpath(".//img/@src"))
            if cover_url:
                cover_url = self._abs_url(cover_url)

            title = self._join_strs(row.xpath(".//div[@class='newnav']//h3//a//text()"))
            author = self._first_str(
                row.xpath(".//div[@class='labelbox']/label[1]/text()")
            )
            latest_chapter = self._first_str(
                row.xpath(".//div[@class='zxzj']//a/text()")
            )
            count += 1

            results.append(
                SearchResult(
                    site=self.site_name,
                    book_id=book_id,
                    book_url=book_url,
                    cover_url=cover_url,
                    title=title,
                    author=author,
                    latest_chapter=latest_chapter,
                    update_date="-",
                    word_count="-",
                    priority=self.priority + count,
                )
            )
        return results
