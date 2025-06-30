#!/usr/bin/env python3
"""
novel_downloader.core.exporters.base
------------------------------------

This module provides an abstract base class `BaseExporter` that defines
the common interface and reusable logic for saving assembled novel
content into various output formats.
"""

import abc
import logging
import types
from datetime import datetime
from pathlib import Path
from typing import Any, Self

from novel_downloader.core.interfaces import ExporterProtocol
from novel_downloader.models import ExporterConfig


class SafeDict(dict[str, Any]):
    def __missing__(self, key: str) -> str:
        return f"{{{key}}}"


class BaseExporter(ExporterProtocol, abc.ABC):
    """
    BaseExporter defines the interface and common structure for
    saving assembled book content into various formats
    such as TXT, EPUB, Markdown, or PDF.
    """

    def __init__(
        self,
        config: ExporterConfig,
        site: str,
    ):
        """
        Initialize the exporter with given configuration.

        :param config: A ExporterConfig object that defines
                        save paths, formats, and options.
        """
        self._config = config
        self._site = site

        self._cache_dir = Path(config.cache_dir) / site
        self._raw_data_dir = Path(config.raw_data_dir) / site
        self._output_dir = Path(config.output_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._output_dir.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger(f"{self.__class__.__name__}")

    def export(
        self,
        book_id: str,
    ) -> None:
        """
        Export the book in the formats specified in config.
        If a method is not implemented or fails, log the error and continue.

        :param book_id: The book identifier (used for filename, lookup, etc.)
        """
        TAG = "[Exporter]"
        actions = [
            ("make_txt", self.export_as_txt),
            ("make_epub", self.export_as_epub),
            ("make_md", self.export_as_md),
            ("make_pdf", self.export_as_pdf),
        ]

        for flag_name, export_method in actions:
            if getattr(self._config, flag_name, False):
                try:
                    self.logger.info(
                        "%s Attempting to export book_id '%s' as %s...",
                        TAG,
                        book_id,
                        flag_name,
                    )
                    export_method(book_id)
                    self.logger.info("%s Successfully saved as %s.", TAG, flag_name)
                except NotImplementedError as e:
                    self.logger.warning(
                        "%s Export method for %s not implemented: %s",
                        TAG,
                        flag_name,
                        str(e),
                    )
                except Exception as e:
                    self.logger.error(
                        "%s Error while saving as %s: %s", TAG, flag_name, str(e)
                    )
        return

    @abc.abstractmethod
    def export_as_txt(self, book_id: str) -> None:
        """
        Persist the assembled book as a .txt file.

        This method must be implemented by all subclasses.

        :param book_id: The book identifier (used for filename, lookup, etc.)
        """
        ...

    def export_as_epub(self, book_id: str) -> None:
        """
        Optional: Persist the assembled book as a EPUB (.epub) file.

        :param book_id: The book identifier.
        :raises NotImplementedError: If the method is not overridden.
        """
        raise NotImplementedError("EPUB export not supported by this Exporter.")

    def export_as_md(self, book_id: str) -> None:
        """
        Optional: Persist the assembled book as a Markdown file.

        :param book_id: The book identifier.
        :raises NotImplementedError: If the method is not overridden.
        """
        raise NotImplementedError("Markdown export not supported by this Exporter.")

    def export_as_pdf(self, book_id: str) -> None:
        """
        Optional: Persist the assembled book as a PDF file.

        :param book_id: The book identifier.
        :raises NotImplementedError: If the method is not overridden.
        """
        raise NotImplementedError("PDF export not supported by this Exporter.")

    def get_filename(
        self,
        *,
        title: str,
        author: str | None = None,
        ext: str = "txt",
        **extra_fields: str,
    ) -> str:
        """
        Generate a filename based on the configured template and metadata fields.

        :param title: Book title (required).
        :param author: Author name (optional).
        :param ext: File extension (e.g., "txt", "epub").
        :param extra_fields: Any additional fields used in the filename template.
        :return: Formatted filename with extension.
        """
        # Merge all fields with defaults
        context = SafeDict(title=title, author=author or "", **extra_fields)

        name = self.filename_template.format_map(context)

        if self._config.append_timestamp:
            name += f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        return f"{name}.{ext}"

    @property
    def output_dir(self) -> Path:
        """Access the output directory for saving files."""
        return self._output_dir

    @property
    def filename_template(self) -> str:
        """Access the filename template."""
        return self._config.filename_template

    def _on_close(self) -> None:
        """
        Hook method called at the beginning of close().
        Override in subclass if needed.
        """
        pass

    def close(self) -> None:
        """
        Shutdown and clean up the exporter.
        """
        self._on_close()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        tb: types.TracebackType | None,
    ) -> None:
        self.close()

    def __del__(self) -> None:
        self.close()
