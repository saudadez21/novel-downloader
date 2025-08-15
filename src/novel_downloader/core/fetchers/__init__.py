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
    "AaatxtSession",
    "BiqugeSession",
    "BiquyueduSession",
    "DeqixsSession",
    "EightnovelSession",
    "EsjzoneSession",
    "GuidayeSession",
    "HetushuSession",
    "I25zwSession",
    "Jpxs123Session",
    "LewennSession",
    "LinovelibSession",
    "PiaotiaSession",
    "QbtrSession",
    "QianbiSession",
    "QidianSession",
    "Quanben5Session",
    "SfacgSession",
    "ShencouSession",
    "ShuhaigeSession",
    "TongrenquanSession",
    "TtkanSession",
    "XiaoshuowuSession",
    "XiguashuwuSession",
    "YamiboSession",
]

from .aaatxt import AaatxtSession
from .biquge import BiqugeSession
from .biquyuedu import BiquyueduSession
from .deqixs import DeqixsSession
from .eightnovel import EightnovelSession
from .esjzone import EsjzoneSession
from .guidaye import GuidayeSession
from .hetushu import HetushuSession
from .i25zw import I25zwSession
from .jpxs123 import Jpxs123Session
from .lewenn import LewennSession
from .linovelib import LinovelibSession
from .piaotia import PiaotiaSession
from .qbtr import QbtrSession
from .qianbi import QianbiSession
from .qidian import QidianSession
from .quanben5 import Quanben5Session
from .registry import get_fetcher
from .sfacg import SfacgSession
from .shencou import ShencouSession
from .shuhaige import ShuhaigeSession
from .tongrenquan import TongrenquanSession
from .ttkan import TtkanSession
from .xiaoshuowu import XiaoshuowuSession
from .xiguashuwu import XiguashuwuSession
from .yamibo import YamiboSession
