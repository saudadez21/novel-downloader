#!/usr/bin/env python3
"""
novel_downloader.core.exporters.common.main_exporter
----------------------------------------------------

This module implements the `CommonExporter` class, a concrete exporter for handling
novel data. It defines the logic to compile, structure, and export novel content
in plain text format based on the platform's metadata and chapter files.
"""

from collections.abc import Mapping
from typing import Any

from novel_downloader.core.exporters.base import BaseExporter
from novel_downloader.models import ExporterConfig
from novel_downloader.utils.chapter_storage import ChapterStorage

from .txt import common_export_as_txt


class CommonExporter(BaseExporter):
    """
    CommonExporter is a exporter that processes and exports novels.
    It extends the BaseExporter interface and provides
    logic for exporting full novels as plain text (.txt) files
    and EPUB (.epub) files.
    """

    def __init__(
        self,
        config: ExporterConfig,
        site: str,
        chap_folders: list[str] | None = None,
    ):
        super().__init__(config, site)
        self._chapter_storage_cache: dict[str, list[ChapterStorage]] = {}
        self._chap_folders: list[str] = chap_folders or ["chapters"]

    def export_as_txt(self, book_id: str) -> None:
        """
        Compile and export a complete novel as a single .txt file.

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
        return common_export_as_txt(self, book_id)

    def export_as_epub(self, book_id: str) -> None:
        """
        Persist the assembled book as a EPUB (.epub) file.

        :param book_id: The book identifier.
        :raises NotImplementedError: If the method is not overridden.
        """
        try:
            from .epub import common_export_as_epub
        except ImportError as err:
            raise NotImplementedError(
                "EPUB export not supported. Please install 'ebooklib'"
            ) from err

        self._init_chapter_storages(book_id)
        return common_export_as_epub(self, book_id)

    @property
    def site(self) -> str:
        """
        Get the site identifier.

        :return: The site string.
        """
        return self._site

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
        if book_id in self._chapter_storage_cache:
            return
        raw_base = self._raw_data_dir / book_id
        self._chapter_storage_cache[book_id] = [
            ChapterStorage(
                raw_base=raw_base,
                namespace=ns,
                backend_type=self._config.storage_backend,
            )
            for ns in self._chap_folders
        ]

    def _on_close(self) -> None:
        """
        Close all ChapterStorage connections in the cache.
        """
        for storages in self._chapter_storage_cache.values():
            for storage in storages:
                try:
                    storage.close()
                except Exception as e:
                    self.logger.warning("Failed to close storage %s: %s", storage, e)
        self._chapter_storage_cache.clear()
