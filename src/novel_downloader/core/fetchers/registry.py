#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.registry
---------------------------------------

Registry and factory helpers for creating site-specific fetchers.
"""

__all__ = ["register_fetcher", "get_fetcher"]

from collections.abc import Callable, Sequence
from typing import TypeVar

from novel_downloader.core.interfaces import FetcherProtocol
from novel_downloader.models import FetcherConfig

FetcherBuilder = Callable[[FetcherConfig], FetcherProtocol]

F = TypeVar("F", bound=FetcherProtocol)
_FETCHER_MAP: dict[str, FetcherBuilder] = {}


def register_fetcher(
    site_keys: Sequence[str],
) -> Callable[[type[F]], type[F]]:
    """
    Decorator to register a fetcher class under given keys.

    :param site_keys: Sequence of site identifiers
    :param backends: Sequence of backend types
    :return: A class decorator that populates _FETCHER_MAP.
    """

    def decorator(cls: type[F]) -> type[F]:
        for site in site_keys:
            site_lower = site.lower()
            _FETCHER_MAP[site_lower] = cls
        return cls

    return decorator


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
    site_key = site.lower()
    try:
        fetcher_cls = _FETCHER_MAP[site_key]
    except KeyError as err:
        raise ValueError(f"Unsupported site: {site!r}") from err

    return fetcher_cls(config)
