#!/usr/bin/env python3
"""
novel_downloader.core.savers.common.main_saver
----------------------------------------------

This module implements the `QidianSaver` class, a concrete saver for handling
novel data from Qidian (起点中文网). It defines the logic to compile, structure,
and export novel content in plain text format based on the platform's metadata
and chapter files.
"""

from collections.abc import Mapping
from typing import Any

from novel_downloader.config.models import SaverConfig
from novel_downloader.utils.chapter_storage import ChapterStorage

from ..base import BaseSaver
from .txt import common_save_as_txt


class CommonSaver(BaseSaver):
    """
    CommonSaver is a saver that processes and exports novels.
    It extends the BaseSaver interface and provides
    logic for exporting full novels as plain text (.txt) files.
    """

    def __init__(
        self,
        config: SaverConfig,
        site: str,
        chap_folders: list[str] | None = None,
    ):
        """
        Initialize the common saver with site information.

        :param config: A SaverConfig object that defines
                        save paths, formats, and options.
        :param site: Identifier for the site the saver is handling.
        """
        super().__init__(config)
        self._site = site
        self._raw_data_dir = self._base_raw_data_dir / site
        self._cache_dir = self._base_cache_dir / site
        self._chapter_storage_cache: dict[str, list[ChapterStorage]] = {}
        self._chap_folders: list[str] = chap_folders or ["chapters"]

    def save_as_txt(self, book_id: str) -> None:
        """
        Compile and save a complete novel as a single .txt file.

        Processing steps:
            1. Load book metadata from `book_info.json`, including title,
               author, summary, and chapter structure.
            2. Iterate through all volumes and chapters, appending each
               volume/chapter title and content.
            3. Combine metadata and content into a final formatted text.
            4. Save the final result to the output directory using the
               configured filename template.

        :param book_id: The book identifier (used to locate raw data)
        """
        self._init_chapter_storages(book_id)
        return common_save_as_txt(self, book_id)

    def save_as_epub(self, book_id: str) -> None:
        """
        Persist the assembled book as a EPUB (.epub) file.

        :param book_id: The book identifier.
        :raises NotImplementedError: If the method is not overridden.
        """
        try:
            from .epub import common_save_as_epub
        except ImportError as err:
            raise NotImplementedError(
                "EPUB export not supported. Please install 'ebooklib'"
            ) from err

        self._init_chapter_storages(book_id)
        return common_save_as_epub(self, book_id)

    @property
    def site(self) -> str:
        """
        Get the site identifier.

        :return: The site string.
        """
        return self._site

    @site.setter
    def site(self, value: str) -> None:
        """
        Set the site identifier.

        :param value: New site string to set.
        """
        self._site = value

    def _get_chapter(
        self,
        book_id: str,
        chap_id: str,
    ) -> Mapping[str, Any]:
        for storage in self._chapter_storage_cache[book_id]:
            data = storage.get(chap_id)
            if data:
                return data
        return {}

    def _init_chapter_storages(self, book_id: str) -> None:
        raw_base = self._raw_data_dir / book_id
        self._chapter_storage_cache[book_id] = [
            ChapterStorage(
                raw_base=raw_base,
                namespace=ns,
                backend_type=self._config.storage_backend,
            )
            for ns in self._chap_folders
        ]
