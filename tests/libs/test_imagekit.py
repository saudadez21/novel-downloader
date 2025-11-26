import io

import numpy as np
import pytest
from PIL import Image

from novel_downloader.libs.image_utils import (
    concat_image_slices_vertical,
    crop_chars_region,
    encode_image_array,
    filter_gray_watermark,
    filter_orange_watermark,
    is_empty_image,
    is_new_paragraph,
    load_image_array_bytes,
    load_image_array_path,
    split_by_height,
    split_by_white_lines,
)


def create_rgb_image(width=50, height=40, color=(255, 0, 0)):
    """Create a simple RGB PIL image."""
    return Image.new("RGB", (width, height), color)


def create_rgba_orange_pixel_image():
    """Orange-ish RGBA image with watermark-like HSV."""
    img = Image.new("RGBA", (20, 10), (255, 140, 0, 255))
    return img


def pil_to_bytes(img: Image.Image, fmt="PNG") -> bytes:
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


def create_test_image(width=10, height=10, color=(255, 0, 0)):
    """Create a simple RGB numpy test image."""
    img = np.zeros((height, width, 3), dtype=np.uint8)
    img[:, :] = color
    return img


def test_load_image_array_bytes():
    img = create_rgb_image()
    data = pil_to_bytes(img)
    arr = load_image_array_bytes(data)

    assert isinstance(arr, np.ndarray)
    assert arr.shape == (40, 50, 3)
    assert arr.dtype == np.uint8


def test_load_image_array_path(tmp_path):
    img = create_rgb_image()
    file = tmp_path / "img.png"
    img.save(file)

    arr = load_image_array_path(file)
    assert arr.shape == (40, 50, 3)


def test_load_image_array_bytes_white_bg():
    img = create_rgba_orange_pixel_image()
    data = pil_to_bytes(img)
    arr = load_image_array_bytes(data, white_bg=True)

    # Since background is white and image is opaque orange
    assert arr.shape == (10, 20, 3)
    assert arr[0, 0].tolist() == [255, 140, 0]


def test_filter_orange_watermark():
    img = np.full((10, 10, 3), [255, 140, 0], dtype=np.uint8)
    filtered = filter_orange_watermark(img.copy())

    assert np.all(filtered == 255)  # all replaced by white


def test_filter_gray_watermark():
    # Very bright gray → should be replaced
    img = np.full((5, 5, 3), 230, dtype=np.uint8)
    filtered = filter_gray_watermark(img.copy(), threshold=200)
    assert np.all(filtered == 255)


def test_split_by_height_basic():
    img = np.zeros((100, 20, 3), dtype=np.uint8)
    chunks = split_by_height(img, height=30)

    # ranges: 0-30, 30-60, 60-90
    assert len(chunks) == 3
    assert chunks[0].shape[0] <= 30


def test_split_by_height_no_offset():
    img = np.zeros((100, 20, 3), dtype=np.uint8)

    chunks = split_by_height(
        img, height=30, top_offset=0, bottom_offset=0, per_chunk_top_ignore=0
    )

    # 0-30, 30-60, 60-90, 90-120 (last is 10px)
    assert len(chunks) == 4


def test_split_by_white_lines():
    # Build image: block - white - block
    block = np.zeros((5, 20, 3), dtype=np.uint8)
    white = np.full((1, 20, 3), 255, dtype=np.uint8)
    img = np.vstack([block, white, block])

    blocks = split_by_white_lines(img, padding=2)
    assert len(blocks) == 2

    for blk in blocks:
        # padded = top(2) + middle block(5) + bottom(2) = 9
        assert blk.shape[0] == 9


def test_crop_chars_region():
    img = np.zeros((10, 100, 3), dtype=np.uint8)
    cropped = crop_chars_region(img, num_chars=2, left_margin=10, char_width=20)
    # columns kept = 10 + 2*20 = 50
    assert cropped.shape[1] == 50


def test_is_empty_image():
    img_white = np.full((10, 10, 3), 255, dtype=np.uint8)
    img_black = np.zeros((10, 10, 3), dtype=np.uint8)
    assert is_empty_image(img_white) is True
    assert is_empty_image(img_black) is False


def test_is_new_paragraph_true():
    # Left area all white
    img = np.full((10, 50, 3), 255, dtype=np.uint8)
    assert is_new_paragraph(img, paragraph_threshold=20)


def test_is_new_paragraph_false():
    img = np.full((10, 50, 3), 255, dtype=np.uint8)
    img[:, 0:5] = 0  # black indent area
    assert is_new_paragraph(img, paragraph_threshold=20) is False


@pytest.mark.parametrize("format", ["JPEG", "PNG"])
def test_encode_image_array_basic(format):
    img = create_test_image()

    encoded = encode_image_array(img, format=format)

    # Should return bytes
    assert isinstance(encoded, bytes)
    assert len(encoded) > 0

    # Should be loadable by PIL
    loaded = Image.open(io.BytesIO(encoded))
    assert loaded.size == (10, 10)
    assert loaded.mode == "RGB"


def test_encode_image_array_actual_color():
    color = (123, 50, 200)
    img = create_test_image(color=color)

    encoded = encode_image_array(img, format="PNG")  # PNG is lossless
    loaded = np.array(Image.open(io.BytesIO(encoded)))

    assert loaded.shape == img.shape
    np.testing.assert_array_equal(loaded, img)


@pytest.mark.parametrize("format", ["JPEG", "PNG"])
def test_concat_image_slices_vertical_basic(format):
    slice1 = create_test_image(height=5, color=(255, 0, 0))
    slice2 = create_test_image(height=7, color=(0, 255, 0))

    encoded = concat_image_slices_vertical([slice1, slice2], format=format)
    loaded = np.array(Image.open(io.BytesIO(encoded)))

    assert loaded.shape == (12, 10, 3)

    expected_top = np.array([255, 0, 0])
    expected_bottom = np.array([0, 255, 0])

    top = loaded[:5]
    bottom = loaded[5:]

    if format == "PNG":
        # PNG is lossless
        assert np.all(top == expected_top)
        assert np.all(bottom == expected_bottom)
    else:
        # JPEG: allow lossy compression, check mean error
        top_mean_error = np.mean(np.abs(top - expected_top))
        bottom_mean_error = np.mean(np.abs(bottom - expected_bottom))

        assert top_mean_error <= 15
        assert bottom_mean_error <= 15


def test_concat_image_slices_vertical_empty():
    """Should raise error when empty list is provided."""
    with pytest.raises(ValueError, match="No slices provided"):
        concat_image_slices_vertical([])


def test_concat_image_slices_vertical_one_slice():
    """Concatenating one slice should return the same image."""
    img = create_test_image(height=8)
    encoded = concat_image_slices_vertical([img], format="PNG")
    loaded = np.array(Image.open(io.BytesIO(encoded)))

    np.testing.assert_array_equal(loaded, img)
