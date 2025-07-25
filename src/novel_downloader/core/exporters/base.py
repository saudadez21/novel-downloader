#!/usr/bin/env python3
"""
novel_downloader.core.exporters.base
------------------------------------

This module provides an abstract base class `BaseExporter` that defines
the common interface and reusable logic for saving assembled novel
content into various output formats.
"""

import abc
import json
import logging
import types
from datetime import datetime
from pathlib import Path
from typing import Any, Self, cast

from novel_downloader.core.interfaces import ExporterProtocol
from novel_downloader.models import BookInfoDict, ChapterDict, ExporterConfig
from novel_downloader.utils import ChapterStorage


class SafeDict(dict[str, Any]):
    def __missing__(self, key: str) -> str:
        return f"{{{key}}}"


class BaseExporter(ExporterProtocol, abc.ABC):
    """
    BaseExporter defines the interface and common structure for
    saving assembled book content into various formats
    such as TXT, EPUB, Markdown, or PDF.
    """

    DEFAULT_SOURCE_ID = 0
    DEFAULT_PRIORITIES_MAP = {
        DEFAULT_SOURCE_ID: 0,
    }

    def __init__(
        self,
        config: ExporterConfig,
        site: str,
        priorities: dict[int, int] | None = None,
    ):
        """
        Initialize the exporter with given configuration.

        :param config: Exporter configuration settings.
        :param site: Identifier for the target website or source.
        :param priorities: Mapping of source_id to priority value.
                           Lower numbers indicate higher priority.
                           E.X. {0: 10, 1: 100} means source 0 is preferred.
        """
        self._config = config
        self._site = site
        self._priorities = priorities or self.DEFAULT_PRIORITIES_MAP
        self._storage_cache: dict[str, ChapterStorage] = {}

        self._raw_data_dir = Path(config.raw_data_dir) / site
        self._output_dir = Path(config.output_dir)
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
    def site(self) -> str:
        """
        Get the site identifier.

        :return: The site string.
        """
        return self._site

    @property
    def output_dir(self) -> Path:
        """
        Access the output directory for saving files.
        """
        return self._output_dir

    @property
    def filename_template(self) -> str:
        """
        Access the filename template.
        """
        return self._config.filename_template

    def _get_chapter(
        self,
        book_id: str,
        chap_id: str,
    ) -> ChapterDict | None:
        if book_id not in self._storage_cache:
            return None
        return self._storage_cache[book_id].get_best_chapter(chap_id)

    def _get_chapters(
        self,
        book_id: str,
        chap_ids: list[str],
    ) -> dict[str, ChapterDict | None]:
        if book_id not in self._storage_cache:
            return {}
        return self._storage_cache[book_id].get_best_chapters(chap_ids)

    def _load_book_info(self, book_id: str) -> BookInfoDict | None:
        info_path = self._raw_data_dir / book_id / "book_info.json"
        if not info_path.is_file():
            self.logger.error("Missing metadata file: %s", info_path)
            return None

        try:
            text = info_path.read_text(encoding="utf-8")
            data: Any = json.loads(text)
            if not isinstance(data, dict):
                self.logger.error(
                    "Invalid JSON structure in %s: expected an object at the top",
                    info_path,
                )
                return None
            return cast(BookInfoDict, data)
        except json.JSONDecodeError as e:
            self.logger.error("Corrupt JSON in %s: %s", info_path, e)
        return None

    def _init_chapter_storages(self, book_id: str) -> None:
        if book_id in self._storage_cache:
            return
        self._storage_cache[book_id] = ChapterStorage(
            raw_base=self._raw_data_dir / book_id,
            priorities=self._priorities,
        )
        self._storage_cache[book_id].connect()

    def _close_chapter_storages(self) -> None:
        for storage in self._storage_cache.values():
            try:
                storage.close()
            except Exception as e:
                self.logger.warning("Failed to close storage %s: %s", storage, e)
        self._storage_cache.clear()

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
        self._close_chapter_storages()

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
