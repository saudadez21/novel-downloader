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
    CleanupMixin,
    DownloadMixin,
    ExportEpubMixin,
    ExportHtmlMixin,
    ExportTxtMixin,
    ProcessMixin,
)
from novel_downloader.plugins.protocols import ExportUI, LoginUI
from novel_downloader.schemas import BookConfig, ExporterConfig

logger = logging.getLogger(__name__)


class _ExportBookFunc(Protocol):
    def __call__(
        self,
        book: BookConfig,
        cfg: ExporterConfig,
        *,
        stage: str | None,
        **kwargs: Any,
    ) -> list[Path]: ...


class _ExportChapterFunc(Protocol):
    def __call__(
        self,
        book_id: str,
        chapter_id: str,
        cfg: ExporterConfig,
        *,
        stage: str | None,
        **kwargs: Any,
    ) -> Path | None: ...


class CommonClient(
    CleanupMixin,
    DownloadMixin,
    ExportEpubMixin,
    ExportHtmlMixin,
    ExportTxtMixin,
    ProcessMixin,
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
            export_func: _ExportBookFunc | None = getattr(self, method_name, None)

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
    ) -> dict[str, Path | None]:
        """
        Persist the assembled chapter to disk.

        :param cfg: Optional ExporterConfig defining export parameters.
        :param formats: Optional list of format strings (e.g., ['epub', 'txt']).
        :return: A mapping from format name to the resulting file path.
        """
        cfg = cfg or ExporterConfig()
        formats = formats or ["txt"]
        results: dict[str, Path | None] = {}

        for fmt in formats:
            method_name = f"_export_chapter_{fmt.lower()}"
            export_func: _ExportChapterFunc | None = getattr(self, method_name, None)

            if not callable(export_func):
                logger.warning("Unsupported chapter export format '%s'", fmt)
                results[fmt] = None
                continue

            try:
                path = export_func(
                    book_id=book_id,
                    chapter_id=chapter_id,
                    cfg=cfg,
                    stage=stage,
                    **kwargs,
                )
                results[fmt] = path

            except Exception as e:
                results[fmt] = None
                logger.warning(
                    "Error exporting chapter (format=%s): %s",
                    fmt,
                    e,
                )

        return results
