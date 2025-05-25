#!/usr/bin/env python3
"""
novel_downloader.core.factory.downloader_factory
------------------------------------------------

This module implements a factory function for creating downloader instances
based on the site name and parser mode specified in the configuration.
"""

from collections.abc import Callable
from typing import cast

from novel_downloader.config import DownloaderConfig, load_site_rules
from novel_downloader.core.downloaders import (
    BiqugeAsyncDownloader,
    BiqugeDownloader,
    CommonAsyncDownloader,
    CommonDownloader,
    EsjzoneAsyncDownloader,
    EsjzoneDownloader,
    QianbiAsyncDownloader,
    QianbiDownloader,
    QidianDownloader,
    SfacgAsyncDownloader,
    SfacgDownloader,
    YamiboAsyncDownloader,
    YamiboDownloader,
)
from novel_downloader.core.interfaces import (
    AsyncDownloaderProtocol,
    AsyncRequesterProtocol,
    ParserProtocol,
    SaverProtocol,
    SyncDownloaderProtocol,
    SyncRequesterProtocol,
)

AsyncDownloaderBuilder = Callable[
    [AsyncRequesterProtocol, ParserProtocol, SaverProtocol, DownloaderConfig],
    AsyncDownloaderProtocol,
]

SyncDownloaderBuilder = Callable[
    [SyncRequesterProtocol, ParserProtocol, SaverProtocol, DownloaderConfig],
    SyncDownloaderProtocol,
]

_async_site_map: dict[str, AsyncDownloaderBuilder] = {
    "biquge": BiqugeAsyncDownloader,
    "esjzone": EsjzoneAsyncDownloader,
    "qianbi": QianbiAsyncDownloader,
    "sfacg": SfacgAsyncDownloader,
    "yamibo": YamiboAsyncDownloader,
}
_sync_site_map: dict[str, SyncDownloaderBuilder] = {
    "biquge": BiqugeDownloader,
    "esjzone": EsjzoneDownloader,
    "qianbi": QianbiDownloader,
    "qidian": QidianDownloader,
    "sfacg": SfacgDownloader,
    "yamibo": YamiboDownloader,
}


def get_async_downloader(
    requester: AsyncRequesterProtocol,
    parser: ParserProtocol,
    saver: SaverProtocol,
    site: str,
    config: DownloaderConfig,
) -> AsyncDownloaderProtocol:
    """
    Returns an AsyncDownloaderProtocol for the given site.

    :param requester: Requester implementation
    :param parser: Parser implementation
    :param saver: Saver implementation
    :param site: Site name (e.g., 'qidian')
    :param config: Downloader configuration

    :return: An instance of a downloader class

    :raises ValueError: If a site-specific downloader does not support async mode.
    :raises TypeError: If the provided requester does not match the required protocol.
    """
    site_key = site.lower()

    if not isinstance(requester, AsyncRequesterProtocol):
        raise TypeError("Async mode requires an AsyncRequesterProtocol")

    # site-specific
    if site_key in _async_site_map:
        return _async_site_map[site_key](requester, parser, saver, config)

    # fallback
    site_rules = load_site_rules()
    site_rule = site_rules.get(site_key)
    if site_rule is None:
        raise ValueError(f"Unsupported site: {site}")

    return CommonAsyncDownloader(requester, parser, saver, config, site_key)


def get_sync_downloader(
    requester: SyncRequesterProtocol,
    parser: ParserProtocol,
    saver: SaverProtocol,
    site: str,
    config: DownloaderConfig,
) -> SyncDownloaderProtocol:
    """
    Returns a DownloaderProtocol for the given site.
    First tries a site-specific downloader (e.g. QidianDownloader),
    otherwise falls back to CommonDownloader.

    :param requester: Requester implementation
    :param parser: Parser implementation
    :param saver: Saver implementation
    :param site: Site name (e.g., 'qidian')
    :param config: Downloader configuration

    :return: An instance of a downloader class

    :raises ValueError: If a site-specific downloader does not support async mode.
    :raises TypeError: If the provided requester does not match the required protocol.
    """
    site_key = site.lower()

    if not isinstance(requester, SyncRequesterProtocol):
        raise TypeError("Sync mode requires a RequesterProtocol")

    # site-specific
    if site_key in _sync_site_map:
        return _sync_site_map[site_key](requester, parser, saver, config)

    # fallback
    site_rules = load_site_rules()
    site_rule = site_rules.get(site_key)
    if site_rule is None:
        raise ValueError(f"Unsupported site: {site}")

    return CommonDownloader(requester, parser, saver, config, site_key)


def get_downloader(
    requester: AsyncRequesterProtocol | SyncRequesterProtocol,
    parser: ParserProtocol,
    saver: SaverProtocol,
    site: str,
    config: DownloaderConfig,
) -> AsyncDownloaderProtocol | SyncDownloaderProtocol:
    """
    Dispatches to get_async_downloader if config.mode == 'async',
    otherwise to get_sync_downloader.

    :param requester: Requester implementation
    :param parser: Parser implementation
    :param saver: Saver implementation
    :param site: Site name (e.g., 'qidian')
    :param config: Downloader configuration

    :return: An instance of a downloader class

    :raises ValueError: If a site-specific downloader does not support async mode.
    :raises TypeError: If the provided requester does not match the required protocol.
    """
    if requester.is_async():
        if config.mode.lower() != "async":
            raise TypeError("Requester is async, but config.mode is not 'async'")
        async_requester = cast(AsyncRequesterProtocol, requester)
        return get_async_downloader(async_requester, parser, saver, site, config)
    else:
        if config.mode.lower() not in ("browser", "session"):
            raise TypeError(
                "Requester is sync, but config.mode is not 'browser' or 'session'"
            )
        sync_requester = cast(SyncRequesterProtocol, requester)
        return get_sync_downloader(sync_requester, parser, saver, site, config)
