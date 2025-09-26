#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.registry
---------------------------------------

Registry and factory helpers for creating site-specific fetchers.
"""

__all__ = ["register_fetcher", "get_fetcher"]

from collections.abc import Callable, Sequence
from importlib import import_module
from typing import TypeVar

from novel_downloader.core.interfaces import FetcherProtocol
from novel_downloader.models import FetcherConfig

FetcherBuilder = Callable[[FetcherConfig], FetcherProtocol]

F = TypeVar("F", bound=FetcherProtocol)
_FETCHER_MAP: dict[str, FetcherBuilder] = {}
_FETCHERS_PKG = "novel_downloader.core.fetchers"


def register_fetcher(
    site_keys: Sequence[str],
) -> Callable[[type[F]], type[F]]:
    """
    Decorator to register a fetcher class under given keys.

    :param site_keys: Sequence of site identifiers
    :return: A class decorator that populates _FETCHER_MAP.
    """

    def decorator(cls: type[F]) -> type[F]:
        for site in site_keys:
            site_lower = site.lower()
            _FETCHER_MAP[site_lower] = cls
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


def _import_fetcher(site_key: str) -> None:
    """
    Attempt to import the site-specific fetcher module.
    """
    modname = f"{_FETCHERS_PKG}.{site_key}"
    try:
        import_module(modname)
    except ModuleNotFoundError as e:
        if e.name == modname:
            return
        raise


def get_fetcher(
    site: str,
    config: FetcherConfig,
) -> FetcherProtocol:
    """
    Returns an FetcherProtocol for the given site.

    :param site: Site name (e.g., 'qidian')
    :param config: Configuration for the requester
    :return: An instance of a requester class
    """
    site_key = _normalize_key(site)

    fetcher_cls = _FETCHER_MAP.get(site_key)
    if fetcher_cls is None:
        _import_fetcher(site_key)
        fetcher_cls = _FETCHER_MAP.get(site_key)

    if fetcher_cls is None:
        raise ValueError(f"Unsupported site: {site!r}")

    return fetcher_cls(config)
