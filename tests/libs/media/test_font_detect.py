from pathlib import Path

import pytest
from novel_downloader.libs.media.font import detect_font_format

FONT_TYPES = {
    "ttf",
    "otf",
    "woff",
    "woff2",
    "pfb",
    "ttc",
    "ps",
    "dfont",
    "cff",
    "bin",
}

EXPECTED_MAP = {
    "ttf": "ttf",
    "otf": "otf",
    "woff": "woff",
    "woff2": "woff2",
    "pfb": "pfb",
    "ttc": "ttc",
    "ps": None,
    "dfont": None,
    "cff": None,
    "bin": None,
}


@pytest.mark.parametrize("ext", sorted(FONT_TYPES))
def test_detect_font_format(ext):
    """
    Ensure detect_font_format() correctly detects font formats.
    """
    base = Path(__file__).parents[2] / "data" / "libs" / "media" / "font"
    files = list(base.glob(f"*.{ext}"))
    assert files, f"No test font found for extension {ext}"

    expected = EXPECTED_MAP[ext]

    for font_file in files:
        data = font_file.read_bytes()
        fmt = detect_font_format(data)
        assert fmt == expected, f"{font_file.name}: expected {expected}, got {fmt}"


def test_detect_font_format_small_input():
    """Small input (<12 bytes) must return None."""
    assert detect_font_format(b"123") is None


def test_detect_font_format_unknown():
    """Unknown magic number must return None."""
    assert detect_font_format(b"ThisIsNotAFontFile...") is None
