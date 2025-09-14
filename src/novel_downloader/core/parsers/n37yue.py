#!/usr/bin/env python3
"""
novel_downloader.core.parsers.n37yue
------------------------------------

"""

from novel_downloader.core.parsers.mangg_net import ManggNetParser
from novel_downloader.core.parsers.registry import register_parser


@register_parser(
    site_keys=["n37yue"],
)
class N37yueParser(ManggNetParser):
    """
    Parser for 37阅读网 book pages.
    """

    site_name: str = "n37yue"
