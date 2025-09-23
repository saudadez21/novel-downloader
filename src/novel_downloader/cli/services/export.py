#!/usr/bin/env python3
"""
novel_downloader.cli.services.export
------------------------------------

"""

from novel_downloader.cli import ui
from novel_downloader.core import get_exporter
from novel_downloader.models import BookConfig, ExporterConfig
from novel_downloader.utils.i18n import t


def export_book(
    site: str,
    book: BookConfig,
    exporter_cfg: ExporterConfig,
    formats: list[str] | None = None,
) -> None:
    export_books(site, [book], exporter_cfg, formats)


def export_books(
    site: str,
    books: list[BookConfig],
    exporter_cfg: ExporterConfig,
    formats: list[str] | None = None,
) -> None:
    with get_exporter(site, exporter_cfg) as exporter:
        for book in books:
            book_id = book["book_id"]

            ui.info(t("export_processing", book_id=book_id))
            if formats is None:
                # based on config
                try:
                    exporter.export(book_id)
                    ui.success(t("export_success", book_id=book_id, format="default"))
                except Exception as e:
                    ui.error(
                        t(
                            "export_failed",
                            book_id=book_id,
                            format="default",
                            err=str(e),
                        )
                    )
                continue

            for fmt in formats:
                fmt = fmt.lower()
                method_name = f"export_as_{fmt}"
                export_fn = getattr(exporter, method_name, None)

                if not callable(export_fn):
                    ui.warn(t("export_unsupported", format=fmt))
                    continue

                try:
                    export_fn(book_id)
                    ui.success(t("export_success", book_id=book_id, format=fmt))
                except Exception as e:
                    ui.error(
                        t("export_failed", book_id=book_id, format=fmt, err=str(e))
                    )
