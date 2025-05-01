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

from novel_downloader.config import RequesterConfig, load_site_rules
from novel_downloader.core.interfaces import RequesterProtocol
from novel_downloader.core.requesters import (
    CommonSession,
    QidianBrowser,
    QidianSession,
)

_site_map = {
    "qidian": {
        "browser": QidianBrowser,
        "session": QidianSession,
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
    site_key = site.lower()

    site_entry = _site_map.get(site_key)
    if site_entry:
        requester_class = (
            site_entry.get(config.mode) if isinstance(site_entry, dict) else site_entry
        )
        if requester_class:
            return requester_class(config)
        raise ValueError(f"Unsupported mode '{config.mode}' for site '{site}'")

    # Fallback: Load site rules
    site_rules = load_site_rules()
    site_rule = site_rules.get(site_key)
    if site_rule is None:
        raise ValueError(f"Unsupported site: {site}")

    site_profile = site_rule["profile"]
    return CommonSession(config, site_key, site_profile)
