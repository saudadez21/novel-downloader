#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.lewenn.parser
--------------------------------------------

"""

from novel_downloader.plugins.common.parser.biquge2 import Biquge2Parser
from novel_downloader.plugins.registry import registrar


@registrar.register_parser()
class LewennParser(Biquge2Parser):
    """
    Parser for 乐文小说网 book pages.
    """

    site_name: str = "lewenn"
    BASE_URL = "https://www.lewenn.net"
    ADS = {
        "记住乐文小说网",
        r"lewenn\.net",
    }
