#!/usr/bin/env python3
"""
novel_downloader.plugins.base.downloader
----------------------------------------

Abstract base class providing common workflow and utilities for novel downloaders
"""

import abc
import asyncio
import json
import logging
import re
import time
from collections.abc import Awaitable, Callable, Sequence
from pathlib import Path
from typing import Any, ClassVar

from novel_downloader.plugins.protocols import FetcherProtocol, ParserProtocol
from novel_downloader.schemas import (
    BookConfig,
    BookInfoDict,
    DownloaderConfig,
    VolumeInfoDict,
)

ONE_DAY = 86400  # seconds


class BaseDownloader(abc.ABC):
    """
    Abstract base class for novel downloaders.

    Defines the general interface and batch download workflow,
    while delegating book-specific downloading logic to subclasses.

    Subclasses are required to implement methods for downloading
    a single book, using the provided fetcher and parser components.
    """

    DEFAULT_SOURCE_ID: ClassVar[int] = 0
    PRIORITIES_MAP: ClassVar[dict[int, int]] = {
        DEFAULT_SOURCE_ID: 0,
    }

    _IMG_SRC_RE = re.compile(
        r'<img[^>]*\bsrc\s*=\s*["\'](https?://[^"\']+)["\'][^>]*>',
        re.IGNORECASE,
    )

    def __init__(
        self,
        fetcher: FetcherProtocol,
        parser: ParserProtocol,
        config: DownloaderConfig,
        site: str,
    ):
        """
        Initialize the downloader for a specific site.

        :param fetcher: Fetcher component for retrieving raw chapter data.
        :param parser: Parser component for extracting chapter content.
        :param config: Downloader configuration settings.
        :param site: Identifier for the target website or source.
        """
        self._fetcher = fetcher
        self._parser = parser
        self._site = site

        self._save_html = config.save_html
        self._skip_existing = config.skip_existing
        self._login_required = config.login_required
        self._request_interval = config.request_interval
        self._retry_times = config.retry_times
        self._backoff_factor = config.backoff_factor
        self._workers = config.workers
        self._storage_batch_size = max(1, config.storage_batch_size)

        self._raw_data_dir = Path(config.raw_data_dir) / site
        self._debug_dir = Path.cwd() / "debug" / site

        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def download_many(
        self,
        books: list[BookConfig],
        *,
        progress_hook: Callable[[int, int], Awaitable[None]] | None = None,
        cancel_event: asyncio.Event | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Download multiple books with pre-download hook and error handling.

        :param books: List of BookConfig entries.
        :param progress_hook: Optional async callback after each chapter.
                                args: completed_count, total_count.
        :param cancel_event: Optional asyncio.Event to allow cancellation.
        """
        if not self._check_login():
            book_ids = [b["book_id"] for b in books]
            self.logger.warning(
                "%s login failed, skipping download of books: %s",
                self._site,
                ", ".join(book_ids) or "<none>",
            )
            return

        for book in books:
            # stop early if cancellation requested
            if cancel_event and cancel_event.is_set():
                self.logger.info(
                    "%s download cancelled before book: %s",
                    self._site,
                    book["book_id"],
                )
                break

            try:
                await self._download_one(
                    book,
                    progress_hook=progress_hook,
                    cancel_event=cancel_event,
                    **kwargs,
                )
            except Exception as e:
                self._handle_download_exception(book, e)

    async def download(
        self,
        book: BookConfig,
        *,
        progress_hook: Callable[[int, int], Awaitable[None]] | None = None,
        cancel_event: asyncio.Event | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Download a single book with pre-download hook and error handling.

        :param book: BookConfig with at least 'book_id'.
        :param progress_hook: Optional async callback after each chapter.
                                args: completed_count, total_count.
        :param cancel_event: Optional asyncio.Event to allow cancellation.
        """
        if not self._check_login():
            self.logger.warning(
                "%s login failed, skipping download of book: %s (%s-%s)",
                self._site,
                book["book_id"],
                book.get("start_id", "-"),
                book.get("end_id", "-"),
            )
            return

        # if already cancelled before starting
        if cancel_event and cancel_event.is_set():
            self.logger.info(
                "%s download cancelled before start of book: %s",
                self._site,
                book["book_id"],
            )
            return

        try:
            await self._download_one(
                book,
                progress_hook=progress_hook,
                cancel_event=cancel_event,
                **kwargs,
            )
        except Exception as e:
            self._handle_download_exception(book, e)

    @abc.abstractmethod
    async def _download_one(
        self,
        book: BookConfig,
        *,
        progress_hook: Callable[[int, int], Awaitable[None]] | None = None,
        cancel_event: asyncio.Event | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Subclasses must implement this to define how to download a single book.
        """
        ...

    async def _load_book_info(self, book_id: str) -> BookInfoDict | None:
        """
        Attempt to fetch and parse the book_info for a given book_id.

        :param book_id: identifier of the book
        :return: parsed BookInfoDict or None if all attempts fail
        """
        info_path = self._raw_data_dir / book_id / "book_info.json"
        book_info: BookInfoDict | None = None

        if info_path.exists():
            try:
                book_info = json.loads(info_path.read_text(encoding="utf-8"))
                last_checked = book_info.get("last_checked", 0.0) if book_info else 0.0
                if time.time() - last_checked < ONE_DAY:
                    return book_info
            except json.JSONDecodeError:
                self.logger.warning(
                    "Corrupted book_info.json for %s: could not decode JSON", book_id
                )

        try:
            info_html = await self.fetcher.get_book_info(book_id)
            self._save_html_pages(book_id, "info", info_html)

            book_info = self.parser.parse_book_info(info_html)
            if book_info:
                book_info["last_checked"] = time.time()
                self._save_book_info(book_id, book_info)
                return book_info

        except Exception as exc:
            self.logger.warning(
                "Failed to fetch/parse book_info for %s: %s", book_id, exc
            )

        return book_info

    def _save_book_info(self, book_id: str, book_info: BookInfoDict) -> None:
        """
        Serialize and save the book_info dict as json.

        :param book_id: identifier of the book
        :param book_info: dict containing metadata about the book
        """
        target_dir = self._raw_data_dir / book_id
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / "book_info.json").write_text(
            json.dumps(book_info, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _save_html_pages(
        self,
        book_id: str,
        filename: str,
        html_list: Sequence[str],
        *,
        folder: str = "html",
    ) -> None:
        """
        If save_html is enabled, write each HTML snippet to a file.

        Filenames will be {book_id}_{filename}_{index}.html in html_dir.

        :param book_id: The book identifier
        :param filename: used as filename prefix
        :param html_list: list of HTML strings to save
        """
        if not self._save_html:
            return
        html_dir = self._debug_dir / folder
        html_dir.mkdir(parents=True, exist_ok=True)
        for i, html in enumerate(html_list):
            (html_dir / f"{book_id}_{filename}_{i}.html").write_text(
                html, encoding="utf-8"
            )

    @classmethod
    def _extract_img_urls(cls, content: str) -> list[str]:
        """
        Extract all <img> tag src URLs from the given HTML string.
        """
        return cls._IMG_SRC_RE.findall(content)

    @staticmethod
    def _select_chapter_ids(
        vols: list[VolumeInfoDict],
        start_id: str | None,
        end_id: str | None,
        ignore: set[str],
    ) -> list[str]:
        seen_start = start_id is None
        out: list[str] = []
        for vol in vols:
            for chap in vol["chapters"]:
                cid = chap.get("chapterId")
                if not cid:
                    continue
                if not seen_start:
                    if cid == start_id:
                        seen_start = True
                    else:
                        continue
                if cid not in ignore:
                    out.append(cid)
                if end_id is not None and cid == end_id:
                    return out
        return out

    @property
    def fetcher(self) -> FetcherProtocol:
        return self._fetcher

    @property
    def parser(self) -> ParserProtocol:
        return self._parser

    def _handle_download_exception(self, book: BookConfig, error: Exception) -> None:
        """
        Handle download errors in a consistent way.

        This method can be overridden or extended to implement retry logic, etc.

        :param book: The book that failed.
        :param error: The exception raised during download.
        """
        self.logger.warning(
            "%s Failed to download (book_id=%s, start=%s, end=%s): %s",
            self.__class__.__name__,
            book.get("book_id", "<unknown>"),
            book.get("start_id", "-"),
            book.get("end_id", "-"),
            error,
        )

    def _check_login(self) -> bool:
        """
        Check login if needed.
        """
        return self.fetcher.is_logged_in if self._login_required else True
