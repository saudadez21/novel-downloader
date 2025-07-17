#!/usr/bin/env python3
"""
novel_downloader.core.exporters.common.main_exporter
----------------------------------------------------

This module implements the `CommonExporter` class, a concrete exporter for handling
novel data. It defines the logic to compile, structure, and export novel content
in plain text format based on the platform's metadata and chapter files.
"""

from novel_downloader.core.exporters.base import BaseExporter

from .txt import common_export_as_txt


class CommonExporter(BaseExporter):
    """
    CommonExporter is a exporter that processes and exports novels.
    It extends the BaseExporter interface and provides
    logic for exporting full novels as plain text (.txt) files
    and EPUB (.epub) files.
    """

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
