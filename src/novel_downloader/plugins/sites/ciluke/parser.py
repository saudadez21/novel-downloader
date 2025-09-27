#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.ciluke.parser
--------------------------------------------

"""

from novel_downloader.plugins.registry import registrar
from novel_downloader.plugins.sites.mangg_net.parser import ManggNetParser


@registrar.register_parser()
class CilukeParser(ManggNetParser):
    """
    Parser for 思路客 book pages.
    """

    site_name: str = "ciluke"
