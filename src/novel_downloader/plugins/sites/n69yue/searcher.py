#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.n69yue.searcher
----------------------------------------------
"""

import json
import logging

from novel_downloader.infra.paths import N69YUE_MAP_PATH
from novel_downloader.plugins.base.searcher import BaseSearcher
from novel_downloader.plugins.searching import register_searcher
from novel_downloader.schemas import SearchResult

logger = logging.getLogger(__name__)


@register_searcher()
class N69yueSearcher(BaseSearcher):
    site_name = "n69yue"
    priority = 20
    BASE_URL = "https://www.69yue.top/"
    SEARCH_URL = "https://www.69yue.top/api/search"
    SEARCH_PAGE_URL = "https://www.69yue.top/search.html"

    _FONT_MAP: dict[str, str] = {}

    @classmethod
    async def _fetch_html(cls, keyword: str) -> str:
        data = {"q": keyword}
        headers = {
            "Origin": "https://www.69yue.top",
            "Referer": cls._build_url(cls.SEARCH_PAGE_URL, data),
        }
        try:
            async with cls._http_post(
                cls.SEARCH_URL, data=data, headers=headers
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
        data = json.loads(html_str)
        rows = data.get("results", [])
        results: list[SearchResult] = []
        count = 0

        for row in rows:
            infourl = row.get("infourl")
            if not infourl or "69shuba" in infourl:
                continue

            if limit is not None and count >= limit:
                break

            # '/articlecategroy/1a6l.html' -> "1a6l"
            book_id = infourl.rsplit("/", 1)[-1].split(".")[0]
            book_url = cls._abs_url(infourl)
            title = cls._map_fonts(row.get("title", "").strip())
            author = cls._map_fonts(row.get("author", "").strip())
            update_date = row.get("updateTime", "-").strip()

            prio = cls.priority + count
            count += 1

            results.append(
                SearchResult(
                    site=cls.site_name,
                    book_id=book_id,
                    book_url=book_url,
                    cover_url="",
                    title=title,
                    author=author,
                    latest_chapter="-",
                    update_date=update_date,
                    word_count="-",
                    priority=prio,
                )
            )
        return results

    @classmethod
    def _map_fonts(cls, text: str) -> str:
        """
        Apply font mapping to the input text.
        """
        if not cls._FONT_MAP:
            cls._FONT_MAP = json.loads(N69YUE_MAP_PATH.read_text(encoding="utf-8"))

        return "".join(cls._FONT_MAP.get(c, c) for c in text)
