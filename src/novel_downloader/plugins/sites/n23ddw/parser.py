#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.n23ddw.parser
--------------------------------------------

"""

from novel_downloader.plugins.common.parser.biquge3 import Biquge3Parser
from novel_downloader.plugins.registry import registrar


@registrar.register_parser()
class N23ddwParser(Biquge3Parser):
    """
    Parser for 顶点小说网 book pages.
    """

    site_name: str = "n23ddw"
