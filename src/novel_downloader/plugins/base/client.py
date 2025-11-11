#!/usr/bin/env python3
"""
novel_downloader.plugins.base.client
------------------------------------

Abstract base class providing common
"""

import abc
import json
import logging
import time
import types
from pathlib import Path
from typing import Any, Protocol, Self, cast

from novel_downloader.libs.filesystem import img_name
from novel_downloader.plugins.protocols import FetcherProtocol, ParserProtocol
from novel_downloader.plugins.protocols.ui import (
    DownloadUI,
    ExportUI,
    LoginUI,
    ProcessUI,
)
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import (
    BookConfig,
    BookInfoDict,
    ChapterDict,
    ChapterInfoDict,
    ClientConfig,
    ExporterConfig,
    FetcherConfig,
    ParserConfig,
    ProcessorConfig,
    VolumeInfoDict,
)

ONE_DAY = 86400  # seconds


class AbstractClient(abc.ABC):
    """
    Abstract base class for site client.
    """

    def __init__(
        self,
        site: str,
        config: ClientConfig | None = None,
    ) -> None:
        """
        Initialize the downloader for a specific site.

        :param site: Identifier for the target website or source.
        :param config: Downloader configuration settings.
        """
        self._site = site
        cfg = config or ClientConfig()

        self._save_html = cfg.save_html
        self._skip_existing = cfg.skip_existing
        self._request_interval = cfg.request_interval
        self._retry_times = cfg.retry_times
        self._backoff_factor = cfg.backoff_factor
        self._workers = max(1, cfg.workers)
        self._storage_batch_size = max(1, cfg.storage_batch_size)

        self._fetcher_cfg = cfg.fetcher_cfg
        self._parser_cfg = cfg.parser_cfg

        self._fetcher: FetcherProtocol | None = None
        self._parser: ParserProtocol | None = None

        self._raw_data_dir = Path(cfg.raw_data_dir) / site
        self._output_dir = Path(cfg.output_dir)
        self._debug_dir = Path.cwd() / "debug" / site

        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def init(self, fetcher_cfg: FetcherConfig, parser_cfg: ParserConfig) -> None:
        if self._fetcher or self._parser:
            await self.close()
        self._fetcher = registrar.get_fetcher(self._site, fetcher_cfg)
        self._parser = registrar.get_parser(self._site, parser_cfg)

        await self._fetcher.init()

    async def close(self) -> None:
        if self._fetcher:
            if self._fetcher.is_logged_in:
                await self._fetcher.save_state()
            await self._fetcher.close()
            self._fetcher = None
        self._parser = None

    @abc.abstractmethod
    async def login(
        self,
        *,
        ui: LoginUI,
        login_cfg: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> bool:
        """
        Attempt to log in asynchronously.

        :returns: True if login succeeded.
        """
        ...

    @abc.abstractmethod
    async def download(
        self,
        book: BookConfig,
        *,
        ui: DownloadUI | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Download a single book.

        :param book: BookConfig with at least 'book_id'.
        :param cancel_event: Optional asyncio.Event to allow cancellation.
        :param ui: Optional DownloadUI to report progress or messages.
        """
        ...

    @abc.abstractmethod
    def process(
        self,
        book: BookConfig,
        processors: list[ProcessorConfig],
        *,
        ui: ProcessUI | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Run all processors for a single book.

        :param book: BookConfig to process.
        :param ui: Optional ProcessUI to report progress.
        """
        ...

    @abc.abstractmethod
    async def cache_images(
        self,
        book: BookConfig,
        *,
        force_update: bool = False,
        concurrent: int = 10,
        **kwargs: Any,
    ) -> None:
        """
        Asynchronously pre-cache all images associated with a book.

        :param book: The BookConfig instance representing the book.
        :param force_update: If True, re-download even if images are already cached.
        :param concurrent: Maximum number of concurrent download tasks.
        """
        ...

    @abc.abstractmethod
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
        Persist the assembled book to disk.

        :param book: The book configuration to export.
        :param cfg: Optional ExporterConfig defining export parameters.
        :param formats: Optional list of format strings (e.g., ['epub', 'txt']).
        :param ui: Optional ExportUI for reporting export progress.
        :return: A mapping from format name to the resulting file path.
        """
        ...

    @property
    def fetcher(self) -> FetcherProtocol:
        """
        Return the active fetcher.

        :raises RuntimeError: If the fetcher is uninitialized.
        """
        if self._fetcher is None:
            raise RuntimeError("Fetcher is not initialized.")
        return self._fetcher

    @property
    def parser(self) -> ParserProtocol:
        """
        Return the active parser.

        :raises RuntimeError: If the parser is uninitialized.
        """
        if self._parser is None:
            raise RuntimeError("Fetcher is not initialized.")
        return self._parser

    @property
    def workers(self) -> int:
        return self._workers

    async def __aenter__(self) -> Self:
        await self.init(self._fetcher_cfg, self._parser_cfg)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        tb: types.TracebackType | None,
    ) -> None:
        await self.close()


class SafeDict(dict[str, Any]):
    def __missing__(self, key: str) -> str:
        return f"{{{key}}}"


class _ExportFunc(Protocol):
    def __call__(
        self,
        book: BookConfig,
        cfg: ExporterConfig | None = None,
        *,
        stage: str | None,
        **kwargs: Any,
    ) -> list[Path]:
        ...


class BaseClient(AbstractClient, abc.ABC):
    """
    Abstract intermediate client that provides reusable helper methods.
    """

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
        Persist the assembled book to disk.

        :param book: The book configuration to export.
        :param cfg: Optional ExporterConfig defining export parameters.
        :param formats: Optional list of format strings (e.g., ['epub', 'txt']).
        :param ui: Optional ExportUI for reporting export progress.
        :return: A mapping from format name to the resulting file path.
        """
        formats = formats or ["epub"]
        results: dict[str, list[Path]] = {}

        for fmt in formats:
            method_name = f"export_as_{fmt.lower()}"
            export_func: _ExportFunc | None = getattr(self, method_name, None)

            if not callable(export_func):
                if ui:
                    ui.on_unsupported(book, fmt)
                results[fmt] = []
                continue

            if ui:
                ui.on_start(book, fmt)

            try:
                paths = export_func(book, cfg, stage=stage, **kwargs)
                results[fmt] = paths

                if paths and ui:
                    for path in paths:
                        ui.on_success(book, fmt, path)

            except Exception as e:
                results[fmt] = []
                self.logger.warning(f"Error exporting {fmt}: {e}")
                if ui:
                    ui.on_error(book, fmt, e)

        return results

    async def _get_book_info(self, book_id: str) -> BookInfoDict:
        """
        Attempt to fetch and parse the book_info for a given book_id.

        :param book_id: identifier of the book
        :return: parsed BookInfoDict
        """
        book_info: BookInfoDict | None = None
        try:
            book_info = self._load_book_info(book_id)
            if book_info and time.time() - book_info.get("last_checked", 0.0) < ONE_DAY:
                return book_info
        except FileNotFoundError as exc:
            self.logger.debug("No cached book_info found for %s: %s", book_id, exc)
        except Exception as exc:
            self.logger.info("Failed to load cached book_info for %s: %s", book_id, exc)

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

        if book_info is None:
            raise LookupError(f"Unable to load book_info for {book_id}")

        return book_info

    def _save_book_info(
        self, book_id: str, book_info: BookInfoDict, stage: str = "raw"
    ) -> None:
        """
        Serialize and save the book_info dict as json.

        :param book_id: identifier of the book
        :param book_info: dict containing metadata about the book
        """
        target_dir = self._raw_data_dir / book_id
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / f"book_info.{stage}.json").write_text(
            json.dumps(book_info, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _load_book_info(self, book_id: str, stage: str = "raw") -> BookInfoDict:
        """
        Load and return the book_info payload for the given book.

        :param book_id: Book identifier.
        :raises FileNotFoundError: if the metadata file does not exist.
        :raises ValueError: if the JSON is invalid or has an unexpected structure.
        :return: Parsed BookInfoDict.
        """
        info_path = self._raw_data_dir / book_id / f"book_info.{stage}.json"
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

    def _save_html_pages(
        self,
        book_id: str,
        filename: str,
        html_list: list[str],
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

    def _get_filename(
        self,
        filename_template: str,
        *,
        title: str,
        author: str | None = None,
        append_timestamp: bool = True,
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
        name = filename_template.format_map(context)
        if append_timestamp:
            from datetime import datetime

            name += f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return f"{name}.{ext}"

    def _collect_img_map(self, chap: ChapterDict) -> dict[int, list[dict[str, Any]]]:
        """
        Collect and normalize `image_positions` into {int: [ {type, data, ...}, ... ]}.
        """
        extra = chap.get("extra")
        if not isinstance(extra, dict):
            return {}

        raw_map = extra.get("image_positions")
        if not isinstance(raw_map, dict):
            return {}

        result: dict[int, list[dict[str, Any]]] = {}

        for k, v in raw_map.items():
            try:
                key = int(k)
            except Exception:
                key = 0
            items: list[dict[str, str]] = []
            if isinstance(v, list | tuple):
                for u in v:
                    if isinstance(u, str):
                        s = u.strip()
                        if s:
                            item = {
                                "type": "url" if s.startswith("http") else "data",
                                "data": s,
                            }
                            items.append(item)
                    elif isinstance(u, dict):
                        if "data" in u:
                            items.append(u)
            elif isinstance(v, str) and (s := v.strip()):
                items.append(
                    {"type": "url" if s.startswith("http") else "data", "data": s}
                )

            if items:
                result.setdefault(key, []).extend(items)
        return result

    def _extract_img_urls(self, chap: ChapterDict) -> list[str]:
        """
        Extract all image URLs from 'extra' field.
        """
        img_map = self._collect_img_map(chap)
        urls: list[str] = []
        for imgs in img_map.values():
            for img in imgs:
                if img.get("type") == "url" and isinstance(img.get("data"), str):
                    urls.append(img["data"])
        return urls

    @staticmethod
    def _resolve_img_path(
        img_dir: Path | None,
        url: str | None,
        *,
        name: str | None = None,
    ) -> Path | None:
        """
        Resolve the local path of an image if it exists.

        :param img_dir: The directory where images are stored.
        :param url: The source URL of the image.
        :param name: Optional explicit base name.
        :return: Path to the existing image, or None if not found or invalid.
        """
        if not img_dir or not url:
            return None

        path = img_dir / img_name(url, name=name)
        return path if path.is_file() else None

    @staticmethod
    def _select_chapter_ids(
        vols: list[VolumeInfoDict],
        start_id: str | None,
        end_id: str | None,
        ignore: frozenset[str],
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
                if cid not in ignore and chap.get("accessible", True):
                    out.append(cid)
                if end_id is not None and cid == end_id:
                    return out
        return out

    @staticmethod
    def _filter_volumes(
        vols: list[VolumeInfoDict],
        start_id: str | None,
        end_id: str | None,
        ignore: frozenset[str],
    ) -> list[VolumeInfoDict]:
        """
        Rebuild volumes to include only chapters within
        the [start_id, end_id] range (inclusive),
        while excluding any chapter IDs in `ignore`.

        :param vols: List of volume dicts.
        :param start_id: Range start chapter ID (inclusive) or None to start.
        :param end_id: Range end chapter ID (inclusive) or None to go till the end.
        :param ignore: Set of chapter IDs to exclude (regardless of range).
        :return: New list of volumes with chapters filtered accordingly.
        """
        if start_id is None and end_id is None and not ignore:
            return vols

        started = start_id is None
        finished = False
        result: list[VolumeInfoDict] = []

        for vol in vols:
            if finished:
                break

            kept: list[ChapterInfoDict] = []

            for ch in vol.get("chapters", []):
                cid = ch.get("chapterId")
                if not cid:
                    continue

                # wait until hit the start_id
                if not started:
                    if cid == start_id:
                        started = True
                    else:
                        continue

                if cid not in ignore:
                    kept.append(ch)

                # check for end_id after keeping
                if end_id is not None and cid == end_id:
                    finished = True
                    break

            if kept:
                result.append(
                    {
                        **vol,
                        "chapters": kept,
                    }
                )

        return result

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
            db_file = base_dir / f"chapter.{stg}.sqlite"
            info_file = base_dir / f"book_info.{stg}.json"
            if db_file.is_file() and info_file.is_file():
                return stg

        return "raw"
