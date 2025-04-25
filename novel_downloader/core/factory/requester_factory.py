#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.factory.requester_factory
-----------------------------------------------

This module implements a factory function for retrieving requester instances
based on the target novel platform (site).

Currently supported:
- Site: 'qidian'
    - Modes:
        - 'browser': QidianBrowser
        - 'session': (Not implemented yet)

To add support for new sites or modes, extend the `_site_map` accordingly.
"""

from novel_downloader.config import RequesterConfig
from novel_downloader.core.interfaces import RequesterProtocol
from novel_downloader.core.requesters import (
    QidianBrowser,
)

_site_map = {
    "qidian": {
        "browser": QidianBrowser,
        # "session": QidianSession,
    },
    # "biquge": ...
}


def get_requester(site: str, config: RequesterConfig) -> RequesterProtocol:
    """
    Returns a site-specific requester instance.

    :param site: Site name (e.g., 'qidian')
    :param config: Configuration for the requester
    :return: An instance of a requester class
    """
    site = site.lower()
    site_entry = _site_map.get(site)
    if not site_entry:
        raise ValueError(f"Unsupported site: {site}")

    if isinstance(site_entry, dict):
        requester_class = site_entry.get(config.mode)
        if not requester_class:
            raise ValueError(f"Unsupported mode '{config.mode}' for site '{site}'")
    else:
        requester_class = site_entry

    return requester_class(config)
