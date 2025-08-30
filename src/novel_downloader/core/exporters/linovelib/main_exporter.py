#!/usr/bin/env python3
"""
novel_downloader.core.exporters.linovelib.main_exporter
-------------------------------------------------------

Exporter implementation for Linovelib novels, supporting TXT and EPUB outputs.
"""

from pathlib import Path

from novel_downloader.core.exporters.base import BaseExporter
from novel_downloader.core.exporters.registry import register_exporter
from novel_downloader.models import ExporterConfig

from .epub import (
    export_by_volume,
    export_whole_book,
)
from .txt import linovelib_export_as_txt


@register_exporter(site_keys=["linovelib"])
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

    def export_as_txt(self, book_id: str) -> Path | None:
        """
        Compile and export a novel as a single .txt file.

        :param book_id: The book identifier (used to locate raw data)
        """
        self._init_chapter_storages(book_id)
        return linovelib_export_as_txt(self, book_id)

    def export_as_epub(self, book_id: str) -> Path | None:
        """
        Persist the assembled book as a EPUB (.epub) file.

        :param book_id: The book identifier.
        :raises NotImplementedError: If the method is not overridden.
        """
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
