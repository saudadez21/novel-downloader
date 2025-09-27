#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.linovelib.fetcher
------------------------------------------------

"""

import re
from pathlib import Path
from typing import Any, Literal

from novel_downloader.infra.http_defaults import DEFAULT_HEADERS, DEFAULT_IMAGE_SUFFIX
from novel_downloader.libs.filesystem import write_file
from novel_downloader.plugins.base.fetcher import BaseSession
from novel_downloader.plugins.registry import registrar

_IMG_HEADERS = DEFAULT_HEADERS.copy()
_IMG_HEADERS["Referer"] = "https://www.linovelib.com/"


@registrar.register_fetcher()
class LinovelibSession(BaseSession):
    """
    A session class for interacting with 哔哩轻小说 (www.linovelib.com) novel.
    """

    site_name: str = "linovelib"

    BASE_URL = "https://www.linovelib.com"
    BOOK_INFO_URL = "https://www.linovelib.com/novel/{book_id}.html"
    BOOK_CATALOG_UTL = "https://www.linovelib.com/novel/{book_id}/catalog"
    BOOK_VOL_URL = "https://www.linovelib.com/novel/{book_id}/{vol_id}.html"
    CHAPTER_URL = "https://www.linovelib.com/novel/{book_id}/{chapter_id}.html"

    _VOL_ID_PATTERN: re.Pattern[str] = re.compile(r"/novel/\d+/(vol_\d+)\.html")

    async def get_book_info(
        self,
        book_id: str,
        **kwargs: Any,
    ) -> list[str]:
        """
        Fetch the raw HTML of the book info page.

        Order: [info, vol1_html, ..., volN_html]

        :param book_id: The book identifier.
        :return: The page content as string list.
        """
        url = self.book_info_url(book_id=book_id)
        info_html = await self.fetch(url, **kwargs)

        vol_ids = self._extract_vol_ids(info_html)
        vol_ids.reverse()
        if not vol_ids:
            url = self.catalog_url(book_id=book_id)
            catalog_html = await self.fetch(url, **kwargs)
            vol_ids = self._extract_vol_ids(catalog_html)

        vol_htmls = []
        for vol_id in vol_ids:
            await self._sleep()
            html = await self.get_book_volume(book_id, vol_id, **kwargs)
            if html:
                vol_htmls.append(html)

        return [info_html] + vol_htmls

    async def get_book_volume(
        self,
        book_id: str,
        vol_id: str,
        **kwargs: Any,
    ) -> str:
        """
        Fetch the HTML content of a specific volume.

        :param book_id: The book identifier.
        :param vol_id: The volume identifier.
        :return: The volume content as a string.
        """
        url = self.volume_url(book_id=book_id, vol_id=vol_id)
        return await self.fetch(url, **kwargs)

    async def get_book_chapter(
        self,
        book_id: str,
        chapter_id: str,
        **kwargs: Any,
    ) -> list[str]:
        """
        Fetch the raw HTML of a single chapter asynchronously.

        Order: [page1, ..., pageN]

        :param book_id: The book identifier.
        :param chapter_id: The chapter identifier.
        :return: The page content as string list.
        """
        origin = self.BASE_URL.rstrip("/")
        pages: list[str] = []
        idx = 1
        suffix = self.relative_chapter_url(book_id, chapter_id, idx)

        while True:
            html = await self.fetch(origin + suffix, **kwargs)
            pages.append(html)
            idx += 1
            suffix = self.relative_chapter_url(book_id, chapter_id, idx)
            if suffix not in html:
                break
            await self._sleep()

        return pages

    @classmethod
    def book_info_url(cls, book_id: str) -> str:
        """
        Construct the URL for fetching a book's info page.

        :param book_id: The identifier of the book.
        :return: Fully qualified URL for the book info page.
        """
        return cls.BOOK_INFO_URL.format(book_id=book_id)

    @classmethod
    def catalog_url(cls, book_id: str) -> str:
        """
        Construct the URL for fetching a catalog page.

        :param book_id: The identifier of the book.
        :return: Fully qualified catalog URL.
        """
        return cls.BOOK_CATALOG_UTL.format(book_id=book_id)

    @classmethod
    def volume_url(cls, book_id: str, vol_id: str) -> str:
        """
        Construct the URL for fetching a specific volume.

        :param book_id: The identifier of the book.
        :param vol_id: The identifier of the volume.
        :return: Fully qualified volume URL.
        """
        return cls.BOOK_VOL_URL.format(book_id=book_id, vol_id=vol_id)

    @classmethod
    def chapter_url(cls, book_id: str, chapter_id: str) -> str:
        """
        Construct the URL for fetching a specific chapter.

        :param book_id: The identifier of the book.
        :param chapter_id: The identifier of the chapter.
        :return: Fully qualified chapter URL.
        """
        return cls.CHAPTER_URL.format(book_id=book_id, chapter_id=chapter_id)

    @classmethod
    def relative_chapter_url(cls, book_id: str, chapter_id: str, idx: int) -> str:
        """
        Return the relative URL path for a given chapter.
        """
        return (
            f"/novel/{book_id}/{chapter_id}.html"
            if idx == 1
            else f"/novel/{book_id}/{chapter_id}_{idx}.html"
        )

    def _extract_vol_ids(self, html_str: str) -> list[str]:
        """
        Extract volume IDs (like 'vol_12345') from the info HTML.

        :param html_str: Raw HTML of the info page.
        :return: List of volume ID strings.
        """
        # /novel/{book_id}/{vol_id}.html
        return self._VOL_ID_PATTERN.findall(html_str)

    async def _download_one_image(
        self,
        url: str,
        folder: Path,
        *,
        on_exist: Literal["overwrite", "skip", "rename"],
    ) -> None:
        """Download a single image."""
        async with self.session.get(url, headers=_IMG_HEADERS) as resp:
            save_path = self._build_filepath(
                url=url,
                folder=folder,
                default_suffix=DEFAULT_IMAGE_SUFFIX,
                on_exist=on_exist,
            )
            if save_path.exists() and on_exist == "skip":
                return

            resp.raise_for_status()
            write_file(
                content=await resp.read(),  # bytes
                filepath=save_path,
                on_exist=on_exist,
            )
            self.logger.debug("Saved image: %s <- %s", save_path, url)
