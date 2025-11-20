from pathlib import Path

import pytest
from novel_downloader.libs.media.image import detect_image_format

IMG_TYPES = {
    "bmp",
    "gif",
    "ico",
    "jpg",
    "jpeg",
    "svg",
    "png",
    "tiff",
    "webp",
}


@pytest.mark.parametrize("ext", sorted(IMG_TYPES))
def test_detect_image_format(ext):
    """
    Ensure detect_image_format() correctly detects all supported types.
    """
    base = Path(__file__).parents[2] / "data" / "libs" / "media" / "image"
    files = list(base.glob(f"*.{ext}"))

    if not files:
        pytest.skip(f"No test images found for extension '{ext}'")

    for img_file in files:
        data = img_file.read_bytes()
        fmt = detect_image_format(data)

        # normalize: jpg should map to jpeg
        expected = "jpeg" if ext in {"jpg", "jpeg"} else ext

        assert fmt == expected, f"{img_file.name}: expected {expected}, got {fmt}"


def test_detect_image_format_small_input():
    """Small input (<12 bytes) must return None."""
    assert detect_image_format(b"123") is None


def test_detect_image_format_unknown():
    """Unknown magic number should return None."""
    assert detect_image_format(b"ThisIsNotAnImage....") is None
