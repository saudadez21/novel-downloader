#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.n69hao.parser
--------------------------------------------
"""

from novel_downloader.plugins.common.parser.biquge3 import Biquge3Parser
from novel_downloader.plugins.registry import registrar


@registrar.register_parser()
class N69haoParser(Biquge3Parser):
    """
    Parser for 69书吧 book pages.
    """

    site_name: str = "n69hao"
