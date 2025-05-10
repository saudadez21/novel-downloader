#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.savers.epub_utils.volume_intro

Responsible for generating HTML code for volume introduction pages,
including two style variants and a unified entry point.
"""

from typing import Tuple

from novel_downloader.utils.constants import EPUB_IMAGE_FOLDER


def split_volume_title(volume_title: str) -> Tuple[str, str]:
    """
    Split volume title into two parts for better display.

    :param volume_title: Original volume title string.
    :return: Tuple of (line1, line2)
    """
    if " " in volume_title:
        parts = volume_title.split(" ")
    elif "-" in volume_title:
        parts = volume_title.split("-")
    else:
        return "", volume_title

    return parts[0], "".join(parts[1:])


def create_volume_intro(volume_title: str, volume_intro_text: str = "") -> str:
    """
    Generate the HTML snippet for a volume's introduction section.

    :param volume_title: Title of the volume.
    :param volume_intro_text: Optional introduction text for the volume.
    :return: HTML string representing the volume's intro section.
    """
    line1, line2 = split_volume_title(volume_title)

    def make_border_img(class_name: str) -> str:
        return (
            f'<div class="{class_name}">'
            f'<img alt="" class="{class_name}" '
            f'src="../{EPUB_IMAGE_FOLDER}/volume_border.png" />'
            f"</div>"
        )

    html_parts = [make_border_img("border1")]

    if line1:
        html_parts.append(f'<h1 class="volume-title-line1">{line1}</h1>')

    html_parts.append(f'<p class="volume-title-line2">{line2}</p>')
    html_parts.append(make_border_img("border2"))

    if volume_intro_text:
        html_parts.append(f'<p class="intro">{volume_intro_text}</p>')

    return "\n".join(html_parts)
