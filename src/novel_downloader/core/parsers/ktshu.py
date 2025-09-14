#!/usr/bin/env python3
"""
novel_downloader.core.parsers.ktshu
-----------------------------------

"""

from novel_downloader.core.parsers.mangg_net import ManggNetParser
from novel_downloader.core.parsers.registry import register_parser


@register_parser(
    site_keys=["ktshu"],
)
class KtshuParser(ManggNetParser):
    """
    Parser for 八一中文网 book pages.
    """

    site_name: str = "ktshu"
