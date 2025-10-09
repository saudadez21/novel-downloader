#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.mangg_net.parser
-----------------------------------------------

"""

from novel_downloader.plugins.common.parser.biquge1 import Biquge1Parser
from novel_downloader.plugins.registry import registrar


@registrar.register_parser()
class ManggNetParser(Biquge1Parser):
    """
    Parser for 追书网 book pages.
    """

    site_name: str = "mangg_net"
