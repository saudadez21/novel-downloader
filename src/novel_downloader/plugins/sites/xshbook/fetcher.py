#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.xshbook.fetcher
----------------------------------------------

"""

from pathlib import Path
from typing import Literal

from novel_downloader.infra.http_defaults import IMAGE_HEADERS
from novel_downloader.libs.filesystem import img_name, write_file
from novel_downloader.plugins.base.fetcher import GenericFetcher
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class XshbookFetcher(GenericFetcher):
    """
    A session class for interacting with the 小说虎 (www.xshbook.com) novel.
    """

    site_name: str = "xshbook"

    BOOK_ID_REPLACEMENTS = [("-", "/")]

    BOOK_INFO_URL = "https://www.xshbook.com/{book_id}/"
    CHAPTER_URL = "https://www.xshbook.com/{book_id}/{chapter_id}.html"

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
                url, allow_redirects=True, headers=IMAGE_HEADERS
            )
        except Exception as e:
            self.logger.warning(
                "Image request failed (site=xshbook) %s: %s",
                url,
                e,
            )
            return None

        if not resp.ok:
            self.logger.warning(
                "Image request failed (site=xshbook) %s: HTTP %s",
                url,
                resp.status,
            )
            return None

        if not resp.content:
            self.logger.warning(
                "Empty response for image (site=xshbook): %s",
                url,
            )
            return None

        write_file(content=resp.content, filepath=save_path, on_exist="overwrite")
        self.logger.debug("Saved image: %s <- %s", save_path, url)
        return save_path
