from pathlib import Path

import numpy as np
import pytest
from PIL import ImageFont

from novel_downloader.libs.font_utils import (
    extract_font_charset,
    extract_font_charset_bytes,
    load_render_font,
    load_render_font_bytes,
    render_char_image,
    render_char_image_array,
    render_text_image,
)

FONT_DIR = Path(__file__).parents[1] / "data" / "libs" / "media" / "font"


def discover_ttf_fonts() -> list[Path]:
    if not FONT_DIR.exists():
        return []
    fonts = [p for p in FONT_DIR.glob("*.ttf") if not p.name.startswith("font_")]
    return sorted(fonts, key=lambda p: p.name)


FONT_FILES = discover_ttf_fonts()

if not FONT_FILES:
    pytest.skip(f"No TTF fonts found in {FONT_DIR}", allow_module_level=True)


@pytest.fixture(params=FONT_FILES, ids=[p.name for p in FONT_FILES])
def font_case(request):
    """
    Returns (font_path_str, FreeTypeFont instance)
    This gives readable pytest output: [OpenSans-Regular.ttf]
    """
    font_path = request.param
    font_obj = ImageFont.truetype(str(font_path), size=32)
    return str(font_path), font_obj


def test_render_char_image(font_case):
    font_path, font = font_case
    img = render_char_image("C", font, size=64)
    arr = np.array(img)
    assert np.any(arr < 255), f"Blank render for font {font_path}"


def test_render_char_image_array(font_case):
    font_path, font = font_case
    arr = render_char_image_array("C", font, size=64)
    assert arr.shape == (64, 64, 3), font_path


def test_render_char_image_reflect(font_case):
    font_path, font = font_case
    img1 = render_char_image("C", font, size=64)
    img2 = render_char_image("C", font, size=64, is_reflect=True)
    assert not np.array_equal(np.array(img1), np.array(img2)), (
        f"Reflection identical for font {font_path}"
    )


def test_render_text_image(font_case):
    font_path, font = font_case
    img = render_text_image("HelloWorld", font, cell_size=32, chars_per_line=5)
    assert img.size == (5 * 32, 2 * 32), font_path


def test_load_render_font(font_case):
    font_path, _ = font_case
    f = load_render_font(font_path, char_size=32)
    assert isinstance(f, ImageFont.FreeTypeFont), font_path


def test_load_render_font_bytes(font_case):
    font_path, _ = font_case
    data = Path(font_path).read_bytes()
    f = load_render_font_bytes(data, char_size=32)
    assert isinstance(f, ImageFont.FreeTypeFont), font_path


def test_extract_font_charset(font_case):
    font_path, _ = font_case
    charset = extract_font_charset(font_path)
    assert len(charset) > 0, f"No characters extracted for font {font_path}"


def test_extract_font_charset_bytes(font_case):
    font_path, _ = font_case
    data = Path(font_path).read_bytes()
    charset = extract_font_charset_bytes(data)
    assert len(charset) > 0, f"No characters extracted from bytes for {font_path}"
