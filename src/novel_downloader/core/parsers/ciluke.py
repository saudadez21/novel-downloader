#!/usr/bin/env python3
"""
novel_downloader.core.parsers.ciluke
------------------------------------

"""

from novel_downloader.core.parsers.mangg_net import ManggNetParser
from novel_downloader.core.parsers.registry import register_parser


@register_parser(
    site_keys=["ciluke"],
)
class CilukeParser(ManggNetParser):
    """
    Parser for 思路客 book pages.
    """

    site_name: str = "ciluke"
