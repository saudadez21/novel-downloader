#!/usr/bin/env python3
"""
novel_downloader.utils.cache
----------------------------

Provides decorators for caching function results,
specifically optimized for configuration loading functions.
"""

from collections.abc import Callable
from functools import lru_cache, wraps
from typing import Any, TypeVar, cast

T = TypeVar("T", bound=Callable[..., Any])


def cached_load_config(func: T) -> T:
    """
    A decorator to cache the result of a config-loading function.
    Uses LRU cache with maxsize=1.
    """
    cached = lru_cache(maxsize=1)(func)
    wrapped = wraps(func)(cached)
    return cast(T, wrapped)
