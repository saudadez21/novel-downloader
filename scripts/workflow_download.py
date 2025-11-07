#!/usr/bin/env python3
import asyncio
import logging
import os
from collections import defaultdict
from pathlib import Path

from novel_downloader.infra.book_url_resolver import resolve_book_url
from novel_downloader.plugins import registrar
from novel_downloader.schemas import (
    BookConfig,
    ClientConfig,
    ExporterConfig,
)

logger = logging.getLogger()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)

# --- Editable defaults (overridable by ENV) ---
WORKERS = int(os.environ.get("WORKERS", 8))
SITE_KEY = ""
BOOK_IDS = ""
BOOK_URLS = ""
FORMATS = """
txt
epub
"""

# ---------------------------------------------------------------------------


class SimpleDownloadUI:
    def __init__(self, site: str, interval: int = 20) -> None:
        self.site = site
        self.interval = interval

    async def on_start(self, book: BookConfig) -> None:
        logger.info(f"Downloading {self.site} book {book.book_id}...")

    async def on_progress(self, done: int, total: int) -> None:
        if done % self.interval == 0 or done == total:
            logger.info("Progress (%s): %d/%d chapters", self.site, done, total)

    async def on_complete(self, book: BookConfig) -> None:
        logger.info(f"Book {book.book_id} ({self.site}) downloaded.")


class SimpleExportUI:
    def __init__(self, site: str) -> None:
        self.site = site

    def on_start(self, book: BookConfig, fmt: str | None = None) -> None:
        msg = f"Starting export of {book.book_id} ({self.site})"
        if fmt:
            msg += f" -> {fmt}"
        logger.info(msg)

    def on_success(self, book: BookConfig, fmt: str, path: Path) -> None:
        logger.info(
            "Export success: %s (%s) -> %s saved to %s",
            book.book_id,
            self.site,
            fmt,
            path,
        )

    def on_error(self, book: BookConfig, fmt: str | None, error: Exception) -> None:
        fmt = fmt or "default"
        logger.error(
            "Export error: %s (%s) %s: %s",
            book.book_id,
            self.site,
            fmt,
            error,
        )

    def on_unsupported(self, book: BookConfig, fmt: str) -> None:
        logger.warning(
            "Unsupported export format %s for %s (%s)",
            fmt,
            book.book_id,
            self.site,
        )


def get_list(name: str, fallback: str) -> list[str]:
    """Read env var if set, else fallback. Normalize commas/newlines."""
    raw = os.environ.get(name, fallback)
    raw = raw.replace(",", "\n")
    return [s for line in raw.splitlines() if (s := line.strip())]


SITE_KEYS = get_list("SITE_KEY", SITE_KEY)
BOOK_IDS_LIST = get_list("BOOK_IDS", BOOK_IDS)
BOOK_URLS_LIST = get_list("BOOK_URLS", BOOK_URLS)
FORMATS_LIST = get_list("FORMATS", FORMATS)


async def download_books(
    site: str,
    books: list[BookConfig],
    client_cfg: ClientConfig,
) -> None:
    try:
        client = registrar.get_client(site=site, config=client_cfg)
        ui = SimpleDownloadUI(site=site)
    except ValueError as e:
        logger.warning("Init failed for %s: %s", site, e)
        return

    async with client:
        for book in books:
            try:
                await client.download(book, ui=ui)
            except Exception as e:
                logger.warning("Failed to download %s (%s): %s", book.book_id, site, e)


def export_books(
    site: str,
    books: list[BookConfig],
    exporter_cfg: ExporterConfig,
    formats: list[str],
) -> None:
    try:
        client = registrar.get_client(site=site)
        ui = SimpleExportUI(site=site)
    except ValueError as e:
        logger.warning("Init failed for %s: %s", site, e)
        return

    for book in books:
        try:
            client.export(
                book,
                exporter_cfg,
                formats=formats,
                ui=ui,
            )
        except Exception as e:
            logger.warning("Failed to export %s (%s): %s", book.book_id, site, e)


def main() -> None:
    grouped: defaultdict[str, list[BookConfig]] = defaultdict(list)

    # Add from BOOK_URLS
    for url in BOOK_URLS_LIST:
        info = resolve_book_url(url)
        if not info:
            logger.warning("Unresolved URL: %s", url)
            continue
        grouped[info["site_key"]].append(info["book"])

    # Add from SITE_KEYS + BOOK_IDS pairing
    if SITE_KEYS and BOOK_IDS_LIST:
        for site in SITE_KEYS:
            for book_id in BOOK_IDS_LIST:
                grouped[site].append(BookConfig(book_id=book_id))

    if not grouped:
        logger.info("No books to process.")
        return

    client_cfg = ClientConfig()
    exporter_cfg = ExporterConfig()

    async def process_site(site: str, books: list[BookConfig], sem: asyncio.Semaphore):
        async with sem:
            logger.info("Starting downloads for site: %s (%d books)", site, len(books))
            await download_books(site, books, client_cfg)
            logger.info("Finished downloads for site: %s", site)

    async def run_all_downloads():
        sem = asyncio.Semaphore(WORKERS)
        tasks = [
            asyncio.create_task(process_site(site, books, sem))
            for site, books in grouped.items()
        ]
        await asyncio.gather(*tasks)

    try:
        asyncio.run(run_all_downloads())
    except KeyboardInterrupt:
        logger.warning("Interrupted by user, shutting down downloads...")
        return

    # --- Export phase ---
    logger.info("Starting export phase for all sites...")
    for site, books in grouped.items():
        export_books(site, books, exporter_cfg, FORMATS_LIST)
    logger.info("All exports completed.")


if __name__ == "__main__":
    main()
