#!/usr/bin/env python3
"""
novel_downloader.core.parsers.registry
--------------------------------------

Registry and factory helpers for creating site-specific parsers.
"""

__all__ = ["register_parser", "get_parser"]

from collections.abc import Callable, Sequence
from importlib import import_module
from typing import TypeVar

from novel_downloader.core.interfaces import ParserProtocol
from novel_downloader.models import ParserConfig

ParserBuilder = Callable[[ParserConfig], ParserProtocol]

P = TypeVar("P", bound=ParserProtocol)
_PARSER_MAP: dict[str, ParserBuilder] = {}
_PARSERS_PKG = "novel_downloader.core.parsers"


def register_parser(
    site_keys: Sequence[str],
) -> Callable[[type[P]], type[P]]:
    """
    Decorator to register a parser class under given keys.

    :param site_keys: Sequence of site identifiers
    :return: A class decorator that populates _PARSER_MAP.
    """

    def decorator(cls: type[P]) -> type[P]:
        for site in site_keys:
            site_lower = site.lower()
            _PARSER_MAP[site_lower] = cls
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


def _load_parser(site_key: str) -> None:
    """
    Attempt to import the site-specific parser module.
    """
    modname = f"{_PARSERS_PKG}.{site_key}"
    try:
        import_module(modname)
    except ModuleNotFoundError as e:
        if e.name == modname:
            return
        raise


def get_parser(site: str, config: ParserConfig) -> ParserProtocol:
    """
    Returns a site-specific parser instance.

    :param site: Site name (e.g., 'qidian')
    :param config: Configuration for the parser
    :return: An instance of a parser class
    """
    site_key = _normalize_key(site)

    parser_cls = _PARSER_MAP.get(site_key)
    if parser_cls is None:
        _load_parser(site_key)
        parser_cls = _PARSER_MAP.get(site_key)

    if parser_cls is None:
        raise ValueError(f"Unsupported site: {site!r}")

    return parser_cls(config)
