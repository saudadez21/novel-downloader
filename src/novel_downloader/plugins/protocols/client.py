#!/usr/bin/env python3
"""
novel_downloader.plugins.protocols.client
-----------------------------------------

Protocol definitions for client implementations.

A client orchestrates fetching, parsing, processing, and exporting
of book data using site-specific fetchers, parsers, and processors.
"""

import types
from pathlib import Path
from typing import Any, Protocol, Self

from novel_downloader.schemas import (
    BookConfig,
    BookInfoDict,
    ChapterDict,
    ExporterConfig,
    FetcherConfig,
    ParserConfig,
    PipelineMeta,
    ProcessorConfig,
    VolumeInfoDict,
)

from .fetcher import FetcherProtocol
from .parser import ParserProtocol
from .ui import (
    DownloadUI,
    ExportUI,
    LoginUI,
    ProcessUI,
)


class ClientProtocol(Protocol):
    """
    Protocol for a site-specific client implementation.

    Defines the required asynchronous and synchronous interfaces
    for fetching, processing, and exporting books and related resources.

    Concrete implementations (e.g. ``QidianClient``) should subclass
    :class:`AbstractClient` or otherwise conform to this protocol.
    """

    async def init(self, fetcher_cfg: FetcherConfig, parser_cfg: ParserConfig) -> None:
        """
        Initialize the client with fetcher and parser configurations.

        :param fetcher_cfg: Configuration for the network fetcher.
        :param parser_cfg: Configuration for the data parser.
        """
        ...

    async def close(self) -> None:
        """Close all open resources such as network sessions or workers."""
        ...

    async def login(
        self,
        *,
        ui: LoginUI,
        login_cfg: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> bool:
        """
        Attempt asynchronous login to the target website or API.

        :param ui: :class:`LoginUI` instance for user interaction.
        :param login_cfg: Optional credential mapping.
        :return: ``True`` if login succeeded.
        """
        ...

    async def get_book_info(
        self,
        book_id: str,
        **kwargs: Any,
    ) -> BookInfoDict:
        """
        Retrieve structured metadata for a given book.

        This high-level helper will attempt to:
          * load cached metadata if available,
          * otherwise fetch raw pages via the :class:`FetcherProtocol`,
          * parse the result using :class:`ParserProtocol`,
          * persist the parsed metadata for future reuse.

        :param book_id: Identifier of the book to retrieve metadata for.
        :return: Parsed :class:`BookInfoDict` instance.
        """
        ...

    async def get_chapter(
        self,
        book_id: str,
        chapter_id: str,
        **kwargs: Any,
    ) -> ChapterDict | None:
        """
        Retrieve structured content for a single chapter.

        This high-level helper performs:
          * fetching raw chapter pages via :class:`FetcherProtocol`,
          * saving the raw HTML for inspection or caching,
          * parsing the chapter content,
          * extracting and downloading any referenced images,
          * retrying the operation up to ``self.retry_times``.

        :return: Parsed :class:`ChapterDict` on success, or ``None`` on failure.
        """
        ...

    async def download(
        self,
        book: BookConfig,
        *,
        ui: DownloadUI | None = None,
        **kwargs: Any,
    ) -> None:
        """
        .. deprecated:: 3.0.0
           This method is deprecated and will be removed in a future release.
           Use :meth:`download_book` instead.

        Download a single book.

        :param book: :class:`BookConfig` with at least ``book_id`` defined.
        :param ui: Optional :class:`DownloadUI` for progress reporting.
        """
        ...

    async def download_book(
        self,
        book: BookConfig,
        *,
        ui: DownloadUI | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Download all chapters and metadata for a single book.

        :param book: :class:`BookConfig` with at least ``book_id`` defined.
        :param ui: Optional :class:`DownloadUI` for progress reporting.
        """
        ...

    async def download_chapter(
        self,
        book_id: str,
        chapter_id: str,
        **kwargs: Any,
    ) -> None:
        """
        Download a specific chapter by its identifier.

        :param book_id: Identifier of the book to download.
        :param chapter_id: Identifier of the chapter to download.
        """
        ...

    def process_book(
        self,
        book: BookConfig,
        processors: list[ProcessorConfig],
        *,
        ui: ProcessUI | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Apply configured processors to the given book.

        :param book: :class:`BookConfig` to process.
        :param processors: List of :class:`ProcessorConfig` items.
        :param ui: Optional :class:`ProcessUI` for progress reporting.
        """
        ...

    async def cache_media(
        self,
        book: BookConfig,
        *,
        force_update: bool = False,
        concurrent: int = 10,
        **kwargs: Any,
    ) -> None:
        """
        Pre-cache media files (e.g., images) associated with a book.

        :param book: :class:`BookConfig` representing the book.
        :param force_update: Re-download media even if cached.
        :param concurrent: Maximum number of concurrent download tasks.
        """
        ...

    def cleanup_book(
        self,
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
        ...

    def cleanup_metadata(
        self,
        book_id: str,
        *,
        stage: str = "raw",
        **kwargs: Any,
    ) -> None:
        """
        Delete metadata JSON for a book.
        """
        ...

    def cleanup_chapters(
        self,
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
        ...

    def cleanup_media(
        self,
        book_id: str,
        **kwargs: Any,
    ) -> None:
        """
        Delete images/media folder for this book.
        """
        ...

    def cleanup_cache(
        self,
        **kwargs: Any,
    ) -> None:
        """
        Remove local cache directory for site.
        """
        ...

    def export(
        self,
        book: BookConfig,
        cfg: ExporterConfig | None = None,
        *,
        formats: list[str] | None = None,
        stage: str | None = None,
        ui: ExportUI | None = None,
        **kwargs: Any,
    ) -> dict[str, list[Path]]:
        """
        .. deprecated:: 3.0.0
           This method is deprecated and will be removed in a future release.
           Use :meth:`export_book` instead.

        Persist the assembled book to disk.

        :param book: The book configuration to export.
        :param cfg: Optional ExporterConfig defining export parameters.
        :param formats: Optional list of format strings (e.g., ['epub', 'txt']).
        :param ui: Optional ExportUI for reporting export progress.
        :return: A mapping from format name to the resulting file path.
        """
        ...

    def export_book(
        self,
        book: BookConfig,
        cfg: ExporterConfig | None = None,
        *,
        formats: list[str] | None = None,
        stage: str | None = None,
        ui: ExportUI | None = None,
        **kwargs: Any,
    ) -> dict[str, list[Path]]:
        """
        Persist the assembled book to disk in one or more formats.

        :param book: The :class:`BookConfig` instance to export.
        :param cfg: Optional :class:`ExporterConfig` defining export parameters.
        :param formats: Optional list of format identifiers (e.g. ``['epub', 'txt']``).
        :param stage: Optional export stage name, used for multi-phase exports.
        :param ui: Optional :class:`ExportUI` for reporting progress.
        :return: Mapping from format name to generated file paths.
        """
        ...

    def export_chapter(
        self,
        book_id: str,
        chapter_id: str,
        cfg: ExporterConfig | None = None,
        *,
        formats: list[str] | None = None,
        stage: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Path | None]:
        """
        Persist a single chapter to disk in one or more formats.

        :param book_id: Identifier of the book to download.
        :param chapter_id: Identifier of the chapter to download.
        :param cfg: Optional :class:`ExporterConfig` defining export parameters.
        :param formats: Optional list of format identifiers (e.g. ``['epub', 'txt']``).
        :param stage: Optional export stage name.
        :return: Mapping from format name to generated file paths.
        """
        ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        tb: types.TracebackType | None,
    ) -> None: ...


class _ClientContext(ClientProtocol, Protocol):
    """
    Internal protocol used for mixin typing.

    Provides common attributes and helper methods shared between
    concrete client classes and mixins.
    """

    _site: str

    _cache_dir: Path
    _raw_data_dir: Path
    _output_dir: Path
    _debug_dir: Path

    _request_interval: float
    _retry_times: int
    _backoff_factor: float

    _cache_book_info: bool
    _cache_chapter: bool
    _fetch_inaccessible: bool

    _storage_batch_size: int

    @property
    def fetcher(self) -> FetcherProtocol:
        """Return the active :class:`FetcherProtocol` instance."""
        ...

    @property
    def parser(self) -> ParserProtocol:
        """Return the active :class:`ParserProtocol` instance."""
        ...

    @property
    def workers(self) -> int: ...

    def _book_dir(self, book_id: str) -> Path: ...

    def _detect_latest_stage(self, book_id: str) -> str:
        """
        Determine the most recent processing stage for export.

        Strategy:
          * If ``pipeline.json`` exists, walk the pipeline in reverse and
            pick the last stage whose recorded SQLite file exists.
          * Fallback: any executed record with an existing SQLite file.
          * Else: ``'raw'``.
        """
        ...

    def _save_book_info(
        self, book_id: str, book_info: BookInfoDict, stage: str = "raw"
    ) -> None:
        """Serialize and save :class:`BookInfoDict` as JSON."""
        ...

    def _load_book_info(self, book_id: str, stage: str = "raw") -> BookInfoDict:
        """Load and return stored :class:`BookInfoDict` for a book."""
        ...

    def _load_pipeline_meta(self, book_id: str) -> PipelineMeta:
        """Load and return the pipeline metadata for the given book."""
        ...

    def _save_pipeline_meta(self, book_id: str, meta: PipelineMeta) -> None:
        """Serialize and write ``pipeline.json`` for the given book."""
        ...

    def _save_raw_pages(
        self,
        book_id: str,
        filename: str,
        raw_pages: list[str],
        *,
        folder: str = "raw",
    ) -> None:
        """
        Optionally persist raw fetched page fragments to disk.

        Files will be named ``{book_id}_{filename}_{index}.html`` (or similar)
        under the given ``folder``.
        """
        ...

    @staticmethod
    def _filter_volumes(
        vols: list[VolumeInfoDict],
        start_id: str | None,
        end_id: str | None,
        ignore: frozenset[str],
    ) -> list[VolumeInfoDict]:
        """
        Filter volumes to include only chapters within a given range,
        excluding any chapter IDs in ``ignore``.
        """
        ...

    def _extract_chapter_ids(
        self,
        vols: list[VolumeInfoDict],
        start_id: str | None,
        end_id: str | None,
        ignore: frozenset[str],
    ) -> list[str]:
        """Select chapter IDs matching the specified range and exclusions."""
        ...

    @staticmethod
    def _resolve_image_path(
        img_dir: Path | None,
        url: str | None,
        *,
        name: str | None = None,
    ) -> Path | None:
        """Resolve the local path of an image if it exists."""
        ...
