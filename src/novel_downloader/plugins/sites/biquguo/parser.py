#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.biquguo.parser
---------------------------------------------

"""

from novel_downloader.plugins.registry import registrar
from novel_downloader.plugins.sites.mangg_net.parser import ManggNetParser


@registrar.register_parser()
class BiquguoParser(ManggNetParser):
    """
    Parser for 笔趣阁小说网 book pages.
    """

    site_name: str = "biquguo"
