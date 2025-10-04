#!/usr/bin/env python3
"""
novel_downloader.usecases.download
----------------------------------
"""

from novel_downloader.plugins import registrar
from novel_downloader.schemas import (
    BookConfig,
    DownloaderConfig,
    FetcherConfig,
    ParserConfig,
)

from .login import ensure_login
from .protocols import DownloadUI, LoginUI


async def download_books(
    site: str,
    books: list[BookConfig],
    downloader_cfg: DownloaderConfig,
    fetcher_cfg: FetcherConfig,
    parser_cfg: ParserConfig,
    login_ui: LoginUI,
    download_ui: DownloadUI,
    login_config: dict[str, str] | None = None,
) -> None:
    try:
        parser = registrar.get_parser(site, parser_cfg)
        fetcher = registrar.get_fetcher(site, fetcher_cfg)
    except ValueError as e:
        await download_ui.on_site_error(site, e)
        return

    async with fetcher:
        if downloader_cfg.login_required and (
            not await ensure_login(fetcher, login_ui, login_config)
        ):
            return

        downloader = registrar.get_downloader(
            fetcher=fetcher,
            parser=parser,
            site=site,
            config=downloader_cfg,
        )

        for book in books:
            await download_ui.on_start(book)

            try:
                await downloader.download(book, progress_hook=download_ui.on_progress)
                await download_ui.on_complete(book)
            except Exception as e:
                await download_ui.on_book_error(book, e)

        if downloader_cfg.login_required and fetcher.is_logged_in:
            await fetcher.save_state()
