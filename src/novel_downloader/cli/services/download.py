#!/usr/bin/env python3
"""
novel_downloader.cli.services.download
--------------------------------------

"""

from novel_downloader.cli import ui
from novel_downloader.core import get_downloader, get_fetcher, get_parser
from novel_downloader.models import (
    BookConfig,
    DownloaderConfig,
    FetcherConfig,
    ParserConfig,
)
from novel_downloader.utils.i18n import t

from .login import ensure_login


async def download_book(
    site: str,
    book: BookConfig,
    downloader_cfg: DownloaderConfig,
    fetcher_cfg: FetcherConfig,
    parser_cfg: ParserConfig,
    login_config: dict[str, str] | None = None,
) -> None:
    await download_books(
        site,
        [book],
        downloader_cfg,
        fetcher_cfg,
        parser_cfg,
        login_config,
    )


async def download_books(
    site: str,
    books: list[BookConfig],
    downloader_cfg: DownloaderConfig,
    fetcher_cfg: FetcherConfig,
    parser_cfg: ParserConfig,
    login_config: dict[str, str] | None = None,
) -> None:
    parser = get_parser(site, parser_cfg)

    async with get_fetcher(site, fetcher_cfg) as fetcher:
        if downloader_cfg.login_required and not await ensure_login(
            fetcher, login_config
        ):
            return

        downloader = get_downloader(
            fetcher=fetcher,
            parser=parser,
            site=site,
            config=downloader_cfg,
        )

        for book in books:
            ui.info(t("download_downloading", book_id=book["book_id"], site=site))

            hook, close = ui.create_progress_hook(
                prefix=t("download_progress_prefix"), unit="chapters"
            )
            try:
                await downloader.download(book, progress_hook=hook)
            finally:
                close()

        if downloader_cfg.login_required and fetcher.is_logged_in:
            await fetcher.save_state()
