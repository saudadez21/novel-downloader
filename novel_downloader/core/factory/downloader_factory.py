#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.factory.downloader_factory
------------------------------------------------

This module implements a factory function for creating downloader instances
based on the site name and parser mode specified in the configuration.

- get_async_downloader -> always returns a CommonAsyncDownloader
- get_sync_downloader  -> returns a site-specific downloader or CommonDownloader
- get_downloader       -> dispatches to one of the above based on config.mode

To add support for new sites or modes, extend the `_site_map` accordingly.
"""

from typing import Union

from novel_downloader.config import DownloaderConfig, load_site_rules
from novel_downloader.core.downloaders import (
    CommonAsyncDownloader,
    CommonDownloader,
    QidianDownloader,
)
from novel_downloader.core.interfaces import (
    AsyncDownloaderProtocol,
    AsyncRequesterProtocol,
    DownloaderProtocol,
    ParserProtocol,
    RequesterProtocol,
    SaverProtocol,
)

_site_map = {
    "qidian": QidianDownloader,
    # "biquge": ...
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
    :raises TypeError: If the provided requester does not match the required protocol
                    for the chosen mode (sync vs async).
    """
    site_key = site.lower()

    if not isinstance(requester, AsyncRequesterProtocol):
        raise TypeError("Async mode requires an AsyncRequesterProtocol")

    site_rules = load_site_rules()
    site_rule = site_rules.get(site_key)
    if site_rule is None:
        raise ValueError(f"Unsupported site: {site}")

    return CommonAsyncDownloader(requester, parser, saver, config, site_key)


def get_sync_downloader(
    requester: RequesterProtocol,
    parser: ParserProtocol,
    saver: SaverProtocol,
    site: str,
    config: DownloaderConfig,
) -> DownloaderProtocol:
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
    :raises TypeError: If the provided requester does not match the required protocol
                    for the chosen mode (sync vs async).
    """
    site_key = site.lower()

    if not isinstance(requester, RequesterProtocol):
        raise TypeError("Sync mode requires a RequesterProtocol")

    # site-specific
    if site_key in _site_map:
        return _site_map[site_key](requester, parser, saver, config)

    # fallback
    site_rules = load_site_rules()
    site_rule = site_rules.get(site_key)
    if site_rule is None:
        raise ValueError(f"Unsupported site: {site}")

    return CommonDownloader(requester, parser, saver, config, site_key)


def get_downloader(
    requester: Union[AsyncRequesterProtocol, RequesterProtocol],
    parser: ParserProtocol,
    saver: SaverProtocol,
    site: str,
    config: DownloaderConfig,
) -> Union[AsyncDownloaderProtocol, DownloaderProtocol]:
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
    :raises TypeError: If the provided requester does not match the required protocol
                    for the chosen mode (sync vs async).
    """
    mode = config.mode.lower()
    if mode == "async":
        if not isinstance(requester, AsyncRequesterProtocol):
            raise TypeError("Async mode requires an AsyncRequesterProtocol")
        return get_async_downloader(requester, parser, saver, site, config)
    if mode in ("browser", "session"):
        if not isinstance(requester, RequesterProtocol):
            raise TypeError("Sync mode requires a RequesterProtocol")
        return get_sync_downloader(requester, parser, saver, site, config)
    raise ValueError(f"Unknown mode '{config.mode}' for site '{site}'")
