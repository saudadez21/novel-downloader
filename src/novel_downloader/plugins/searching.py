#!/usr/bin/env python3
"""
novel_downloader.plugins.searching
----------------------------------

"""

__all__ = ["register_searcher", "search", "search_stream"]

import asyncio
import logging
import pkgutil
from collections.abc import AsyncGenerator, Callable, Sequence
from importlib import import_module
from typing import TypeVar

import aiohttp

from novel_downloader.plugins.base.searcher import BaseSearcher
from novel_downloader.schemas import SearchResult

S = TypeVar("S", bound=BaseSearcher)

_LOADED = False
_SEARCHER_REGISTRY: dict[str, type[BaseSearcher]] = {}
_SITES_PKG = "novel_downloader.plugins.sites"

logger = logging.getLogger(__name__)


def register_searcher(site_key: str | None = None) -> Callable[[type[S]], type[S]]:
    """
    Decorator to register a searcher class under given name.
    """

    def decorator(cls: type[S]) -> type[S]:
        key = site_key or cls.__module__.split(".")[-2].lower()
        _SEARCHER_REGISTRY[key] = cls
        return cls

    return decorator


def _load_all_searchers() -> None:
    """
    Attempt to import all site-specific searcher module.
    """
    global _LOADED
    if _LOADED:
        return

    pkg = import_module(_SITES_PKG)
    for _, name, ispkg in pkgutil.iter_modules(pkg.__path__, pkg.__name__ + "."):
        if not ispkg:
            continue
        try:
            import_module(f"{name}.searcher")
        except ModuleNotFoundError:
            continue

    _LOADED = True


async def search(
    keyword: str,
    sites: Sequence[str] | None = None,
    limit: int | None = None,
    per_site_limit: int = 5,
    timeout: float = 5.0,
) -> list[SearchResult]:
    """
    Perform a search for the given keyword across one or more registered sites,
    then aggregate and sort the results by their `priority` value.

    :param keyword: The search term or keyword to query.
    :param sites: An optional sequence of site keys to limit which searchers.
    :param limit: Maximum total number of results to return; if None, return all.
    :param per_site_limit: Maximum number of search results per site.
    :param timeout: Per-request time budget (seconds)
    :return: A flat list of `SearchResult` objects.
    """
    _load_all_searchers()

    keys = list(sites or _SEARCHER_REGISTRY.keys())
    to_call = {_SEARCHER_REGISTRY[key] for key in keys if key in _SEARCHER_REGISTRY}

    site_timeout = aiohttp.ClientTimeout(total=timeout)

    results: list[SearchResult] = []
    async with aiohttp.ClientSession(timeout=site_timeout) as session:
        # Give all searchers the same session
        for cls in to_call:
            cls.configure(session)

        # Kick off all sites in parallel
        coros = [cls.search(keyword, limit=per_site_limit) for cls in to_call]
        site_lists = await asyncio.gather(*coros, return_exceptions=True)

    # Collect successful results; skip failures
    for item in site_lists:
        if isinstance(item, Exception | BaseException):
            continue
        results.extend(item)

    results.sort(key=lambda res: res["priority"])
    return results[:limit] if limit is not None else results


async def search_stream(
    keyword: str,
    sites: Sequence[str] | None = None,
    per_site_limit: int = 5,
    timeout: float = 5.0,
) -> AsyncGenerator[list[SearchResult]]:
    """
    Stream search results from registered sites as soon as each site finishes.

    :param keyword: Search keyword or term.
    :param sites: Optional list of site keys; if None, use all registered sites.
    :param per_site_limit: Maximum number of results per site.
    :param timeout: Timeout per-site (seconds).
    :yield: Lists of `SearchResult` objects from each completed site.
    """
    _load_all_searchers()

    keys = list(sites or _SEARCHER_REGISTRY.keys())
    classes = {_SEARCHER_REGISTRY[k] for k in keys if k in _SEARCHER_REGISTRY}

    site_timeout = aiohttp.ClientTimeout(total=timeout)

    async with aiohttp.ClientSession(timeout=site_timeout) as session:
        for cls in classes:
            cls.configure(session)

        tasks = [
            asyncio.create_task(
                cls.search(keyword, limit=per_site_limit),
                name=f"{cls.__name__}.search",
            )
            for cls in classes
        ]

        try:
            for fut in asyncio.as_completed(tasks):
                try:
                    site_results = await fut
                except asyncio.CancelledError:
                    raise
                except Exception:
                    # a site failed - skip it, keep streaming others
                    continue

                if site_results:
                    yield site_results
        finally:
            # ensure no background tasks are left running after cancel/exit
            for t in tasks:
                if not t.done():
                    t.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
