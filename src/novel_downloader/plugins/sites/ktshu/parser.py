#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.ktshu.parser
-------------------------------------------

"""

from novel_downloader.plugins.registry import registrar
from novel_downloader.plugins.sites.mangg_net.parser import ManggNetParser


@registrar.register_parser()
class KtshuParser(ManggNetParser):
    """
    Parser for 八一中文网 book pages.
    """

    site_name: str = "ktshu"
