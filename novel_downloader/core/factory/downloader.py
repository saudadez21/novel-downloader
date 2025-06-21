#!/usr/bin/env python3
"""
novel_downloader.core.factory.downloader
----------------------------------------

This module implements a factory function for creating downloader instances
based on the site name and parser mode specified in the configuration.
"""

from collections.abc import Callable

from novel_downloader.config import load_site_rules
from novel_downloader.core.downloaders import (
    BiqugeDownloader,
    CommonDownloader,
    EsjzoneDownloader,
    LinovelibDownloader,
    QianbiDownloader,
    QidianDownloader,
    SfacgDownloader,
    YamiboDownloader,
)
from novel_downloader.core.interfaces import (
    DownloaderProtocol,
    FetcherProtocol,
    ParserProtocol,
)
from novel_downloader.models import DownloaderConfig

DownloaderBuilder = Callable[
    [FetcherProtocol, ParserProtocol, DownloaderConfig],
    DownloaderProtocol,
]

_site_map: dict[str, DownloaderBuilder] = {
    "biquge": BiqugeDownloader,
    "esjzone": EsjzoneDownloader,
    "linovelib": LinovelibDownloader,
    "qianbi": QianbiDownloader,
    "qidian": QidianDownloader,
    "sfacg": SfacgDownloader,
    "yamibo": YamiboDownloader,
}


def get_downloader(
    fetcher: FetcherProtocol,
    parser: ParserProtocol,
    site: str,
    config: DownloaderConfig,
) -> DownloaderProtocol:
    """
    Returns an DownloaderProtocol for the given site.

    :param fetcher: Fetcher implementation
    :param parser: Parser implementation
    :param site: Site name (e.g., 'qidian')
    :param config: Downloader configuration

    :return: An instance of a downloader class
    """
    site_key = site.lower()

    # site-specific
    if site_key in _site_map:
        return _site_map[site_key](fetcher, parser, config)

    # fallback
    site_rules = load_site_rules()
    if site_key not in site_rules:
        raise ValueError(f"Unsupported site: {site}")

    return CommonDownloader(fetcher, parser, config, site_key)
