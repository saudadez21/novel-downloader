#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.dushu.fetcher
--------------------------------------------
"""

from pathlib import Path
from typing import Literal

from novel_downloader.infra.http_defaults import IMAGE_HEADERS
from novel_downloader.libs.filesystem import img_name, write_file
from novel_downloader.plugins.base.fetcher import GenericFetcher
from novel_downloader.plugins.registry import registrar

_IMG_HEADERS = IMAGE_HEADERS.copy()
_IMG_HEADERS["Referer"] = "https://www.dushu.com/"


@registrar.register_fetcher()
class DushuFetcher(GenericFetcher):
    """
    A session class for interacting with the 读书 (www.dushu.com) novel.
    """

    site_name: str = "dushu"

    BOOK_INFO_URL = "https://www.dushu.com/showbook/{book_id}/"
    CHAPTER_URL = "https://www.dushu.com/showbook/{book_id}/{chapter_id}.html"

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
            self.logger.debug("dushu image: skip existing %s", save_path)
            return save_path

        try:
            resp = await self.session.get(url, headers=_IMG_HEADERS)
        except Exception as e:
            self.logger.warning(
                "Image request failed (site=dushu) %s: %s",
                url,
                e,
            )
            return None

        if not resp.ok:
            self.logger.warning(
                "Image request failed (site=dushu) %s: HTTP %s",
                url,
                resp.status,
            )
            return None

        write_file(content=resp.content, filepath=save_path, on_exist="overwrite")
        self.logger.debug("dushu image: saved %s <- %s", save_path, url)
        return save_path
