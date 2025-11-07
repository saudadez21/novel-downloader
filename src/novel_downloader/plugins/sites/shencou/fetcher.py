#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.shencou.fetcher
----------------------------------------------

"""

from pathlib import Path
from typing import Any, Literal

from novel_downloader.infra.http_defaults import IMAGE_HEADERS
from novel_downloader.libs.filesystem import img_name, write_file
from novel_downloader.plugins.base.fetcher import GenericFetcher
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class ShencouFetcher(GenericFetcher):
    """
    A session class for interacting with the 神凑轻小说 (www.shencou.com) novel.
    """

    site_name: str = "shencou"

    BOOK_ID_REPLACEMENTS = [("-", "/")]

    HAS_SEPARATE_CATALOG: bool = True
    BOOK_INFO_URL = "https://www.shencou.com/books/read_{book_id}.html"
    BOOK_CATALOG_URL = "https://www.shencou.com/read/{book_id}/index.html"
    CHAPTER_URL = "https://www.shencou.com/read/{book_id}/{chapter_id}.html"

    @classmethod
    def book_info_url(cls, **kwargs: Any) -> str:
        if not cls.BOOK_INFO_URL:
            raise NotImplementedError(f"{cls.__name__}.BOOK_INFO_URL not set")
        book_id = kwargs["book_id"]
        clean_id = book_id.rsplit("/", 1)[-1]
        return cls.BOOK_INFO_URL.format(book_id=clean_id)

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
            resp = await self.session.get(url, headers=IMAGE_HEADERS)
        except Exception as e:
            self.logger.warning(
                "Image request failed (site=shencou) %s: %s",
                url,
                e,
            )
            return None

        if not resp.ok:
            self.logger.warning(
                "Image request failed (site=shencou) %s: HTTP %s",
                url,
                resp.status,
            )
            return None
        if resp.content.startswith(b"<html"):
            self.logger.warning("Non-image content for %s (site=shencou)", url)
            return None

        write_file(content=resp.content, filepath=save_path, on_exist="overwrite")
        self.logger.debug("Saved image: %s <- %s", save_path, url)
        return save_path
