#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.shencou.fetcher
----------------------------------------------

"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Literal

from novel_downloader.infra.http_defaults import IMAGE_HEADERS
from novel_downloader.libs.filesystem import image_filename, write_file
from novel_downloader.plugins.base.fetcher import BaseFetcher
from novel_downloader.plugins.registry import registrar

logger = logging.getLogger(__name__)


@registrar.register_fetcher()
class ShencouFetcher(BaseFetcher):
    """
    A session class for interacting with the 神凑轻小说 (www.shencou.com) novel.
    """

    site_name: str = "shencou"

    BOOK_INFO_URL = "https://www.shencou.com/books/read_{bid}.html"
    BOOK_CATALOG_URL = "https://www.shencou.com/read/{prefix}/{bid}/index.html"
    CHAPTER_URL = "https://www.shencou.com/read/{prefix}/{bid}/{cid}.html"

    async def fetch_book_info(
        self,
        book_id: str,
        **kwargs: Any,
    ) -> list[str]:
        prefix = self._compute_prefix(book_id)

        info_url = self.BOOK_INFO_URL.format(bid=book_id)
        catalog_url = self.BOOK_CATALOG_URL.format(prefix=prefix, bid=book_id)

        info_resp, catalog_resp = await asyncio.gather(
            self.fetch(info_url, **kwargs),
            self.fetch(catalog_url, **kwargs),
        )
        return [info_resp, catalog_resp]

    async def fetch_chapter_content(
        self,
        book_id: str,
        chapter_id: str,
        **kwargs: Any,
    ) -> list[str]:
        prefix = self._compute_prefix(book_id)
        url = self.CHAPTER_URL.format(prefix=prefix, bid=book_id, cid=chapter_id)
        return [await self.fetch(url, **kwargs)]

    @staticmethod
    def _compute_prefix(book_id: str) -> str:
        # prefix rule: IDs < 1000 placed in directory 0
        return "0" if len(book_id) <= 3 else book_id[:-3]

    async def _fetch_one_image(
        self,
        url: str,
        folder: Path,
        *,
        name: str | None = None,
        on_exist: Literal["overwrite", "skip"],
    ) -> Path | None:
        save_path = folder / image_filename(url, name=name)

        if save_path.exists() and on_exist == "skip":
            logger.debug("Skip existing image: %s", save_path)
            return save_path

        try:
            resp = await self.session.get(url, headers=IMAGE_HEADERS)
        except Exception as e:
            logger.warning(
                "Image request failed (site=shencou) %s: %s",
                url,
                e,
            )
            return None

        if not resp.ok:
            logger.warning(
                "Image request failed (site=shencou) %s: HTTP %s",
                url,
                resp.status,
            )
            return None
        if resp.content.startswith(b"<html"):
            logger.warning("Non-image content for %s (site=shencou)", url)
            return None

        write_file(content=resp.content, filepath=save_path, on_exist="overwrite")
        logger.debug("Saved image: %s <- %s", save_path, url)
        return save_path
