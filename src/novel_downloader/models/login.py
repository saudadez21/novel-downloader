#!/usr/bin/env python3
"""
novel_downloader.models.login
-----------------------------

"""

from dataclasses import dataclass
from typing import Literal


@dataclass
class LoginField:
    name: str
    label: str
    type: Literal["text", "password", "cookie", "manual_login"]
    required: bool
    default: str = ""
    placeholder: str = ""
    description: str = ""
