#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.savers.base_saver
---------------------------------------

This module provides an abstract base class `BaseSaver` that defines the
common interface and reusable logic for saving assembled novel content
into various output formats.
"""

import abc
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from novel_downloader.config.models import SaverConfig
from novel_downloader.core.interfaces import SaverProtocol

logger = logging.getLogger(__name__)


class SafeDict(Dict[str, Any]):
    def __missing__(self, key: str) -> str:
        return "{{{}}}".format(key)


class BaseSaver(SaverProtocol, abc.ABC):
    """
    BaseSaver defines the interface and common structure for
    saving assembled book content into various formats
    such as TXT, EPUB, Markdown, or PDF.
    """

    def __init__(self, config: SaverConfig):
        """
        Initialize the saver with given configuration.

        :param config: A SaverConfig object that defines
                        save paths, formats, and options.
        """
        self._config = config

        self._raw_data_dir = Path(config.raw_data_dir)
        self._output_dir = Path(config.output_dir)
        self._raw_data_dir.mkdir(parents=True, exist_ok=True)
        self._output_dir.mkdir(parents=True, exist_ok=True)

        self._filename_template = config.filename_template

    def save(self, book_id: str) -> None:
        """
        Save the book in the formats specified in config.
        If a method is not implemented or fails, log the error and continue.

        :param book_id: The book identifier (used for filename, lookup, etc.)
        """
        TAG = "[Saver]"
        actions = [
            ("make_txt", self.save_as_txt),
            ("make_epub", self.save_as_epub),
            ("make_md", self.save_as_md),
            ("make_pdf", self.save_as_pdf),
        ]

        for flag_name, save_method in actions:
            if getattr(self._config, flag_name, False):
                try:
                    logger.info(
                        "%s Attempting to save book_id '%s' as %s...",
                        TAG,
                        book_id,
                        flag_name,
                    )
                    save_method(book_id)
                    logger.info("%s Successfully saved as %s.", TAG, flag_name)
                except NotImplementedError as e:
                    logger.warning(
                        "%s Save method for %s not implemented: %s",
                        TAG,
                        flag_name,
                        str(e),
                    )
                except Exception as e:
                    logger.error(
                        "%s Error while saving as %s: %s", TAG, flag_name, str(e)
                    )
        return

    @abc.abstractmethod
    def save_as_txt(self, book_id: str) -> None:
        """
        Persist the assembled book as a .txt file.

        This method must be implemented by all subclasses.

        :param book_id: The book identifier (used for filename, lookup, etc.)
        """
        ...

    def save_as_epub(self, book_id: str) -> None:
        """
        Optional: Persist the assembled book as a EPUB (.epub) file.

        :param book_id: The book identifier.
        :raises NotImplementedError: If the method is not overridden.
        """
        raise NotImplementedError("EPUB export not supported by this saver.")

    def save_as_md(self, book_id: str) -> None:
        """
        Optional: Persist the assembled book as a Markdown file.

        :param book_id: The book identifier.
        :raises NotImplementedError: If the method is not overridden.
        """
        raise NotImplementedError("Markdown export not supported by this saver.")

    def save_as_pdf(self, book_id: str) -> None:
        """
        Optional: Persist the assembled book as a PDF file.

        :param book_id: The book identifier.
        :raises NotImplementedError: If the method is not overridden.
        """
        raise NotImplementedError("PDF export not supported by this saver.")

    def get_filename(
        self,
        *,
        title: str,
        author: Optional[str] = None,
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

        name = self._filename_template.format_map(context)

        if self._config.append_timestamp:
            name += f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        return f"{name}.{ext}"

    @property
    def output_dir(self) -> Path:
        """Access the output directory for saving files."""
        return self._output_dir

    @property
    def raw_data_dir(self) -> Path:
        """Access the raw data directory."""
        return self._raw_data_dir

    @property
    def filename_template(self) -> str:
        """Access the filename template."""
        return self._filename_template
