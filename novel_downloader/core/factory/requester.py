#!/usr/bin/env python3
"""
novel_downloader.core.factory.requester_factory
-----------------------------------------------

This module implements a factory function for retrieving requester instances
based on the target novel platform (site).
"""

from collections.abc import Callable

from novel_downloader.config import RequesterConfig, load_site_rules
from novel_downloader.core.interfaces import (
    AsyncRequesterProtocol,
    SyncRequesterProtocol,
)
from novel_downloader.core.requesters import (
    BiqugeAsyncSession,
    BiqugeSession,
    CommonAsyncSession,
    CommonSession,
    EsjzoneAsyncSession,
    EsjzoneSession,
    QianbiAsyncSession,
    QianbiSession,
    QidianBrowser,
    QidianSession,
    SfacgAsyncSession,
    SfacgSession,
    YamiboAsyncSession,
    YamiboSession,
)

AsyncRequesterBuilder = Callable[[RequesterConfig], AsyncRequesterProtocol]
SyncRequesterBuilder = Callable[[RequesterConfig], SyncRequesterProtocol]


_async_site_map: dict[str, AsyncRequesterBuilder] = {
    "biquge": BiqugeAsyncSession,
    "esjzone": EsjzoneAsyncSession,
    "qianbi": QianbiAsyncSession,
    "sfacg": SfacgAsyncSession,
    "yamibo": YamiboAsyncSession,
}
_sync_site_map: dict[
    str,
    dict[str, SyncRequesterBuilder],
] = {
    "biquge": {
        "session": BiqugeSession,
    },
    "esjzone": {
        "session": EsjzoneSession,
    },
    "qianbi": {
        "session": QianbiSession,
    },
    "qidian": {
        "session": QidianSession,
        "browser": QidianBrowser,
    },
    "sfacg": {
        "session": SfacgSession,
    },
    "yamibo": {
        "session": YamiboSession,
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

    # site-specific
    if site_key in _async_site_map:
        return _async_site_map[site_key](config)

    # fallback
    site_rules = load_site_rules()
    site_rule = site_rules.get(site_key)
    if site_rule is None:
        raise ValueError(f"Unsupported site: {site}")
    profile = site_rule["profile"]
    return CommonAsyncSession(config, site_key, profile)


def get_sync_requester(
    site: str,
    config: RequesterConfig,
) -> SyncRequesterProtocol:
    """
    Returns a RequesterProtocol for the given site.

    :param site: Site name (e.g., 'qidian')
    :param config: Configuration for the requester
    :return: An instance of a requester class
    """
    site_key = site.lower()
    site_entry = _sync_site_map.get(site_key)

    # site-specific
    if site_entry:
        cls = site_entry.get(config.mode)
        if cls:
            return cls(config)

    # fallback
    site_rules = load_site_rules()
    site_rule = site_rules.get(site_key)
    if site_rule is None:
        raise ValueError(f"Unsupported site: {site}")
    profile = site_rule["profile"]
    return CommonSession(config, site_key, profile)


def get_requester(
    site: str,
    config: RequesterConfig,
) -> AsyncRequesterProtocol | SyncRequesterProtocol:
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
