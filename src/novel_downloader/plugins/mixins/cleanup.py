#!/usr/bin/env python3
"""
novel_downloader.plugins.mixins.cleanup
---------------------------------------
"""

import logging
import shutil
from typing import TYPE_CHECKING, Any

from novel_downloader.infra.persistence.chapter_storage import ChapterStorage
from novel_downloader.schemas import BookConfig

logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from novel_downloader.plugins.protocols import _ClientContext


class CleanupMixin:
    """"""

    def cleanup_book(
        self: "_ClientContext",
        book: BookConfig,
        *,
        remove_metadata: bool = True,
        remove_chapters: bool = True,
        remove_media: bool = False,
        remove_all: bool = False,
        stage: str = "raw",
        **kwargs: Any,
    ) -> None:
        """
        Cleanup an entire book, or selectively remove chapter data + metadata.

        :param remove_all: If True, remove the entire book folder.
        :param stage: Which stage/version of raw data to remove.
        """
        if remove_all:
            book_dir = self._raw_data_dir / book.book_id
            if book_dir.exists():
                logger.info(
                    "Removing all raw data for book %s at %s", book.book_id, book_dir
                )
                shutil.rmtree(book_dir, ignore_errors=True)
            else:
                logger.info(
                    "Raw data directory for book %s does not exist, nothing to remove.",
                    book.book_id,
                )
            return

        # Selective cleanup
        if remove_chapters:
            self.cleanup_chapters(
                book.book_id,
                start_id=book.start_id,
                end_id=book.end_id,
                ignore_ids=book.ignore_ids,
                stage=stage,
            )

        if remove_metadata:
            self.cleanup_metadata(book.book_id, stage=stage)

        if remove_media:
            self.cleanup_media(book.book_id)

    def cleanup_metadata(
        self: "_ClientContext",
        book_id: str,
        *,
        stage: str = "raw",
        **kwargs: Any,
    ) -> None:
        """
        Delete metadata JSON for a book.
        """
        metadata_path = self._raw_data_dir / book_id / f"book_info.{stage}.json"

        if metadata_path.exists():
            try:
                metadata_path.unlink()
                logger.info("Removed metadata: %s", metadata_path)
            except Exception as e:
                logger.warning("Failed to remove metadata %s: %s", metadata_path, e)
        else:
            logger.debug(
                "Metadata file not found for book %s (stage=%s)", book_id, stage
            )

    def cleanup_chapters(
        self: "_ClientContext",
        book_id: str,
        start_id: str | None = None,
        end_id: str | None = None,
        ignore_ids: frozenset[str] = frozenset(),
        *,
        stage: str = "raw",
        **kwargs: Any,
    ) -> None:
        """
        Delete populated chapter entries (in SQLite) for a given range.
        """
        raw_base = self._raw_data_dir / book_id

        # Load chapter listing from metadata
        book_info = self._load_book_info(book_id, stage=stage)
        vols = book_info["volumes"]
        cids = self._extract_chapter_ids(vols, start_id, end_id, ignore_ids)

        db_path = raw_base / f"chapter.{stage}.sqlite"
        if not db_path.exists():
            logger.debug("No chapter DB for book %s (stage=%s)", book_id, stage)
            return

        # Delete rows from SQLite
        with ChapterStorage(raw_base, filename=f"chapter.{stage}.sqlite") as storage:
            deleted = storage.delete_chapters(cids)
            if deleted > 0:
                storage.vacuum()
            logger.info("Deleted %d chapters (requested %d)", deleted, len(cids))

    def cleanup_media(
        self: "_ClientContext",
        book_id: str,
        **kwargs: Any,
    ) -> None:
        """
        Delete images/media folder for this book.
        """
        media_dir = self._raw_data_dir / book_id / "media"

        if media_dir.exists():
            logger.info("Removing media directory: %s", media_dir)
            shutil.rmtree(media_dir, ignore_errors=True)
        else:
            logger.debug("No media directory for book %s", book_id)

    def cleanup_cache(
        self: "_ClientContext",
        **kwargs: Any,
    ) -> None:
        """
        Remove local cache directory for site.
        """
        cache_dir = self._cache_dir

        if cache_dir.exists():
            logger.info("Removing cache directory: %s", cache_dir)
            shutil.rmtree(cache_dir, ignore_errors=True)
        else:
            logger.debug("No cache directory for site %s", self._site)
