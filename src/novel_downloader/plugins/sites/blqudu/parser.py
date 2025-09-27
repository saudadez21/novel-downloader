#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.blqudu.parser
--------------------------------------------

"""

from novel_downloader.plugins.registry import registrar
from novel_downloader.plugins.sites.lewenn.parser import LewennParser


@registrar.register_parser()
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
