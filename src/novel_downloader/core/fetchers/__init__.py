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
    "EightnovelSession",
    "EsjzoneSession",
    "GuidayeSession",
    "HetushuSession",
    "I25zwSession",
    "LinovelibSession",
    "PiaotiaSession",
    "QbtrSession",
    "QianbiSession",
    "QidianSession",
    "Quanben5Session",
    "SfacgSession",
    "ShencouSession",
    "TongrenquanSession",
    "TtkanSession",
    "XiaoshuowuSession",
    "YamiboSession",
]

from .biquge import BiqugeSession
from .biquyuedu import BiquyueduSession
from .eightnovel import EightnovelSession
from .esjzone import EsjzoneSession
from .guidaye import GuidayeSession
from .hetushu import HetushuSession
from .i25zw import I25zwSession
from .linovelib import LinovelibSession
from .piaotia import PiaotiaSession
from .qbtr import QbtrSession
from .qianbi import QianbiSession
from .qidian import QidianSession
from .quanben5 import Quanben5Session
from .registry import get_fetcher
from .sfacg import SfacgSession
from .shencou import ShencouSession
from .tongrenquan import TongrenquanSession
from .ttkan import TtkanSession
from .xiaoshuowu import XiaoshuowuSession
from .yamibo import YamiboSession
