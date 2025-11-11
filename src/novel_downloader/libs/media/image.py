#!/usr/bin/env python3
"""
novel_downloader.libs.media.image
---------------------------------
"""


def detect_image_format(data: bytes) -> str | None:
    """
    Detect the true image format based on magic numbers.

    :param data: Raw image bytes (at least the first 12 bytes).
    :return: Lowercase format name such as 'jpeg' or None if unknown.
    """
    if len(data) < 12:
        return None

    header = data[:64]

    # --- common formats ---
    if header.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if header.startswith((b"GIF87a", b"GIF89a")):
        return "gif"
    if header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        return "webp"
    if header.startswith(b"BM"):
        return "bmp"
    if header[:4] in (b"II*\x00", b"MM\x00*"):
        return "tiff"
    if header[:4] == b"\x00\x00\x01\x00":
        return "ico"
    if header[:4] == b"\x00\x00\x02\x00":
        return "cur"

    # --- svg / xml-based ---
    lower_head = header.lower()
    if lower_head.startswith(b"<?xml") or b"<svg" in lower_head:
        return "svg"

    # --- uncommon formats ---
    # if header.startswith(b"\x76\x2f\x31\x01"):
    #     return "exr"  # OpenEXR
    # if header.startswith(b"\x59\xA6\x6A\x95"):
    #     return "rast"  # Sun raster
    # if header.startswith(b"#define "):
    #     return "xbm"  # X bitmap (ASCII text image)

    # if header.startswith(b"8BPS"):
    #     return "psd"
    # if header.startswith(b"\x00\x00\x00\x0CjP  "):
    #     return "jp2"
    # if b"ftypheic" in header[:12] or b"ftypheix" in header[:12]:
    #     return "heic"
    # if b"ftypavif" in header[:12]:
    #     return "avif"

    # # PBM/PGM/PPM (Netpbm formats)
    # if len(header) >= 3 and header[0] == ord(b"P"):
    #     if header[1] in b"14" and header[2] in b" \t\n\r":
    #         return "pbm"
    #     if header[1] in b"25" and header[2] in b" \t\n\r":
    #         return "pgm"
    #     if header[1] in b"36" and header[2] in b" \t\n\r":
    #         return "ppm"

    # # SGI RGB image
    # if header.startswith(b"\x01\xDA"):
    #     return "rgb"

    return None
