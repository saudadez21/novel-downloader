#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.ktshu.parser
-------------------------------------------

"""

from novel_downloader.plugins.common.parser.biquge1 import Biquge1Parser
from novel_downloader.plugins.registry import registrar


@registrar.register_parser()
class KtshuParser(Biquge1Parser):
    """
    Parser for 八一中文网 book pages.
    """

    site_name: str = "ktshu"
