#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.bxwx9.parser
-------------------------------------------

"""

from novel_downloader.plugins.registry import registrar
from novel_downloader.plugins.sites.mangg_net.parser import ManggNetParser


@registrar.register_parser()
class Bxwx9Parser(ManggNetParser):
    """
    Parser for 笔下文学网 book pages.
    """

    site_name: str = "bxwx9"
