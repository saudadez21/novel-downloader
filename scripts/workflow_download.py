#!/usr/bin/env python3
import asyncio
import logging
import os
from collections import defaultdict
from collections.abc import Awaitable, Callable

from novel_downloader.libs.book_url_resolver import resolve_book_url
from novel_downloader.plugins import registrar
from novel_downloader.schemas import (
    BookConfig,
    DownloaderConfig,
    ExporterConfig,
    FetcherConfig,
    ParserConfig,
)

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)


# --- Editable defaults (overridable by ENV) ---
SITE_KEY = ""
BOOK_IDS = """

"""
BOOK_URLS = """

"""
FORMATS = """
txt
epub
"""


def get_list(name: str, fallback: str) -> list[str]:
    """Read env var if set, else fallback. Normalize commas/newlines."""
    raw = os.environ.get(name, fallback)
    raw = raw.replace(",", "\n")
    return [s for line in raw.splitlines() if (s := line.strip())]


SITE_KEYS = get_list("SITE_KEY", SITE_KEY)
BOOK_IDS_LIST = get_list("BOOK_IDS", BOOK_IDS)
BOOK_URLS_LIST = get_list("BOOK_URLS", BOOK_URLS)
FORMATS_LIST = get_list("FORMATS", FORMATS)


def make_progress_hook(
    site: str,
    book_id: str,
    interval: int = 20,
) -> Callable[[int, int], Awaitable[None]]:
    async def progress_hook(done: int, total: int) -> None:
        if done % interval == 0 or done == total:
            logger.info("Progress %s [%s]: %d/%d chapters", book_id, site, done, total)

    return progress_hook


async def download_books(
    site: str,
    books: list[BookConfig],
    downloader_cfg: DownloaderConfig,
    fetcher_cfg: FetcherConfig,
    parser_cfg: ParserConfig,
) -> None:
    try:
        parser = registrar.get_parser(site, parser_cfg)
        fetcher = registrar.get_fetcher(site, fetcher_cfg)
    except ValueError as e:
        logger.warning("Init failed for %s: %s", site, e)
        return

    async with fetcher:
        downloader = registrar.get_downloader(
            fetcher=fetcher,
            parser=parser,
            site=site,
            config=downloader_cfg,
        )

        for book in books:
            logger.info("Downloading %s [%s]", book.book_id, site)
            hook = make_progress_hook(site, book.book_id)

            try:
                await downloader.download(book, progress_hook=hook)
                logger.info("Downloaded %s [%s]", book.book_id, site)
            except Exception as e:
                logger.warning("Failed to download %s [%s]: %s", book.book_id, site, e)


def export_books(
    site: str,
    books: list[BookConfig],
    exporter_cfg: ExporterConfig,
    formats: list[str],
) -> None:
    with registrar.get_exporter(site, exporter_cfg) as exporter:
        for book in books:
            for fmt in formats:
                export_fn = getattr(exporter, f"export_as_{fmt.lower()}", None)
                if not callable(export_fn):
                    logger.warning("Format %s not supported for %s", fmt, site)
                    continue

                try:
                    export_fn(book)
                    logger.info("Exported %s [%s] as %s", book.book_id, site, fmt)
                except Exception as e:
                    logger.warning(
                        "Failed to export %s [%s] as %s: %s", book.book_id, site, fmt, e
                    )


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

    downloader_cfg = DownloaderConfig()
    fetcher_cfg = FetcherConfig()
    parser_cfg = ParserConfig()
    exporter_cfg = ExporterConfig()

    async def run_all():
        for site, books in grouped.items():
            await download_books(site, books, downloader_cfg, fetcher_cfg, parser_cfg)
            export_books(site, books, exporter_cfg, FORMATS_LIST)

    asyncio.run(run_all())


if __name__ == "__main__":
    main()
