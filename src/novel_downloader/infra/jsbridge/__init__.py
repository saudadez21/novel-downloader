#!/usr/bin/env python3
"""
novel_downloader.infra.jsbridge
-------------------------------

Provides NodeDecryptor, which ensures a Node.js environment,
downloads or installs the required JS modules (Fock + decrypt script),
and invokes a Node.js subprocess to decrypt chapter content.
"""

__all__ = ["get_decryptor"]

from .decryptor import get_decryptor
