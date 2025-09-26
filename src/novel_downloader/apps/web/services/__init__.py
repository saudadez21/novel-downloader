#!/usr/bin/env python3
"""
novel_downloader.apps.web.services
----------------------------------

Convenience re-exports for web UI services
"""

__all__ = [
    "setup_dialog",
    "manager",
    "DownloadTask",
    "Status",
]

from .client_dialog import setup_dialog
from .task_manager import DownloadTask, Status, manager
