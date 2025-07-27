#!/usr/bin/env python3
"""
novel_downloader.core.fetchers
------------------------------

This package provides fetcher implementations for different novel platforms.
Each submodule corresponds to a specific site and encapsulates the logic needed
to perform network interactions, such as logging in, sending requests,
or interacting with browser/session-based sources.
"""

__all__ = [
    "get_fetcher",
    "BiqugeSession",
    "BiquyueduSession",
    "EsjzoneSession",
    "I25zwSession",
    "LinovelibSession",
    "PiaotiaSession",
    "QianbiSession",
    "QidianSession",
    "SfacgSession",
    "TtkanSession",
    "XiaoshuowuSession",
    "YamiboSession",
]

from .biquge import BiqugeSession
from .biquyuedu import BiquyueduSession
from .esjzone import EsjzoneSession
from .i25zw import I25zwSession
from .linovelib import LinovelibSession
from .piaotia import PiaotiaSession
from .qianbi import QianbiSession
from .qidian import QidianSession
from .registry import get_fetcher
from .sfacg import SfacgSession
from .ttkan import TtkanSession
from .xiaoshuowu import XiaoshuowuSession
from .yamibo import YamiboSession
