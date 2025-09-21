#!/usr/bin/env python3
"""
novel_downloader.core.parsers.blqudu
------------------------------------

"""

from novel_downloader.core.parsers.lewenn import LewennParser
from novel_downloader.core.parsers.registry import register_parser


@register_parser(
    site_keys=["blqudu"],
)
class BlquduParser(LewennParser):
    """
    Parser for 笔趣读 book pages.
    """

    site_name: str = "blqudu"
    BASE_URL = "https://www.blqudu.cc"
    ADS = {
        "记住笔趣阁",
        r"biqudv\.cc",
    }
