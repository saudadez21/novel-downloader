#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.novelpia.fetcher
-----------------------------------------------
"""

import asyncio
import json
import time
from typing import Any

from novel_downloader.plugins.base.fetcher import BaseFetcher
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class NovelpiaFetcher(BaseFetcher):
    """
    A session class for interacting with the ノベルピア (novelpia.jp) novel.
    """

    site_name: str = "novelpia"

    BOOK_INFO_URL = "https://novelpia.jp/proc/novel"
    BOOK_CATALOG_URL = "https://novelpia.jp/proc/episode_list"
    CHAPTER_URL = "https://novelpia.jp/proc/viewer_data/{chapter_id}"

    async def get_book_info(
        self,
        book_id: str,
        **kwargs: Any,
    ) -> list[str]:
        payload: dict[str, str] = {
            "cmd": "get_novel",
            "novel_no": book_id,
            "mem_nick": "HATI",
            "_": str(int(time.time() * 1000)),
        }
        resp = await self.session.get(self.BOOK_INFO_URL, params=payload, **kwargs)
        if not resp.ok:
            raise ConnectionError(
                f"Book info request failed: {self.BOOK_INFO_URL}, status={resp.status}"
            )

        try:
            info = resp.json()
        except Exception as exc:
            raise RuntimeError(
                f"Book info JSON parse failed for {book_id}: {exc}"
            ) from exc

        results: list[str] = [json.dumps(info)]

        chap_count: int = info.get("novel", {}).get("count_book", 0)
        page_size = 20
        total_pages = (chap_count + page_size - 1) // page_size

        async def fetch_page(idx: int) -> str:
            payload = {"novel_no": book_id, "page": str(idx)}
            resp = await self.session.post(
                self.BOOK_CATALOG_URL, data=payload, **kwargs
            )
            if not resp.ok:
                raise ConnectionError(
                    f"Book catalog page {idx} failed, status={resp.status}"
                )
            return resp.text

        pages = await asyncio.gather(*[fetch_page(idx) for idx in range(total_pages)])
        results.extend(pages)
        return results

    async def get_book_chapter(
        self,
        book_id: str,
        chapter_id: str,
        **kwargs: Any,
    ) -> list[str]:
        url = self.CHAPTER_URL.format(chapter_id=chapter_id)
        data = {"size": "14"}

        resp = await self.session.post(url, data=data, **kwargs)
        if not resp.ok:
            raise ConnectionError(
                f"Book chapter request failed: {url}, status={resp.status}"
            )

        return [resp.text]
