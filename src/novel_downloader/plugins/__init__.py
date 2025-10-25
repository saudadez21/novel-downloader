#!/usr/bin/env python3
"""
novel_downloader.plugins
------------------------

Plugin system core. Includes protocols, site implementations,
common utilities, and the plugin registry.
"""

__all__ = [
    "registrar",
    "ClientProtocol",
    "FetcherProtocol",
    "ParserProtocol",
]

from .protocols import (
    ClientProtocol,
    FetcherProtocol,
    ParserProtocol,
)
from .registry import registrar
