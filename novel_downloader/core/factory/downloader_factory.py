#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.factory.downloader_factory
------------------------------------------------

This module implements a factory function for creating downloader instances
based on the site name and parser mode specified in the configuration.

Currently supported:
- Site: 'qidian'
    - QidianDownloader

To add support for new sites or modes, extend the `_site_map` accordingly.
"""

from novel_downloader.config import DownloaderConfig, load_site_rules
from novel_downloader.core.downloaders import (
    CommonDownloader,
    QidianDownloader,
)
from novel_downloader.core.interfaces import (
    DownloaderProtocol,
    ParserProtocol,
    RequesterProtocol,
    SaverProtocol,
)

_site_map = {
    "qidian": QidianDownloader,
    # "biquge": ...
}


def get_downloader(
    requester: RequesterProtocol,
    parser: ParserProtocol,
    saver: SaverProtocol,
    site: str,
    config: DownloaderConfig,
) -> DownloaderProtocol:
    """
    Returns a site-specific downloader instance.

    :param requester: Requester implementation
    :param parser: Parser implementation
    :param saver: Saver implementation
    :param site: Site name (e.g., 'qidian')
    :param config: Downloader configuration
    :return: An instance of a downloader class
    """
    site_key = site.lower()

    if site_key in _site_map:
        downloader_class = _site_map[site_key]
        return downloader_class(requester, parser, saver, config)

    site_rules = load_site_rules()
    if site_key not in site_rules:
        raise ValueError(f"Unsupported site: {site}")

    return CommonDownloader(requester, parser, saver, config, site_key)
