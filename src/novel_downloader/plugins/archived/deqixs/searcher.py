#!/usr/bin/env python3
"""
novel_downloader.plugins.archived.deqixs.searcher
-------------------------------------------------

"""

import logging

from lxml import html
from novel_downloader.plugins.base.searcher import BaseSearcher
from novel_downloader.schemas import SearchResult

logger = logging.getLogger(__name__)


class DeqixsSearcher(BaseSearcher):
    site_name = "deqixs"
    priority = 20
    BASE_URL = "https://www.deqixs.com"
    SEARCH_URL = "https://www.deqixs.com/tag/"

    @classmethod
    async def _fetch_html(cls, keyword: str) -> str:
        params = {"key": keyword}
        try:
            async with cls._http_get(cls.SEARCH_URL, params=params) as resp:
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
        rows = doc.xpath("//div[@class='container']/div[@class='item']")
        results: list[SearchResult] = []

        for idx, row in enumerate(rows):
            if limit is not None and idx >= limit:
                break

            href = row.xpath(".//h3/a/@href")[0]
            book_id = href.strip("/ ").split("/")[-1]
            if not book_id:
                continue
            book_url = cls.BASE_URL + href
            img_src = row.xpath(".//a/img/@src")[0]
            cover_url = "https:" + img_src if img_src.startswith("//") else img_src
            title = row.xpath(".//h3/a/text()")[0].strip()

            author_text = row.xpath(".//p[2]/a/text()")[0]
            author = author_text.replace("作者：", "").strip()

            spans = row.xpath(".//p[1]/span/text()")
            word_count = spans[2].strip() if len(spans) > 2 else ""

            # Extract latest chapter and update date
            first_li = row.xpath(".//ul/li")[0]
            update_date = first_li.xpath("./i/text()")[0].strip()
            latest_chapter = first_li.xpath("./a/text()")[0].strip()

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
