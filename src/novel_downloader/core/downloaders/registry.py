#!/usr/bin/env python3
"""
novel_downloader.core.downloaders.registry
------------------------------------------

Registry and factory helpers for creating site-specific or common downloaders
"""

__all__ = ["register_downloader", "get_downloader"]

from collections.abc import Callable, Sequence
from importlib import import_module
from typing import TypeVar

from novel_downloader.core.interfaces import (
    DownloaderProtocol,
    FetcherProtocol,
    ParserProtocol,
)
from novel_downloader.models import DownloaderConfig

DownloaderBuilder = Callable[
    [FetcherProtocol, ParserProtocol, DownloaderConfig, str],
    DownloaderProtocol,
]
D = TypeVar("D", bound=DownloaderProtocol)
_DOWNLOADER_MAP: dict[str, DownloaderBuilder] = {}
_DOWNLOADERS_PKG = "novel_downloader.core.downloaders"


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


def _normalize_key(site_key: str) -> str:
    """
    Normalize a site key to the expected module basename:
      * lowercase
      * if first char is a digit, prefix with 'n'
    """
    key = site_key.strip().lower()
    if not key:
        raise ValueError("Site key cannot be empty")
    if key[0].isdigit():
        return f"n{key}"
    return key


def _load_downloader(site_key: str) -> None:
    """
    Attempt to import the site-specific downloader module.
    """
    modname = f"{_DOWNLOADERS_PKG}.{site_key}"
    try:
        import_module(modname)
    except ModuleNotFoundError as e:
        if e.name == modname:
            return
        raise


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
    site_key = _normalize_key(site)

    downloader_cls = _DOWNLOADER_MAP.get(site_key)
    if downloader_cls is None:
        _load_downloader(site_key)
        downloader_cls = _DOWNLOADER_MAP.get(site_key)

    if downloader_cls is None:
        from novel_downloader.core.downloaders.common import CommonDownloader

        return CommonDownloader(fetcher, parser, config, site_key)

    return downloader_cls(fetcher, parser, config, site_key)
