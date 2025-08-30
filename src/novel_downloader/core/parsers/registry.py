#!/usr/bin/env python3
"""
novel_downloader.core.parsers.registry
--------------------------------------

Registry and factory helpers for creating site-specific parsers.
"""

__all__ = ["register_parser", "get_parser"]

from collections.abc import Callable, Sequence
from typing import TypeVar

from novel_downloader.core.interfaces import ParserProtocol
from novel_downloader.models import ParserConfig

ParserBuilder = Callable[[ParserConfig], ParserProtocol]

P = TypeVar("P", bound=ParserProtocol)
_PARSER_MAP: dict[str, ParserBuilder] = {}


def register_parser(
    site_keys: Sequence[str],
) -> Callable[[type[P]], type[P]]:
    """
    Decorator to register a parser class under given keys.

    :param site_keys: Sequence of site identifiers
    :param backends: Sequence of backend types
    :return: A class decorator that populates _PARSER_MAP.
    """

    def decorator(cls: type[P]) -> type[P]:
        for site in site_keys:
            site_lower = site.lower()
            _PARSER_MAP[site_lower] = cls
        return cls

    return decorator


def get_parser(site: str, config: ParserConfig) -> ParserProtocol:
    """
    Returns a site-specific parser instance.

    :param site: Site name (e.g., 'qidian')
    :param config: Configuration for the parser
    :return: An instance of a parser class
    """
    site_key = site.lower()
    try:
        parser_cls = _PARSER_MAP[site_key]
    except KeyError as err:
        raise ValueError(f"Unsupported site: {site!r}") from err

    return parser_cls(config)
