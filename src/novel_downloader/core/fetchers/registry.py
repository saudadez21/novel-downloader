#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.registry
---------------------------------------

"""

__all__ = ["register_fetcher", "get_fetcher"]

from collections.abc import Callable, Sequence
from typing import TypeVar

from novel_downloader.core.interfaces import FetcherProtocol
from novel_downloader.models import FetcherConfig

FetcherBuilder = Callable[[FetcherConfig], FetcherProtocol]

F = TypeVar("F", bound=FetcherProtocol)
_FETCHER_MAP: dict[str, dict[str, FetcherBuilder]] = {}


def register_fetcher(
    site_keys: Sequence[str],
    backends: Sequence[str],
) -> Callable[[type[F]], type[F]]:
    """
    Decorator to register a fetcher class under given keys.

    :param site_keys: Sequence of site identifiers
    :param backends:  Sequence of backend types
    :return: A class decorator that populates _FETCHER_MAP.
    """

    def decorator(cls: type[F]) -> type[F]:
        for site in site_keys:
            site_lower = site.lower()
            bucket = _FETCHER_MAP.setdefault(site_lower, {})
            for backend in backends:
                bucket[backend] = cls
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
        backend_map = _FETCHER_MAP[site_key]
    except KeyError as err:
        raise ValueError(f"Unsupported site: {site!r}") from err

    mode = config.mode
    try:
        fetcher_cls = backend_map[mode]
    except KeyError as err:
        raise ValueError(
            f"Unsupported fetcher mode {mode!r} for site {site!r}. "
            f"Available modes: {list(backend_map)}"
        ) from err

    return fetcher_cls(config)
