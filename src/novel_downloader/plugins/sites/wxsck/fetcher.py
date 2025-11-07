#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.wxsck.fetcher
--------------------------------------------
"""

from pathlib import Path
from typing import Any, Literal

from novel_downloader.infra.http_defaults import IMAGE_HEADERS
from novel_downloader.libs.filesystem import img_name, write_file
from novel_downloader.plugins.base.fetcher import BaseFetcher
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class WxsckFetcher(BaseFetcher):
    """
    A session class for interacting with the 万相书城 (wxsck.com) novel.
    """

    site_name: str = "wxsck"

    BASE_URL = "https://wxsck.com"
    BOOK_INFO_URL = "https://wxsck.com/book/{book_id}/"

    async def get_book_info(self, book_id: str, **kwargs: Any) -> list[str]:
        info_url = self.BOOK_INFO_URL.format(book_id=book_id)
        return [await self.fetch(info_url, allow_redirects=True, **kwargs)]

    async def get_book_chapter(
        self, book_id: str, chapter_id: str, **kwargs: Any
    ) -> list[str]:
        origin = self.BASE_URL
        pages: list[str] = []
        idx = 1
        suffix = self.relative_chapter_url(book_id, chapter_id, idx)

        while True:
            html = await self.fetch(origin + suffix, allow_redirects=True, **kwargs)
            pages.append(html)
            idx += 1
            suffix = self.relative_chapter_url(book_id, chapter_id, idx)
            if suffix not in html:
                break
            await self._sleep()

        return pages

    @classmethod
    def relative_chapter_url(cls, book_id: str, chapter_id: str, idx: int) -> str:
        return (
            f"/book/{book_id}/{chapter_id}_{idx}.html"
            if idx > 1
            else f"/book/{book_id}/{chapter_id}.html"
        )

    async def _download_one_image(
        self,
        url: str,
        folder: Path,
        *,
        name: str | None = None,
        on_exist: Literal["overwrite", "skip"],
    ) -> Path | None:
        save_path = folder / img_name(url, name=name)

        if save_path.exists() and on_exist == "skip":
            self.logger.debug("Skip existing image: %s", save_path)
            return save_path

        try:
            resp = await self.session.get(
                url, headers=IMAGE_HEADERS, allow_redirects=True
            )
        except Exception as e:
            self.logger.warning(
                "Image request failed (site=wxsck) %s: %s",
                url,
                e,
            )
            return None

        if not resp.ok:
            self.logger.warning(
                "Image request failed (site=wxsck) %s: HTTP %s",
                url,
                resp.status,
            )
            return None

        write_file(content=resp.content, filepath=save_path, on_exist="overwrite")
        self.logger.debug("Saved image: %s <- %s", save_path, url)
        return save_path
