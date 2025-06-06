#!/usr/bin/env python3
"""
novel_downloader.models.browser
-------------------------------

"""

from pathlib import Path
from typing import TypedDict

from playwright.async_api import ViewportSize


class NewContextOptions(TypedDict, total=False):
    user_agent: str
    locale: str
    storage_state: Path
    viewport: ViewportSize
    java_script_enabled: bool
    ignore_https_errors: bool
    extra_http_headers: dict[str, str]
