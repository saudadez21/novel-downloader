#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.ciluke.parser
--------------------------------------------

"""

from novel_downloader.plugins.common.parser.biquge1 import Biquge1Parser
from novel_downloader.plugins.registry import registrar


@registrar.register_parser()
class CilukeParser(Biquge1Parser):
    """
    Parser for 思路客 book pages.
    """

    site_name: str = "ciluke"
