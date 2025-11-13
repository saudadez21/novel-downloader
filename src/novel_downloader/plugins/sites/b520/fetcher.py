#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.b520.fetcher
-------------------------------------------

"""

import logging
from pathlib import Path
from typing import Any, Literal

from novel_downloader.infra.http_defaults import IMAGE_HEADERS
from novel_downloader.libs.filesystem import image_filename, write_file
from novel_downloader.plugins.base.fetcher import BaseFetcher
from novel_downloader.plugins.registry import registrar

_IMG_HEADERS = IMAGE_HEADERS.copy()
_IMG_HEADERS["Referer"] = "http://www.b520.cc/"
logger = logging.getLogger(__name__)


@registrar.register_fetcher()
class B520Fetcher(BaseFetcher):
    """
    A session class for interacting with the 笔趣阁 (www.b520.cc) novel.
    """

    site_name: str = "b520"

    BOOK_INFO_URL = "http://www.b520.cc/{book_id}/"
    CHAPTER_URL = "http://www.b520.cc/{book_id}/{chapter_id}.html"

    async def fetch_book_info(
        self,
        book_id: str,
        **kwargs: Any,
    ) -> list[str]:
        headers = {
            **self.headers,
            "Referer": "http://www.b520.cc/",
        }
        url = self.book_info_url(book_id=book_id)
        return [await self.fetch(url, headers=headers, **kwargs)]

    async def fetch_chapter_content(
        self,
        book_id: str,
        chapter_id: str,
        **kwargs: Any,
    ) -> list[str]:
        headers = {
            **self.headers,
            "Referer": "http://www.b520.cc/",
        }
        url = self.chapter_url(book_id=book_id, chapter_id=chapter_id)
        return [await self.fetch(url, headers=headers, encoding="gbk", **kwargs)]

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
            logger.debug("b520 image: skip existing %s", save_path)
            return save_path

        try:
            resp = await self.session.get(url, headers=_IMG_HEADERS)
        except Exception as e:
            logger.warning(
                "Image request failed (site=b520) %s: %s",
                url,
                e,
            )
            return None

        if not resp.ok:
            logger.warning(
                "Image request failed (site=b520) %s: HTTP %s",
                url,
                resp.status,
            )
            return None

        write_file(content=resp.content, filepath=save_path, on_exist="overwrite")
        logger.debug("b520 image: saved %s <- %s", save_path, url)
        return save_path

    @classmethod
    def book_info_url(cls, book_id: str) -> str:
        return cls.BOOK_INFO_URL.format(book_id=book_id)

    @classmethod
    def chapter_url(cls, book_id: str, chapter_id: str) -> str:
        return cls.CHAPTER_URL.format(book_id=book_id, chapter_id=chapter_id)
