#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.biquge5.parser
---------------------------------------------

"""

from novel_downloader.plugins.registry import registrar
from novel_downloader.plugins.sites.mangg_net.parser import ManggNetParser


@registrar.register_parser()
class Biquge5Parser(ManggNetParser):
    """
    Parser for 笔趣阁 book pages.
    """

    site_name: str = "biquge5"
