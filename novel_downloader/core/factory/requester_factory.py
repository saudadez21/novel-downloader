#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.factory.requester_factory
-----------------------------------------------

This module implements a factory function for retrieving requester instances
based on the target novel platform (site).

It abstracts the instantiation logic for site-specific requester classes,
allowing clients to obtain the appropriate implementation by passing in a site name.
"""

from novel_downloader.config import RequesterConfig
from novel_downloader.core.interfaces import RequesterProtocol
from novel_downloader.core.requesters import (
    QidianRequester,
)

_site_map = {
    "qidian": QidianRequester,
    # "biquge": BiqugeRequester,
}


def get_requester(site: str, config: RequesterConfig) -> RequesterProtocol:
    """
    Returns a site-specific requester instance.

    :param site: Site name (e.g., 'qidian')
    :param config: Configuration for the requester
    :return: An instance of a requester class
    """
    site = site.lower()
    requester_class = _site_map.get(site)
    if not requester_class:
        raise ValueError(f"Unsupported site: {site}")
    return requester_class(config)
