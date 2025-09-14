#!/usr/bin/env python3
"""
novel_downloader.core.parsers.bxwx9
-----------------------------------

"""

from novel_downloader.core.parsers.mangg_net import ManggNetParser
from novel_downloader.core.parsers.registry import register_parser


@register_parser(
    site_keys=["bxwx9"],
)
class Bxwx9Parser(ManggNetParser):
    """
    Parser for 笔下文学网 book pages.
    """

    site_name: str = "bxwx9"
