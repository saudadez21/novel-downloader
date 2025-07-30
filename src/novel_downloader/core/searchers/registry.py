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
    keyword: str,
    sites: Sequence[str] | None = None,
    limit: int | None = None,
    per_site_limit: int = 5,
) -> list[SearchResult]:
    """
    Perform a search for the given keyword across one or more registered sites,
    then aggregate and sort the results by their `priority` value.

    :param keyword: The search term or keyword to query.
    :param sites:   An optional sequence of site keys to limit which searchers.
    :param limit:   Maximum total number of results to return; if None, return all.
    :param per_site_limit: Maximum number of search results per site.
    :return:        A flat list of `SearchResult` objects.
    """
    keys = list(sites or _SEARCHER_REGISTRY.keys())
    to_call = {_SEARCHER_REGISTRY[key] for key in keys if key in _SEARCHER_REGISTRY}

    results: list[SearchResult] = []
    for cls in to_call:
        try:
            results.extend(cls.search(keyword, limit=per_site_limit))
        except Exception:
            continue

    results.sort(key=lambda res: res["priority"])
    return results[:limit] if limit is not None else results
