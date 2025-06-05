#!/usr/bin/env python3
"""
novel_downloader.core.factory.fetcher
-------------------------------------

This module implements a factory function for retrieving fetcher instances
based on the target novel platform (site).
"""

from collections.abc import Callable

from novel_downloader.config import load_site_rules
from novel_downloader.core.fetchers import (
    BiqugeBrowser,
    BiqugeSession,
    CommonBrowser,
    CommonSession,
    EsjzoneBrowser,
    EsjzoneSession,
    LinovelibBrowser,
    LinovelibSession,
    QianbiBrowser,
    QianbiSession,
    QidianBrowser,
    QidianSession,
    SfacgBrowser,
    SfacgSession,
    YamiboBrowser,
    YamiboSession,
)
from novel_downloader.core.interfaces import FetcherProtocol
from novel_downloader.models import FetcherConfig

FetcherBuilder = Callable[[FetcherConfig], FetcherProtocol]

_site_map: dict[str, dict[str, FetcherBuilder]] = {
    "biquge": {
        "browser": BiqugeBrowser,
        "session": BiqugeSession,
    },
    "esjzone": {
        "browser": EsjzoneBrowser,
        "session": EsjzoneSession,
    },
    "linovelib": {
        "browser": LinovelibBrowser,
        "session": LinovelibSession,
    },
    "qianbi": {
        "browser": QianbiBrowser,
        "session": QianbiSession,
    },
    "qidian": {
        "browser": QidianBrowser,
        "session": QidianSession,
    },
    "sfacg": {
        "browser": SfacgBrowser,
        "session": SfacgSession,
    },
    "yamibo": {
        "browser": YamiboBrowser,
        "session": YamiboSession,
    },
}


def get_fetcher(
    site: str,
    config: FetcherConfig,
) -> FetcherProtocol:
    """
    Returns an FetcherProtocol for the given site.

    :param site: Site name (e.g., 'qidian')
    :param config: Configuration for the requester
    :return: An instance of a requester class
    """
    site_key = site.lower()
    mode = config.mode

    # site-specific
    fetcher_cls = _site_map.get(site_key, {}).get(mode)
    if fetcher_cls is not None:
        return fetcher_cls(config)

    # fallback: use Common based on mode
    site_rules = load_site_rules()
    site_rule = site_rules.get(site_key)
    if site_rule is None:
        raise ValueError(f"Unsupported site: {site}")
    profile = site_rule["profile"]

    if mode == "browser":
        return CommonBrowser(site_key, profile, config)
    return CommonSession(site_key, profile, config)
