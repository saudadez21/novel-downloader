#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.factory.parser_factory
--------------------------------------------

This module implements a factory function for creating parser instances
based on the site name and parser mode specified in the configuration.

Currently supported:
- Site: 'qidian'
    - Modes:
        - 'browser': QidianBrowserParser
        - 'session': (Not implemented yet)

To add support for new sites or modes, extend the `_site_map` accordingly.
"""

from novel_downloader.config import ParserConfig
from novel_downloader.core.interfaces import ParserProtocol
from novel_downloader.core.parsers import (
    QidianBrowserParser,
)

_site_map = {
    "qidian": {
        "browser": QidianBrowserParser,
        # "session": QidianSessionParser,
    },
    # "biquge": ...
}


def get_parser(site: str, config: ParserConfig) -> ParserProtocol:
    """
    Returns a site-specific parser instance.

    :param site: Site name (e.g., 'qidian')
    :param config: Configuration for the parser
    :return: An instance of a parser class
    """
    site = site.lower()
    site_entry = _site_map.get(site)
    if not site_entry:
        raise ValueError(f"Unsupported site: {site}")

    if isinstance(site_entry, dict):
        parser_class = site_entry.get(config.mode)
        if not parser_class:
            raise ValueError(f"Unsupported mode '{config.mode}' for site '{site}'")
    else:
        parser_class = site_entry

    return parser_class(config)
