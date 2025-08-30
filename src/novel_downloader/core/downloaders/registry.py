#!/usr/bin/env python3
"""
novel_downloader.core.downloaders.registry
------------------------------------------

Registry and factory helpers for creating site-specific or common downloaders
"""

__all__ = ["register_downloader", "get_downloader"]

from collections.abc import Callable, Sequence
from typing import TypeVar

from novel_downloader.core.downloaders.common import CommonDownloader
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
D = TypeVar("D", bound=DownloaderProtocol)
_DOWNLOADER_MAP: dict[str, DownloaderBuilder] = {}


def register_downloader(
    site_keys: Sequence[str],
) -> Callable[[type[D]], type[D]]:
    """
    Decorator to register a downloader class under given keys.

    :param site_keys: Sequence of site identifiers
    :return: A class decorator that populates _DOWNLOADER_MAP.
    """

    def decorator(cls: type[D]) -> type[D]:
        for key in site_keys:
            _DOWNLOADER_MAP[key.lower()] = cls
        return cls

    return decorator


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
    try:
        downloader_cls = _DOWNLOADER_MAP[site_key]
    except KeyError:
        return CommonDownloader(fetcher, parser, config, site_key)
    return downloader_cls(fetcher, parser, config)
