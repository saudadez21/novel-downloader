#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.aaatxt.searcher
----------------------------------------------

"""

import logging

from lxml import html

from novel_downloader.plugins.base.searcher import BaseSearcher
from novel_downloader.plugins.searching import register_searcher
from novel_downloader.schemas import SearchResult

logger = logging.getLogger(__name__)


@register_searcher()
class AaatxtSearcher(BaseSearcher):
    site_name = "aaatxt"
    priority = 500
    SEARCH_URL = "http://www.aaatxt.com/search.php"

    @classmethod
    async def _fetch_html(cls, keyword: str) -> str:
        # gbk / gb2312
        params = {
            "keyword": cls._quote(keyword, encoding="gb2312", errors="replace"),
            "submit": cls._quote("搜 索", encoding="gb2312", errors="replace"),
        }
        full_url = cls._build_url(cls.SEARCH_URL, params)  # need build manually
        headers = {
            "Host": "www.aaatxt.com",
            "Referer": "http://www.aaatxt.com/",
        }
        try:
            async with cls._http_get(full_url, headers=headers) as resp:
                resp.raise_for_status()
                return await cls._response_to_str(resp, "gb2312")
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
        rows = doc.xpath("//div[@class='sort']//div[@class='list']/table")
        results: list[SearchResult] = []

        for idx, row in enumerate(rows):
            href = cls._first_str(row.xpath(".//td[@class='name']/h3/a/@href"))
            if not href:
                continue

            if limit is not None and idx >= limit:
                break

            book_id = href.split("/")[-1].split(".")[0]
            book_url = cls._abs_url(href)

            cover_rel = cls._first_str(row.xpath(".//td[@class='cover']/a/img/@src"))
            cover_url = cls._abs_url(cover_rel) if cover_rel else ""

            title = cls._first_str(row.xpath(".//td[@class='name']/h3/a//text()"))

            size_text = row.xpath("string(.//td[@class='size'])")
            size_norm = size_text.replace("\u00a0", " ").replace("&nbsp;", " ").strip()
            tokens = [t for t in size_norm.split() if t]

            word_count = "-"
            author = "-"
            for tok in tokens:
                if tok.startswith("大小:"):
                    word_count = tok.split(":", 1)[1].strip()
                elif tok.startswith("上传:"):
                    author = tok.split(":", 1)[1].strip()

            intro_text = row.xpath("string(.//td[@class='intro'])")
            intro_norm = intro_text.replace("\u00a0", " ").replace("&nbsp;", " ")
            update_date = "-"
            for marker in ("更新:", "更新："):
                if marker in intro_norm:
                    tail = intro_norm.split(marker, 1)[1].strip()
                    update_date = tail.split()[0] if tail else "-"
                    break

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
                    word_count=word_count,
                    priority=cls.priority + idx,
                )
            )
        return results
