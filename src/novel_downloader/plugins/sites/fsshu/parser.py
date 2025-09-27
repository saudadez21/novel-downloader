#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.fsshu.parser
-------------------------------------------

"""

from novel_downloader.plugins.registry import registrar
from novel_downloader.plugins.sites.mangg_net.parser import ManggNetParser


@registrar.register_parser()
class FsshuParser(ManggNetParser):
    """
    Parser for 笔趣阁 book pages.
    """

    site_name: str = "fsshu"
