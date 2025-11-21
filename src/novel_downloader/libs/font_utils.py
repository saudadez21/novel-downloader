#!/usr/bin/env python3
"""
novel_downloader.libs.font_utils
--------------------------------
"""

import io
from pathlib import Path

import numpy as np
from fontTools.ttLib import TTFont
from numpy.typing import NDArray
from PIL import Image, ImageDraw, ImageFont
from PIL.Image import Transpose


def render_char_image(
    char: str,
    render_font: ImageFont.FreeTypeFont,
    is_reflect: bool = False,
    size: int = 64,
) -> Image.Image:
    """
    Render a single character into an RGB square image.

    :param char: character to render
    :param render_font: FreeTypeFont instance to render with
    :param is_reflect: if True, flip the image horizontally
    :param size: output image size (width and height in pixels)
    :return: rendered PIL.Image in RGB or None if blank
    """
    # img = Image.new("L", (size, size), color=255)
    img = Image.new("RGB", (size, size), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    bbox = draw.textbbox((0, 0), char, font=render_font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (size - w) // 2 - bbox[0]
    y = (size - h) // 2 - bbox[1]
    draw.text((x, y), char, fill=0, font=render_font)
    if is_reflect:
        img = img.transpose(Transpose.FLIP_LEFT_RIGHT)

    return img


def render_char_image_array(
    char: str,
    render_font: ImageFont.FreeTypeFont,
    is_reflect: bool = False,
    size: int = 64,
) -> NDArray[np.uint8]:
    """
    Render a single character into an RGB square image.

    :param char: character to render
    :param render_font: FreeTypeFont instance to render with
    :param is_reflect: if True, flip the image horizontally
    :param size: output image size (width and height in pixels)
    :return: rendered image as np.ndarray in RGB or None if blank
    """
    # img = Image.new("L", (size, size), color=255)
    img = Image.new("RGB", (size, size), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    bbox = draw.textbbox((0, 0), char, font=render_font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (size - w) // 2 - bbox[0]
    y = (size - h) // 2 - bbox[1]
    draw.text((x, y), char, fill=0, font=render_font)
    if is_reflect:
        img = img.transpose(Transpose.FLIP_LEFT_RIGHT)

    return np.array(img)


def render_text_image(
    text: str,
    font: ImageFont.FreeTypeFont,
    cell_size: int = 64,
    chars_per_line: int = 16,
) -> Image.Image:
    """
    Render a string into a image.
    """
    # import textwrap
    # lines = textwrap.wrap(text, width=chars_per_line) or [""]
    lines = [
        text[i : i + chars_per_line] for i in range(0, len(text), chars_per_line)
    ] or [""]
    img_w = cell_size * chars_per_line
    img_h = cell_size * len(lines)

    # img = Image.new("L", (img_w, img_h), color=255)
    img = Image.new("RGB", (img_w, img_h), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    for row, line in enumerate(lines):
        for col, ch in enumerate(line):
            x = (col + 0.5) * cell_size
            y = (row + 0.5) * cell_size
            draw.text((x, y), ch, font=font, fill=0, anchor="mm")

    return img


def load_render_font(
    font_path: Path | str, char_size: int = 52
) -> ImageFont.FreeTypeFont:
    """
    Load a FreeType font face at the given pixel size for rendering helpers.

    :param font_path: Path to a TTF/OTF font file.
    :param char_size: Target glyph size in pixels (e.g. 52).
    :return: A PIL `ImageFont.FreeTypeFont` instance.
    :raises OSError: If the font file cannot be opened by PIL.
    """
    return ImageFont.truetype(str(font_path), char_size)


def load_render_font_bytes(
    font_bytes: bytes, char_size: int = 52
) -> ImageFont.FreeTypeFont:
    """
    Load a FreeType font face directly from bytes for rendering helpers.

    :param font_bytes: Raw TTF/OTF font data as bytes.
    :param char_size: Target glyph size in pixels (e.g. 52).
    :return: A PIL `ImageFont.FreeTypeFont` instance.
    """
    return ImageFont.truetype(io.BytesIO(font_bytes), char_size)


def extract_font_charset(font_path: Path | str) -> set[str]:
    """
    Extract the set of Unicode characters encoded by a TrueType/OpenType font.

    This reads the font's best available character map (cmap) and returns the
    corresponding set of characters.

    :param font_path: Path to a TTF/OTF font file.
    :return: A set of Unicode characters present in the font's cmap.
    """
    with TTFont(font_path) as font_ttf:
        cmap = font_ttf.getBestCmap() or {}

    charset: set[str] = set()
    for cp in cmap:
        # guard against invalid/surrogate code points
        if 0 <= cp <= 0x10FFFF and not (0xD800 <= cp <= 0xDFFF):
            try:
                charset.add(chr(cp))
            except ValueError:
                continue
    return charset


def extract_font_charset_bytes(font_bytes: bytes) -> set[str]:
    """
    Extract the set of Unicode characters encoded by a TrueType/OpenType font
    provided as bytes.

    :param font_bytes: Raw TTF/OTF/WOFF2 font data as bytes.
    :return: A set of Unicode characters present in the font's cmap.
    """
    with TTFont(io.BytesIO(font_bytes)) as font_ttf:
        cmap = font_ttf.getBestCmap() or {}

    charset: set[str] = set()
    for cp in cmap:
        if 0 <= cp <= 0x10FFFF and not (0xD800 <= cp <= 0xDFFF):
            try:
                charset.add(chr(cp))
            except ValueError:
                continue
    return charset
