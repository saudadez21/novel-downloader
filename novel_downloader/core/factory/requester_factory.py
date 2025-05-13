#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.factory.requester_factory
-----------------------------------------------

This module implements a factory function for retrieving requester instances
based on the target novel platform (site).

- get_async_requester -> returns AsyncRequesterProtocol
- get_sync_requester  -> returns RequesterProtocol
- get_requester       -> dispatches to one of the above based on config.mode

To add support for new sites or modes, extend the `_site_map` accordingly.
"""

from typing import Callable, Union

from novel_downloader.config import RequesterConfig, load_site_rules
from novel_downloader.core.interfaces import AsyncRequesterProtocol, RequesterProtocol
from novel_downloader.core.requesters import (
    CommonAsyncSession,
    CommonSession,
    QidianBrowser,
    QidianSession,
)

_site_map: dict[
    str,
    dict[str, Callable[[RequesterConfig], RequesterProtocol]],
] = {
    "qidian": {
        "session": QidianSession,
        "browser": QidianBrowser,
    },
}


def get_async_requester(
    site: str,
    config: RequesterConfig,
) -> AsyncRequesterProtocol:
    """
    Returns an AsyncRequesterProtocol for the given site.

    :param site: Site name (e.g., 'qidian')
    :param config: Configuration for the requester
    :return: An instance of a requester class
    """
    site_key = site.lower()
    site_rules = load_site_rules()
    site_rule = site_rules.get(site_key)
    if site_rule is None:
        raise ValueError(f"Unsupported site: {site}")
    profile = site_rule["profile"]
    return CommonAsyncSession(config, site_key, profile)


def get_sync_requester(
    site: str,
    config: RequesterConfig,
) -> RequesterProtocol:
    """
    Returns a RequesterProtocol for the given site.

    :param site: Site name (e.g., 'qidian')
    :param config: Configuration for the requester
    :return: An instance of a requester class
    """
    site_key = site.lower()
    site_entry = _site_map.get(site_key)

    # site-specific implementation for this mode
    if site_entry:
        cls = site_entry.get(config.mode)
        if cls:
            return cls(config)

    # fallback to CommonSession
    site_rules = load_site_rules()
    site_rule = site_rules.get(site_key)
    if site_rule is None:
        raise ValueError(f"Unsupported site: {site}")
    profile = site_rule["profile"]
    return CommonSession(config, site_key, profile)


def get_requester(
    site: str,
    config: RequesterConfig,
) -> Union[AsyncRequesterProtocol, RequesterProtocol]:
    """
    Dispatches to either get_async_requester or get_sync_requester
    based on config.mode. Treats 'browser' and 'async' as async modes,
    'session' as sync; anything else is an error.

    :param site: Site name (e.g., 'qidian')
    :param config: Configuration for the requester
    :return: An instance of a requester class
    """
    mode = config.mode.lower()
    if mode == "async":
        return get_async_requester(site, config)
    if mode in ("browser", "session"):
        return get_sync_requester(site, config)
    raise ValueError(f"Unknown mode '{config.mode}' for site '{site}'")
