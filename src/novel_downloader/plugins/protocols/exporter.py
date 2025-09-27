#!/usr/bin/env python3
"""
novel_downloader.plugins.protocols.exporter
-------------------------------------------

Protocol defining the interface for exporting books to text, EPUB, and other formats.
"""

import types
from pathlib import Path
from typing import Protocol, Self

from novel_downloader.schemas import BookConfig


class ExporterProtocol(Protocol):
    def export(self, book: BookConfig) -> dict[str, Path]:
        """
        Export the book in the formats specified in config.
        If a method is not implemented or fails, log the error and continue.

        :param book: BookConfig with at least 'book_id'.
        """
        ...

    def export_as_txt(self, book: BookConfig) -> Path | None:
        """
        Persist the assembled book as a .txt file.

        :param book: BookConfig with at least 'book_id'.
        """
        ...

    def export_as_epub(self, book: BookConfig) -> Path | None:
        """
        Optional: Persist the assembled book as an .epub file.

        :param book: BookConfig with at least 'book_id'.
        """
        ...

    def export_as_md(self, book: BookConfig) -> Path | None:
        """
        Optional: Persist the assembled book as a Markdown (.md) file.

        :param book: BookConfig with at least 'book_id'.
        """
        ...

    def export_as_pdf(self, book: BookConfig) -> Path | None:
        """
        Optional: Persist the assembled book as a PDF file.

        :param book: BookConfig with at least 'book_id'.
        """
        ...

    def close(self) -> None:
        """
        Shutdown and clean up the exporter.
        """
        ...

    def __enter__(self) -> Self:
        ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        tb: types.TracebackType | None,
    ) -> None:
        ...
