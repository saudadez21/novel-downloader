#!/usr/bin/env python3
"""
novel_downloader.core.exporters.linovelib.main_exporter
-------------------------------------------------------

"""

from collections.abc import Mapping
from typing import Any

from novel_downloader.core.exporters.base import BaseExporter
from novel_downloader.models import ExporterConfig
from novel_downloader.utils.chapter_storage import ChapterStorage

from .txt import linovelib_export_as_txt


class LinovelibExporter(BaseExporter):
    """"""

    def __init__(
        self,
        config: ExporterConfig,
    ):
        """
        Initialize the linovelib exporter.

        :param config: A ExporterConfig object that defines
                        save paths, formats, and options.
        """
        super().__init__(config, "linovelib")
        self._chapter_storage_cache: dict[str, list[ChapterStorage]] = {}
        self._chap_folders: list[str] = ["chapters"]

    def export_as_txt(self, book_id: str) -> None:
        """
        Compile and export a novel as a single .txt file.

        :param book_id: The book identifier (used to locate raw data)
        """
        self._init_chapter_storages(book_id)
        return linovelib_export_as_txt(self, book_id)

    def export_as_epub(self, book_id: str) -> None:
        """
        Persist the assembled book as a EPUB (.epub) file.

        :param book_id: The book identifier.
        :raises NotImplementedError: If the method is not overridden.
        """
        try:
            from .epub import (
                export_by_volume,
                export_whole_book,
            )
        except ImportError as err:
            raise NotImplementedError(
                "EPUB export not supported. Please install 'ebooklib'"
            ) from err

        self._init_chapter_storages(book_id)

        exporters = {
            "volume": export_by_volume,
            "book": export_whole_book,
        }
        try:
            export_fn = exporters[self._config.split_mode]
        except KeyError as err:
            raise ValueError(
                f"Unsupported split_mode: {self._config.split_mode!r}"
            ) from err
        return export_fn(self, book_id)

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
