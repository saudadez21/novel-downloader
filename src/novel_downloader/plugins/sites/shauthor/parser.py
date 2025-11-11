#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.shauthor.parser
----------------------------------------------
"""

from novel_downloader.plugins.common.parser.biquge4 import Biquge4Parser
from novel_downloader.plugins.registry import registrar


@registrar.register_parser()
class ShauthorParser(Biquge4Parser):
    """
    Parser for 大众文学 book pages.
    """

    site_name: str = "shauthor"
    BASE_URL = "https://m.shauthor.com"
