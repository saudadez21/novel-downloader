#!/usr/bin/env python3
"""
novel_downloader.plugins.base.exporter
--------------------------------------

Abstract base class providing common structure and utilities for book exporters
"""

import json
import logging
import types
from datetime import datetime
from pathlib import Path
from typing import Any, Self, cast

from novel_downloader.infra.persistence.chapter_storage import ChapterStorage
from novel_downloader.schemas import (
    BookConfig,
    BookInfoDict,
    ChapterDict,
    ExporterConfig,
)


class SafeDict(dict[str, Any]):
    def __missing__(self, key: str) -> str:
        return f"{{{key}}}"


class BaseExporter:
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

        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

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
        """
        Retrieve one chapter from the cached storage.

        :param book_id: Book identifier.
        :param chap_id: Chapter identifier.
        :return: ChapterDict if found, else None.
        """
        storage = self._storage_cache.get(book_id)
        if storage is None:
            return None
        return storage.get_chapter(chap_id)

    def _get_chapters(
        self,
        book_id: str,
        chap_ids: list[str],
    ) -> dict[str, ChapterDict | None]:
        """
        Retrieve multiple chapters in one call from the cached storage.

        :param book_id: Book identifier.
        :param chap_ids: List of chapter identifiers.
        :return: Mapping chap_id -> ChapterDict (or None if missing).
        """
        storage = self._storage_cache.get(book_id)
        if storage is None:
            return {}
        return storage.get_chapters(chap_ids)

    def _load_book_info(self, book_id: str, stage: str | None = None) -> BookInfoDict:
        """
        Load and return the book_info payload for the given book.

        :param book_id: Book identifier.
        :raises FileNotFoundError: if the metadata file does not exist.
        :raises ValueError: if the JSON is invalid or has an unexpected structure.
        :return: Parsed BookInfoDict.
        """
        stg = stage or self._resolve_stage_selection(book_id)
        base_dir = self._raw_data_dir / book_id

        info_path = base_dir / f"book_info.{stg}.json"
        if stg != "raw" and not info_path.is_file():
            # graceful fallback to raw metadata
            fallback = base_dir / "book_info.raw.json"
            if fallback.is_file():
                info_path = fallback

        if not info_path.is_file():
            raise FileNotFoundError(f"Missing metadata file: {info_path}")

        try:
            data = json.loads(info_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise ValueError(f"Corrupt JSON in {info_path}: {e}") from e

        if not isinstance(data, dict):
            raise ValueError(
                f"Invalid JSON structure in {info_path}: expected an object at the top"
            )

        return cast(BookInfoDict, data)

    def _init_chapter_storages(self, book_id: str, stage: str | None = None) -> None:
        """
        Ensure a ChapterStorage is open and cached for the given book_id.

        :param book_id: Book identifier.
        """
        if book_id in self._storage_cache:
            return

        raw_base = self._raw_data_dir / book_id

        if not raw_base.is_dir():
            raise FileNotFoundError(
                f"Chapter storage does not exist for book_id={book_id} ({raw_base})"
            )

        stg = stage or self._resolve_stage_selection(book_id)
        fname_base = f"chapter.{stg}.sqlite"

        storage = ChapterStorage(base_dir=raw_base, filename=fname_base)
        storage.connect()
        self._storage_cache[book_id] = storage

    def _load_stage_data(self, book_id: str) -> BookInfoDict:
        """
        Resolve the stage, open the corresponding chapter storage,
        and load the matching book_info.

          * Uses `chapter.<stage>.sqlite`
          * Uses `book_info.raw.json` or `book_info.<stage>.json`,
            falling back to raw `book_info.raw.json` if staged file is missing.
        """
        stage = self._resolve_stage_selection(book_id)
        self._init_chapter_storages(book_id, stage)
        return self._load_book_info(book_id, stage)

    def _close_chapter_storages(self) -> None:
        for storage in self._storage_cache.values():
            try:
                storage.close()
            except Exception as e:
                self.logger.warning("Failed to close storage %s: %s", storage, e)
        self._storage_cache.clear()

    def _resolve_stage_selection(self, book_id: str) -> str:
        """
        Return the chosen stage name for export (e.g., 'raw', 'cleaner', 'corrector').
        Strategy:
          * If pipeline.json exists, walk pipeline in reverse and pick the last stage
            whose recorded sqlite file exists.
          * Fallback: any executed record with an existing sqlite file.
          * Else: 'raw'.
        """
        base_dir = self._raw_data_dir / book_id
        pipeline_path = base_dir / "pipeline.json"
        if not pipeline_path.is_file():
            return "raw"

        try:
            meta = json.loads(pipeline_path.read_text(encoding="utf-8"))
        except Exception:
            return "raw"

        pipeline: list[str] = meta.get("pipeline", [])
        if not pipeline:
            return "raw"

        for stg in reversed(pipeline):
            fname = f"chapter.{stg}.sqlite"
            if (base_dir / fname).is_file():
                return stg

        return "raw"

    def _handle_missing_chapter(self, book_id: str, cid: str) -> None:
        """If check_missing is enabled, log a warning."""
        if not self._check_missing:
            return
        self.logger.warning(
            "Missing chapter content (bookId=%s, chapterId=%s)",
            book_id,
            cid,
        )

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
