#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.n37yue.parser
--------------------------------------------

"""

from novel_downloader.plugins.registry import registrar
from novel_downloader.plugins.sites.mangg_net.parser import ManggNetParser


@registrar.register_parser()
class N37yueParser(ManggNetParser):
    """
    Parser for 37阅读网 book pages.
    """

    site_name: str = "n37yue"
