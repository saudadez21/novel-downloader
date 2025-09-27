#!/usr/bin/env python3
"""
novel_downloader.plugins.base.exporter
--------------------------------------

Abstract base class providing common structure and utilities for book exporters
"""

import abc
import contextlib
import json
import logging
import types
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar, Self, cast

from novel_downloader.infra.persistence.chapter_storage import ChapterStorage
from novel_downloader.libs.textutils import get_cleaner
from novel_downloader.schemas import (
    BookConfig,
    BookInfoDict,
    ChapterDict,
    ExporterConfig,
)


class SafeDict(dict[str, Any]):
    def __missing__(self, key: str) -> str:
        return f"{{{key}}}"


class BaseExporter(abc.ABC):
    """
    BaseExporter defines the interface and common structure for
    saving assembled book content into various formats
    such as TXT, EPUB, Markdown, or PDF.
    """

    DEFAULT_SOURCE_ID: ClassVar[int] = 0
    PRIORITIES_MAP: ClassVar[dict[int, int]] = {
        DEFAULT_SOURCE_ID: 0,
    }

    def __init__(
        self,
        config: ExporterConfig,
        site: str,
    ):
        """
        Initialize the exporter with given configuration.

        :param config: Exporter configuration settings.
        :param site: Identifier for the target website or source.
        """
        self._site = site
        self._storage_cache: dict[str, ChapterStorage] = {}

        self._make_txt = config.make_txt
        self._make_epub = config.make_epub
        self._make_md = config.make_md
        self._make_pdf = config.make_pdf

        self._check_missing = config.check_missing
        self._include_cover = config.include_cover
        self._include_picture = config.include_picture
        self._split_mode = config.split_mode
        self._filename_template = config.filename_template
        self._append_timestamp = config.append_timestamp

        self._raw_data_dir = Path(config.raw_data_dir) / site
        self._output_dir = Path(config.output_dir)

        self._cleaner = get_cleaner(
            enabled=config.clean_text,
            config=config.cleaner_cfg,
        )

        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def export(self, book: BookConfig) -> dict[str, Path]:
        """
        Export the book in the formats specified in config.

        :param book: BookConfig with at least 'book_id'.
        """
        results: dict[str, Path] = {}

        actions = [
            (self._make_txt, "txt", self.export_as_txt),
            (self._make_epub, "epub", self.export_as_epub),
            (self._make_md, "md", self.export_as_md),
            (self._make_pdf, "pdf", self.export_as_pdf),
        ]

        for enabled, fmt_key, export_method in actions:
            if enabled:
                try:
                    self.logger.info(
                        "Attempting to export book_id '%s' as %s...",
                        book["book_id"],
                        fmt_key,
                    )
                    path = export_method(book)

                    if isinstance(path, Path):
                        results[fmt_key] = path
                        self.logger.info("Successfully saved as %s.", fmt_key)

                except NotImplementedError as e:
                    self.logger.warning(
                        "Export method for %s not implemented: %s",
                        fmt_key,
                        e,
                    )
                except Exception:
                    self.logger.exception("Error while saving as %s", fmt_key)

        return results

    def export_as_txt(self, book: BookConfig) -> Path | None:
        """
        Persist the assembled book as a .txt file.

        :param book: BookConfig with at least 'book_id'.
        :raises NotImplementedError: If the method is not overridden.
        """
        raise NotImplementedError("TXT export not supported by this Exporter.")

    def export_as_epub(self, book: BookConfig) -> Path | None:
        """
        Optional: Persist the assembled book as a EPUB (.epub) file.

        :param book: BookConfig with at least 'book_id'.
        :raises NotImplementedError: If the method is not overridden.
        """
        raise NotImplementedError("EPUB export not supported by this Exporter.")

    def export_as_md(self, book: BookConfig) -> Path | None:
        """
        Optional: Persist the assembled book as a Markdown file.

        :param book: BookConfig with at least 'book_id'.
        :raises NotImplementedError: If the method is not overridden.
        """
        raise NotImplementedError("Markdown export not supported by this Exporter.")

    def export_as_pdf(self, book: BookConfig) -> Path | None:
        """
        Optional: Persist the assembled book as a PDF file.

        :param book: BookConfig with at least 'book_id'.
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
        context = SafeDict(title=title, author=author or "", **extra_fields)
        name = self._filename_template.format_map(context)
        if self._append_timestamp:
            name += f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return f"{name}.{ext}"

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

    def _init_chapter_storages(self, book_id: str) -> bool:
        if book_id in self._storage_cache:
            return True
        raw_base = self._raw_data_dir / book_id
        if not raw_base.is_dir():
            self.logger.warning(
                "Chapter storage base does not exist for book_id=%s", book_id
            )
            return False
        self._storage_cache[book_id] = ChapterStorage(
            raw_base=raw_base,
            priorities=self.PRIORITIES_MAP,
        )
        self._storage_cache[book_id].connect()
        return True

    def _close_chapter_storages(self) -> None:
        for storage in self._storage_cache.values():
            try:
                storage.close()
            except Exception as e:
                self.logger.warning("Failed to close storage %s: %s", storage, e)
        self._storage_cache.clear()

    def _handle_missing_chapter(self, cid: str) -> None:
        """If check_missing is enabled, log a warning."""
        if not self._check_missing:
            return
        self.logger.warning("Missing chapter content for chapterId=%s", cid)

    def close(self) -> None:
        """
        Shutdown and clean up the exporter.
        """
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
        with contextlib.suppress(Exception):
            self.close()
