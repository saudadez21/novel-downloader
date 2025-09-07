#!/usr/bin/env python3
"""
novel_downloader.core.interfaces.exporter
-----------------------------------------

Protocol defining the interface for exporting books to text, EPUB, and other formats.
"""

import types
from pathlib import Path
from typing import Protocol, Self, runtime_checkable


@runtime_checkable
class ExporterProtocol(Protocol):
    def export(self, book_id: str) -> dict[str, Path]:
        """
        Export the book in the formats specified in config.
        If a method is not implemented or fails, log the error and continue.

        :param book_id: The book identifier (used for filename, lookup, etc.)
        """
        ...

    def export_as_txt(self, book_id: str) -> Path | None:
        """
        Persist the assembled book as a .txt file.

        :param book_id: The book identifier (used for filename or lookup).
        """
        ...

    def export_as_epub(self, book_id: str) -> Path | None:
        """
        Optional: Persist the assembled book as an .epub file.

        :param book_id: The book identifier.
        """
        ...

    def export_as_md(self, book_id: str) -> Path | None:
        """
        Optional: Persist the assembled book as a Markdown (.md) file.

        :param book_id: The book identifier.
        """
        ...

    def export_as_pdf(self, book_id: str) -> Path | None:
        """
        Optional: Persist the assembled book as a PDF file.

        :param book_id: The book identifier.
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
