#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.savers.epub_utils.css_builder

Reads local CSS files and wraps them into epub.EpubItem objects,
returning a list ready to be added to the EPUB.
"""

import logging
from importlib.abc import Traversable
from typing import Dict, List, Union

from ebooklib import epub

from novel_downloader.utils.constants import (
    CSS_MAIN_PATH,
    CSS_VOLUME_INTRO_PATH,
)

logger = logging.getLogger(__name__)


def create_css_items(
    include_main: bool = True,
    include_volume: bool = True,
) -> List[epub.EpubItem]:
    """
    :param include_main:   Whether to load the main stylesheet.
    :param include_volume: Whether to load the “volume intro” stylesheet.
    :returns: A list of epub.EpubItem ready to add to the book.
    """
    css_config: List[Dict[str, Union[str, bool, Traversable]]] = [
        {
            "include": include_main,
            "path": CSS_MAIN_PATH,
            "uid": "style",
            "file_name": "Styles/main.css",
        },
        {
            "include": include_volume,
            "path": CSS_VOLUME_INTRO_PATH,
            "uid": "volume_style",
            "file_name": "Styles/volume-intro.css",
        },
    ]
    css_items: List[epub.EpubItem] = []

    for css in css_config:
        if css["include"]:
            path = css["path"]
            assert isinstance(path, Traversable)
            try:
                content: str = path.read_text(encoding="utf-8")
                css_items.append(
                    epub.EpubItem(
                        uid=css["uid"],
                        file_name=css["file_name"],
                        media_type="text/css",
                        content=content,
                    )
                )
            except FileNotFoundError:
                logger.info(f"[epub] CSS 文件不存在: {css['path']}")
            except UnicodeDecodeError:
                logger.info(f"[epub] 无法解码文件: {css['path']}")

    return css_items
