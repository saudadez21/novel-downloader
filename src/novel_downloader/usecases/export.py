#!/usr/bin/env python3
"""
novel_downloader.usecases.export
--------------------------------
"""

from collections.abc import Callable
from pathlib import Path

from novel_downloader.plugins import registrar
from novel_downloader.schemas import BookConfig, ExporterConfig

from .protocols import ExportUI


def export_books(
    site: str,
    books: list[BookConfig],
    exporter_cfg: ExporterConfig,
    export_ui: ExportUI,
    formats: list[str] | None = None,
) -> None:
    with registrar.get_exporter(site, exporter_cfg) as exporter:
        for book in books:
            if formats is None:
                export_ui.on_start(book)
                try:
                    paths = exporter.export(book)
                    for fmt, path in paths.items():
                        export_ui.on_success(book, fmt, path)
                except Exception as e:
                    export_ui.on_error(book, "default", e)
                continue

            for fmt in formats:
                export_fn: Callable[[BookConfig], Path | None] | None = getattr(
                    exporter, f"export_as_{fmt.lower()}", None
                )

                if not callable(export_fn):
                    export_ui.on_unsupported(book, fmt)
                    continue

                export_ui.on_start(book, fmt)
                try:
                    fmt_path = export_fn(book)
                    if fmt_path is not None:
                        export_ui.on_success(book, fmt, fmt_path)
                    else:
                        export_ui.on_error(book, fmt, Exception("No path returned"))
                except Exception as e:
                    export_ui.on_error(book, fmt, e)
