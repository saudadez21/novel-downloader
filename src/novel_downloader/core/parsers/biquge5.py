#!/usr/bin/env python3
"""
novel_downloader.core.parsers.biquge5
-------------------------------------

"""

from novel_downloader.core.parsers.mangg_net import ManggNetParser
from novel_downloader.core.parsers.registry import register_parser


@register_parser(
    site_keys=["biquge5"],
)
class Biquge5Parser(ManggNetParser):
    """
    Parser for 笔趣阁 book pages.
    """

    site_name: str = "biquge5"
