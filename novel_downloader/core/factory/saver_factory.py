#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.factory.parser_factory
--------------------------------------------

This module implements a factory function for creating saver instances
based on the site name and parser mode specified in the configuration.

Currently supported:
- Site: 'qidian'
    - QidianSaver

To add support for new sites or modes, extend the `_site_map` accordingly.
"""

from novel_downloader.config import SaverConfig
from novel_downloader.core.interfaces import SaverProtocol
from novel_downloader.core.savers import (
    QidianSaver,
)

_site_map = {
    "qidian": QidianSaver,
    # "biquge": ...
}


def get_saver(site: str, config: SaverConfig) -> SaverProtocol:
    """
    Returns a site-specific saver instance.

    :param site: Site name (e.g., 'qidian')
    :param config: Configuration for the saver
    :return: An instance of a saver class
    """
    site = site.lower()
    saver_class = _site_map.get(site)
    if not saver_class:
        raise ValueError(f"Unsupported site: {site}")
    return saver_class(config)
