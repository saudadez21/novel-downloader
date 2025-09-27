#!/usr/bin/env python3
"""
novel_downloader.apps.cli.handlers.download
-------------------------------------------

"""

from novel_downloader.apps.cli import ui
from novel_downloader.infra.i18n import t
from novel_downloader.plugins import registrar
from novel_downloader.schemas import (
    BookConfig,
    DownloaderConfig,
    FetcherConfig,
    ParserConfig,
)

from .login import ensure_login


async def download_book(
    site: str,
    book: BookConfig,
    downloader_cfg: DownloaderConfig,
    fetcher_cfg: FetcherConfig,
    parser_cfg: ParserConfig,
    login_config: dict[str, str] | None = None,
) -> bool:
    return await download_books(
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
) -> bool:
    parser = registrar.get_parser(site, parser_cfg)

    async with registrar.get_fetcher(site, fetcher_cfg) as fetcher:
        if downloader_cfg.login_required and (
            not await ensure_login(fetcher, login_config)
        ):
            return False

        downloader = registrar.get_downloader(
            fetcher=fetcher,
            parser=parser,
            site=site,
            config=downloader_cfg,
        )

        for book in books:
            ui.info(
                t("Downloading book {book_id} from {site}...").format(
                    book_id=book["book_id"], site=site
                )
            )

            hook, close = ui.create_progress_hook(
                prefix=t("Download progress"), unit="chapters"
            )
            try:
                await downloader.download(book, progress_hook=hook)
            finally:
                close()

        if downloader_cfg.login_required and fetcher.is_logged_in:
            await fetcher.save_state()
    return True
