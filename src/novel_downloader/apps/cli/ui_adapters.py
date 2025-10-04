#!/usr/bin/env python3
"""
novel_downloader.apps.cli.ui_adapters
-------------------------------------
"""

from pathlib import Path
from typing import Any

from novel_downloader.apps.cli import ui
from novel_downloader.infra.i18n import t
from novel_downloader.schemas import BookConfig, LoginField


class CLIDownloadUI:
    def __init__(self) -> None:
        self.completed_books: set[BookConfig] = set()
        self._progress: ui.ProgressUI | None = None

    async def on_start(self, book: BookConfig) -> None:
        ui.info(t("Downloading book {book_id}...").format(book_id=book.book_id))
        self._progress = ui.ProgressUI(prefix=t("Download progress"), unit="chapters")
        self._progress.start()

    async def on_progress(self, done: int, total: int) -> None:
        if self._progress is not None:
            await self._progress.update(done, total)

    async def on_complete(self, book: BookConfig) -> None:
        self.completed_books.add(book)
        if self._progress:
            self._progress.stop()
            self._progress = None
        ui.success(t("Book {book_id} downloaded.").format(book_id=book.book_id))

    async def on_book_error(self, book: BookConfig, error: Exception) -> None:
        if self._progress:
            self._progress.stop()
            self._progress = None
        ui.error(
            t("Failed to download {book_id}: {err}").format(
                book_id=book.book_id, err=error
            )
        )

    async def on_site_error(self, site: str, error: Exception) -> None:
        if self._progress:
            self._progress.stop()
            self._progress = None
        ui.error(t("Site error ({site}): {err}").format(site=site, err=error))


class CLIExportUI:
    def __init__(self) -> None:
        self.completed_books: dict[str, dict[str, Path]] = {}

    def on_start(self, book: BookConfig, fmt: str | None = None) -> None:
        ui.info(t("Exporting book {book_id}...").format(book_id=book.book_id))

    def on_success(self, book: BookConfig, fmt: str, path: Path) -> None:
        self.completed_books.setdefault(book.book_id, {})[fmt] = path
        ui.success(
            t("Book {book_id} exported successfully as {format}.").format(
                book_id=book.book_id, format=fmt
            )
        )

    def on_error(self, book: BookConfig, fmt: str | None, error: Exception) -> None:
        fmt = fmt or "default"
        ui.error(
            t("Failed to export book {book_id} as {format}: {err}").format(
                book_id=book.book_id, format=fmt, err=str(error)
            )
        )

    def on_unsupported(self, book: BookConfig, fmt: str) -> None:
        ui.warn(
            t("Export format '{format}' is not supported for book {book_id}.").format(
                format=fmt, book_id=book.book_id
            )
        )


class CLILoginUI:
    async def prompt(
        self,
        fields: list[LoginField],
        prefill: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        from novel_downloader.infra.cookies import parse_cookies

        prefill = prefill or {}
        result: dict[str, Any] = {}

        for field in fields:
            ui.info(f"\n{t(field.label)} ({field.name})")
            if field.description:
                ui.info(f"{t('Description')}: {t(field.description)}")
            if field.placeholder:
                ui.info(f"{t('Hint')}: {t(field.placeholder)}")

            existing_value = prefill.get(field.name, "").strip()
            if existing_value:
                result[field.name] = existing_value
                ui.info(t("Using configured value."))
                continue

            value: str | dict[str, str] = ""
            for _ in range(5):
                if field.type == "password":
                    value = ui.prompt_password(t("Enter your password"))
                elif field.type == "cookie":
                    raw = ui.prompt(t("Enter your cookies"))
                    value = parse_cookies(raw)
                else:
                    value = ui.prompt(t("Enter a value"))

                if not value and field.default:
                    value = field.default

                if not value and field.required:
                    ui.warn(t("This field is required. Please provide a value."))
                else:
                    break

            result[field.name] = value

        return result

    def on_login_failed(self) -> None:
        ui.error(
            t(
                "Login failed: please check your cookies or account credentials and try again."  # noqa: E501
            )
        )

    def on_login_success(self) -> None:
        ui.success(t("Login successful."))


class CLIConfigUI:
    def on_missing(self, path: Path) -> None:
        ui.warn(t("No config found at {path}.").format(path=str(path.resolve())))

    def on_created(self, path: Path) -> None:
        ui.success(
            t("Created default config at {path}.").format(path=str(path.resolve()))
        )

    def on_invalid(self, error: Exception) -> None:
        ui.error(t("Failed to load configuration: {err}").format(err=str(error)))

    def on_abort(self) -> None:
        ui.error(t("Cannot continue without a config file."))

    def confirm_create(self) -> bool:
        return ui.confirm(t("Would you like to create a default config?"), default=True)


class CLIProcessUI:
    def __init__(self) -> None:
        self._progress: ui.ProgressUI | None = None

    def on_stage_start(self, book: BookConfig, stage: str) -> None:
        if self._progress:
            self._progress.stop()
            self._progress = None

        ui.info(
            t("Stage '{stage}' started for {book_id}.").format(
                stage=stage, book_id=book.book_id
            )
        )
        self._progress = ui.ProgressUI(prefix=f"{t('Stage')} {stage}", unit="chapters")
        self._progress.start()

    def on_stage_progress(
        self, book: BookConfig, stage: str, done: int, total: int
    ) -> None:
        if self._progress:
            self._progress.update_sync(done, total)

    def on_stage_complete(self, book: BookConfig, stage: str) -> None:
        if self._progress:
            self._progress.stop()
            self._progress = None
        ui.success(
            t("Stage '{stage}' completed for {book_id}").format(
                stage=stage, book_id=book.book_id
            )
        )

    def on_missing(self, book: BookConfig, what: str, path: Path) -> None:
        ui.warn(
            t("Missing data ({what}) for {book_id}: {path}").format(
                what=what,
                book_id=book.book_id,
                path=str(path),
            )
        )

    def on_book_error(
        self, book: BookConfig, stage: str | None, error: Exception
    ) -> None:
        if self._progress:
            self._progress.stop()
            self._progress = None

        stage_label = stage or "Unknown"
        ui.error(
            t("Error processing {book_id} at stage '{stage}': {err}").format(
                book_id=book.book_id, stage=stage_label, err=str(error)
            )
        )
