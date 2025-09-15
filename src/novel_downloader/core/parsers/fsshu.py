#!/usr/bin/env python3
"""
novel_downloader.core.parsers.fsshu
-----------------------------------

"""

from novel_downloader.core.parsers.mangg_net import ManggNetParser
from novel_downloader.core.parsers.registry import register_parser


@register_parser(
    site_keys=["fsshu"],
)
class FsshuParser(ManggNetParser):
    """
    Parser for 笔趣阁 book pages.
    """

    site_name: str = "fsshu"
