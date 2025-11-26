#!/usr/bin/env python3
"""
novel_downloader.libs.media.font
--------------------------------
"""


def detect_font_format(data: bytes) -> str | None:
    """
    Detect the font format based on magic numbers (file header).

    :param data: Raw font bytes (at least the first 12 bytes).
    :return: Lowercase format name such as 'ttf', or None if unknown.
    """
    if len(data) < 12:
        return None

    header = data[:12]

    # --- TrueType font (TTF) ---
    if header[:4] == b"\x00\x01\x00\x00" or header[:4] == b"true":
        return "ttf"

    # --- OpenType font (OTF) ---
    if header[:4] == b"OTTO":
        return "otf"

    # --- Web Open Font Format (WOFF) ---
    if header[:4] == b"wOFF":
        return "woff"

    # --- Web Open Font Format 2 (WOFF2) ---
    if header[:4] == b"wOF2":
        return "woff2"

    # --- PostScript Type 1 (ASCII or binary) ---
    if header.startswith((b"%!PS-AdobeFont", b"%!FontType")):
        return "pfa"
    if header[:2] == b"\x80\x01" or header[:2] == b"\x80\x02":
        return "pfb"

    # --- SFNT-based container (Apple dfont) ---
    if header[:4] == b"ttcf":
        return "ttc"

    # --- Embedded OpenType (EOT) ---
    if header[:4] == b"L\0P\0" or header[:4] == b"\x4c\x50\x00\x00":
        return "eot"

    return None
