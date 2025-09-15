#!/usr/bin/env python3
"""
novel_downloader.core.parsers.biquguo
-------------------------------------

"""

from novel_downloader.core.parsers.mangg_net import ManggNetParser
from novel_downloader.core.parsers.registry import register_parser


@register_parser(
    site_keys=["biquguo"],
)
class BiquguoParser(ManggNetParser):
    """
    Parser for 笔趣阁小说网 book pages.
    """

    site_name: str = "biquguo"
