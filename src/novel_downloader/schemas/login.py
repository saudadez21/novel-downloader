#!/usr/bin/env python3
"""
novel_downloader.schemas.login
------------------------------

"""

from dataclasses import dataclass
from typing import Literal


@dataclass
class LoginField:
    name: str
    label: str
    type: Literal["text", "password", "cookie"]
    required: bool
    default: str = ""
    placeholder: str = ""
    description: str = ""
