#!/usr/bin/env python3
"""
novel_downloader.core.searchers.registry
----------------------------------------

"""

__all__ = ["register_searcher", "search"]

from collections.abc import Callable, Sequence
from typing import TypeVar

from novel_downloader.core.searchers.base import BaseSearcher
from novel_downloader.models import SearchResult

S = TypeVar("S", bound=BaseSearcher)

_SEARCHER_REGISTRY: dict[str, type[BaseSearcher]] = {}


def register_searcher(
    site_keys: Sequence[str],
) -> Callable[[type[S]], type[S]]:
    """
    Decorator to register a searcher class under given name.
    """

    def decorator(cls: type[S]) -> type[S]:
        for key in site_keys:
            _SEARCHER_REGISTRY[key] = cls
        return cls

    return decorator


def search(
    name: str,
    sites: Sequence[str] | None = None,
    limit: int | None = None,
) -> list[SearchResult]:
    """
    Perform a search for the given keyword across one or more registered sites,
    then aggregate and sort the results by their `priority` value.

    :param name:  The search term or keyword to query.
    :param sites: An optional sequence of site keys to limit which searchers.
    :param limit: Maximum total number of results to return; if None, return all.
    :return:      A flat list of `SearchResult` objects.
    """
    keys = list(sites or _SEARCHER_REGISTRY.keys())

    results: list[SearchResult] = []

    for key in keys:
        cls = _SEARCHER_REGISTRY[key]
        try:
            results.extend(cls.search(name))
        except Exception:
            continue

    results.sort(key=lambda res: res["priority"])
    if limit is not None:
        return results[:limit]
    return results
