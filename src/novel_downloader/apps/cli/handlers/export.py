#!/usr/bin/env python3
"""
novel_downloader.apps.cli.handlers.export
-----------------------------------------

"""

from novel_downloader.apps.cli import ui
from novel_downloader.infra.i18n import t
from novel_downloader.plugins import registrar
from novel_downloader.schemas import BookConfig, ExporterConfig


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
    with registrar.get_exporter(site, exporter_cfg) as exporter:
        for book in books:
            book_id = book["book_id"]

            ui.info(t("Exporting book {book_id}...").format(book_id=book_id))
            if formats is None:
                try:
                    exporter.export(book)
                    ui.success(
                        t(
                            "Book {book_id} exported successfully (default format)."
                        ).format(book_id=book_id)
                    )
                except Exception as e:
                    ui.error(
                        t(
                            "Failed to export book {book_id} with default format: {err}"
                        ).format(book_id=book_id, err=str(e))
                    )
                continue

            for fmt in formats:
                fmt = fmt.lower()
                method_name = f"export_as_{fmt}"
                export_fn = getattr(exporter, method_name, None)

                if not callable(export_fn):
                    ui.warn(
                        t("Export format '{format}' is not supported.").format(
                            format=fmt
                        )
                    )
                    continue

                try:
                    export_fn(book)
                    ui.success(
                        t("Book {book_id} exported successfully as {format}.").format(
                            book_id=book_id, format=fmt
                        )
                    )
                except Exception as e:
                    ui.error(
                        t("Failed to export book {book_id} as {format}: {err}").format(
                            book_id=book_id, format=fmt, err=str(e)
                        )
                    )
