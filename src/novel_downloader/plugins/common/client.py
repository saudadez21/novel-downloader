#!/usr/bin/env python3
"""
novel_downloader.plugins.common.client
--------------------------------------
"""

import logging
from pathlib import Path
from typing import Any, Protocol

from novel_downloader.plugins.base.client import BaseClient
from novel_downloader.plugins.mixins import (
    DownloadMixin,
    ExportEpubMixin,
    ExportHtmlMixin,
    ExportTxtMixin,
)
from novel_downloader.plugins.protocols import ExportUI, LoginUI, ProcessUI
from novel_downloader.plugins.utils.stage_runner import StageRunner
from novel_downloader.schemas import BookConfig, ExporterConfig, ProcessorConfig

logger = logging.getLogger(__name__)


class _ExportFunc(Protocol):
    def __call__(
        self,
        book: BookConfig,
        cfg: ExporterConfig,
        *,
        stage: str | None,
        **kwargs: Any,
    ) -> list[Path]:
        ...


# class CommonClient(DownloadMixin, BaseClient):
class CommonClient(
    DownloadMixin,
    ExportEpubMixin,
    ExportHtmlMixin,
    ExportTxtMixin,
    BaseClient,
):
    """
    Specialized client for "common" novel sites.
    """

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
        if await self.fetcher.load_state():
            return True

        login_data = await ui.prompt(self.fetcher.login_fields, prefill=login_cfg)
        if not await self.fetcher.login(**login_data):
            if ui:
                ui.on_login_failed()
            return False

        await self.fetcher.save_state()
        if ui:
            ui.on_login_success()
        return True

    def process_book(
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
        raw_base = self._raw_data_dir / book.book_id

        raw_sqlite = raw_base / "chapter.raw.sqlite"
        book_info_path = raw_base / "book_info.raw.json"

        # Pre-flight checks
        if not raw_sqlite.is_file():
            if ui:
                ui.on_missing(book, "raw", raw_sqlite)
            return
        if not book_info_path.is_file():
            if ui:
                ui.on_missing(book, "book_info", book_info_path)
            return

        stage_name: str = "Unknown"
        try:
            runner = StageRunner(base_dir=raw_base, book=book)
            for pconf in processors:
                stage_name = pconf.name
                if ui:
                    ui.on_stage_start(book, stage_name)

                def _progress(
                    done: int,
                    total: int,
                    *,
                    _b: BookConfig = book,
                    _s: str = stage_name,
                ) -> None:
                    if ui:
                        ui.on_stage_progress(_b, _s, done, total)

                runner.run(pconf, on_progress=_progress)

                if ui:
                    ui.on_stage_complete(book, stage_name)

            logger.info("All stages completed successfully for book %s", book.book_id)

        except Exception as e:
            logger.warning(
                "Processing failed at stage '%s' for book %s: %s",
                stage_name,
                book.book_id,
                e,
            )

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
        Persist the assembled book to disk.

        :param book: The book configuration to export.
        :param cfg: Optional ExporterConfig defining export parameters.
        :param formats: Optional list of format strings (e.g., ['epub', 'txt']).
        :param ui: Optional ExportUI for reporting export progress.
        :return: A mapping from format name to the resulting file path.
        """
        cfg = cfg or ExporterConfig()
        formats = formats or ["epub"]
        results: dict[str, list[Path]] = {}

        for fmt in formats:
            method_name = f"_export_{cfg.split_mode}_{fmt.lower()}"
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
                logger.warning(f"Error exporting {fmt}: {e}")
                if ui:
                    ui.on_error(book, fmt, e)

        return results

    def export_chapter(
        self,
        book_id: str,
        chapter_id: str,
        cfg: ExporterConfig | None = None,
        *,
        formats: list[str] | None = None,
        stage: str | None = None,
        **kwargs: Any,
    ) -> dict[str, list[Path]]:
        """
        Persist the assembled chapter to disk.

        :param cfg: Optional ExporterConfig defining export parameters.
        :param formats: Optional list of format strings (e.g., ['epub', 'txt']).
        :return: A mapping from format name to the resulting file path.
        """
        # TODO: placeholder
        return {}
