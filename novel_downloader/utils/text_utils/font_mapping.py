#!/usr/bin/env python3
"""
novel_downloader.utils.text_utils.font_mapping
----------------------------------------------

Utility for decoding obfuscated text by applying character-level font mapping.

This is commonly used to reverse font-based obfuscation in scraped content,
where characters are visually disguised via custom font glyphs but can be
recovered using a known mapping.
"""


def apply_font_mapping(text: str, font_map: dict[str, str]) -> str:
    """
    Replace each character in `text` using `font_map`,
    leaving unmapped characters unchanged.

    :param text:    The input string, possibly containing obfuscated font chars.
    :param font_map: A dict mapping obfuscated chars to real chars.
    :return:        The de-obfuscated text.
    """
    return "".join(font_map.get(ch, ch) for ch in text)


__all__ = [
    "apply_font_mapping",
]
