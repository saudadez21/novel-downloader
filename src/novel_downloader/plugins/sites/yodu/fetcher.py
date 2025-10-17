#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.yodu.fetcher
-------------------------------------------

"""

from pathlib import Path
from typing import Literal

from novel_downloader.infra.http_defaults import IMAGE_HEADERS
from novel_downloader.libs.filesystem import img_name, write_file
from novel_downloader.plugins.base.fetcher import GenericSession
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class YoduSession(GenericSession):
    """
    A session class for interacting with the 有度中文网 (www.yodu.org) novel.
    """

    site_name: str = "yodu"

    BASE_URL = "https://www.yodu.org"
    BOOK_INFO_URL = "https://www.yodu.org/book/{book_id}/"

    USE_PAGINATED_CHAPTER = True

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
        on_exist: Literal["overwrite", "skip"],
    ) -> None:
        save_path = folder / img_name(url)

        if save_path.exists() and on_exist == "skip":
            self.logger.debug("Skip existing image: %s", save_path)
            return

        try:
            async with await self.get(url, headers=IMAGE_HEADERS, ssl=False) as resp:
                resp.raise_for_status()
                data = await resp.read()
        except Exception as e:
            self.logger.warning("Failed %s: %s", url, e)
            return

        write_file(content=data, filepath=save_path, on_exist="overwrite")
        self.logger.debug("Saved image: %s <- %s", save_path, url)
