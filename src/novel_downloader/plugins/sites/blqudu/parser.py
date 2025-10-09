#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.blqudu.parser
--------------------------------------------

"""

from novel_downloader.plugins.common.parser.biquge2 import Biquge2Parser
from novel_downloader.plugins.registry import registrar


@registrar.register_parser()
class BlquduParser(Biquge2Parser):
    """
    Parser for 笔趣读 book pages.
    """

    site_name: str = "blqudu"
    BASE_URL = "https://www.blqudu.cc"
    ADS = {
        "记住笔趣阁",
        r"biqudv\.cc",
    }
