#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.syosetu.fetcher
----------------------------------------------
"""

from pathlib import Path
from typing import Literal

from novel_downloader.infra.http_defaults import IMAGE_HEADERS
from novel_downloader.libs.filesystem import img_name, write_file
from novel_downloader.plugins.base.fetcher import GenericFetcher
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class SyosetuFetcher(GenericFetcher):
    """
    A session class for interacting with the 小説家になろう (syosetu.com) novel.
    """

    site_name: str = "syosetu"

    BASE_URL = "https://ncode.syosetu.com"
    CHAPTER_URL = "https://ncode.syosetu.com/{book_id}/{chapter_id}/"

    USE_PAGINATED_INFO = True

    @classmethod
    def relative_info_url(cls, book_id: str, idx: int) -> str:
        return f"/{book_id}/?p={idx}" if idx > 1 else f"/{book_id}/"

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
                "Image request failed (site=syosetu) %s: %s",
                url,
                e,
            )
            return None

        if not resp.ok:
            self.logger.warning(
                "Image request failed (site=syosetu) %s: HTTP %s",
                url,
                resp.status,
            )
            return None

        if not resp.content:
            self.logger.warning(
                "Empty response for image (site=syosetu): %s",
                url,
            )
            return None

        write_file(content=resp.content, filepath=save_path, on_exist="overwrite")
        self.logger.debug("Saved image: %s <- %s", save_path, url)
        return save_path
