#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.n37yue.parser
--------------------------------------------

"""

from novel_downloader.plugins.common.parser.biquge1 import Biquge1Parser
from novel_downloader.plugins.registry import registrar


@registrar.register_parser()
class N37yueParser(Biquge1Parser):
    """
    Parser for 37阅读网 book pages.
    """

    site_name: str = "n37yue"
