#!/usr/bin/env python3
"""
novel_downloader.usecases.search
--------------------------------

"""

__all__ = ["search", "search_stream"]

import asyncio
from collections.abc import AsyncGenerator, Sequence

import aiohttp
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import SearchResult


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
    classes = registrar.get_searcher_classes(sites, load_all_if_none=True)

    if not classes:
        return []

    timeout_cfg = aiohttp.ClientTimeout(total=timeout)
    results: list[SearchResult] = []

    async with aiohttp.ClientSession(timeout=timeout_cfg) as session:
        instances = [cls(session) for cls in classes]
        coros = [inst.search(keyword, limit=per_site_limit) for inst in instances]
        site_lists = await asyncio.gather(*coros, return_exceptions=True)

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
) -> AsyncGenerator[list[SearchResult], None]:
    """
    Stream search results from registered sites as soon as each site finishes.

    :param keyword: Search keyword or term.
    :param sites: Optional list of site keys; if None, use all registered sites.
    :param per_site_limit: Maximum number of results per site.
    :param timeout: Timeout per-site (seconds).
    :yield: Lists of `SearchResult` objects from each completed site.
    """
    classes = registrar.get_searcher_classes(sites, load_all_if_none=True)
    if not classes:
        if False:
            yield []
        return

    timeout_cfg = aiohttp.ClientTimeout(total=timeout)
    async with aiohttp.ClientSession(timeout=timeout_cfg) as session:
        instances = [cls(session) for cls in classes]
        tasks = [
            asyncio.create_task(
                inst.search(keyword, limit=per_site_limit),
                name=f"{cls.__name__}.search",
            )
            for cls, inst in zip(classes, instances, strict=False)
        ]

        try:
            for fut in asyncio.as_completed(tasks):
                try:
                    site_results = await fut
                except asyncio.CancelledError:
                    raise
                except Exception:
                    continue
                if site_results:
                    yield site_results
        finally:
            # ensure no background tasks are left running after cancel/exit
            for t in tasks:
                if not t.done():
                    t.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
