#!/usr/bin/env python3
"""
novel_downloader.libs.image_utils
---------------------------------
"""

import io
from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from PIL import Image


def load_image_array_bytes(data: bytes, white_bg: bool = False) -> NDArray[np.uint8]:
    """
    Decode image bytes into an RGB NumPy array (with white background).

    Reads common image formats (e.g. PNG/JPEG/WebP) from an
    in-memory byte buffer using Pillow, converts the image to RGB,
    and returns a NumPy array suitable for OCR inference.

    :param data: Image file content as raw bytes.
    :param white_bg: If True, flatten images with transparency onto white.
    :return: NumPy array of shape (H, W, 3), dtype=uint8, in RGB order.
    :raises PIL.UnidentifiedImageError, OSError: If input bytes cannot be decoded.
    """
    with Image.open(io.BytesIO(data)) as img:
        return _pil_to_rgb_array(img, white_bg)


def load_image_array_path(path: Path, white_bg: bool = False) -> NDArray[np.uint8]:
    """
    Load a image into an RGB NumPy array (with white background).

    :param path: Image file path.
    :param white_bg: If True, flatten images with transparency onto white.
    :return: Numpy array representing the image (H, W, 3)
    """
    with Image.open(path) as img:
        return _pil_to_rgb_array(img, white_bg)


def filter_orange_watermark(img: NDArray[np.uint8]) -> NDArray[np.uint8]:
    """
    Remove orange-like watermark colors by replacing them with white.

    Note: The input array will be modified in-place.

    :param img: Input image as numpy array (H, W, 3)
    :return: Filtered numpy array (H, W, 3)
    """
    pil_img = Image.fromarray(img).convert("HSV")
    hsv_arr = np.array(pil_img)

    lower_h, upper_h = int(10 / 360 * 255), int(40 / 360 * 255)

    mask_orange = (
        (hsv_arr[:, :, 0] >= lower_h)
        & (hsv_arr[:, :, 0] <= upper_h)
        & (hsv_arr[:, :, 1] > 50)
        & (hsv_arr[:, :, 2] > 100)
    )

    img[mask_orange] = [255, 255, 255]
    return img


def filter_gray_watermark(
    img: NDArray[np.uint8],
    threshold: int = 200,
    background: tuple[int, int, int] = (255, 255, 255),
) -> NDArray[np.uint8]:
    """
    Remove gray-like watermark colors by replacing them with background color.

    Note: The input array will be modified in-place.

    :param img: Input image as numpy array (H, W, 3)
    :return: Filtered numpy array (H, W, 3)
    """
    img16 = img.astype(np.uint16, copy=False)
    sum_rgb = img16[..., 0] + img16[..., 1]
    sum_rgb += img16[..., 2]
    mask = sum_rgb > threshold * 3
    img[mask] = background
    return img


def split_by_height(
    img: NDArray[np.uint8],
    height: int = 38,
    top_offset: int = 10,
    bottom_offset: int = 10,
    per_chunk_top_ignore: int = 10,
) -> list[NDArray[np.uint8]]:
    """
    Split an image vertically into chunks of fixed height,
    with optional global offsets and per-chunk top ignore.

    :param img: Numpy array representing the image (H, W, 3)
    :param height: Height of each chunk
    :param top_offset: Number of pixels to skip from the top (whole image)
    :param bottom_offset: Number of pixels to skip from the bottom (whole image)
    :param per_chunk_top_ignore: Number of pixels to skip from the top of each chunk
    :return: List of numpy arrays, each a sub-image of the original
    """
    h, w, _ = img.shape
    chunks = []
    effective_height = h - top_offset - bottom_offset

    for y in range(0, effective_height, height):
        chunk = img[top_offset + y : top_offset + y + height, :, :]
        if per_chunk_top_ignore > 0 and chunk.shape[0] > per_chunk_top_ignore:
            chunk = chunk[per_chunk_top_ignore:, :, :]
        chunks.append(chunk)

    return chunks


def split_by_white_lines(
    img_arr: NDArray[np.uint8], padding: int = 4
) -> list[NDArray[np.uint8]]:
    """
    Split an RGB image (numpy array) into multiple blocks using full-white
    horizontal separator lines, then add fixed white padding to the top and
    bottom of each block.

    :param img_arr: Input RGB image array with shape (H, W, 3).
    :param padding: Number of white pixels to pad on the top and bottom.
    :return: List of sliced blocks as numpy arrays.
    """
    h, w, _ = img_arr.shape

    # vectorized detection: row is white if min(pixel) == 255
    pix_and = np.bitwise_and.reduce(img_arr, axis=2)
    white_mask = pix_and.min(axis=1) == 255

    # Invert: 1 for content (non-white)
    content_mask = ~white_mask

    if not content_mask.any():
        return []  # whole image is white

    # Locate ranges of consecutive content rows
    # Example: 0 1 1 0 0 1 1 1 0
    # start_indices = [0, 5]
    # end_indices   = [2, 8]
    diff = np.diff(content_mask.astype(np.int8))
    starts = np.flatnonzero(diff == 1) + 1
    ends = np.flatnonzero(diff == -1) + 1

    # If the sequence starts with content
    if content_mask[0]:
        starts = np.r_[0, starts]
    # If the sequence ends with content
    if content_mask[-1]:
        ends = np.r_[ends, h]

    # Prepare padding rows
    pad_block = np.full((padding, w, 3), 255, dtype=np.uint8)

    blocks = []
    for start, end in zip(starts, ends, strict=False):
        block = img_arr[start:end]
        padded = np.concatenate((pad_block, block, pad_block), axis=0)
        blocks.append(padded)

    return blocks


def crop_chars_region(
    img: NDArray[np.uint8],
    num_chars: int,
    left_margin: int = 14,
    char_width: int = 28,
) -> NDArray[np.uint8]:
    """
    Crop the image to keep only the region that covers the specified
    number of characters starting after the left margin.

    :param img: Input image as (H, W, 3) numpy array
    :param num_chars: How many characters to keep
    :param left_margin: Number of columns to skip from the left
    :param char_width: Width of one character (in pixels)
    :return: Cropped image as (H, W', 3)
    """
    h, w, _ = img.shape
    end_col = min(left_margin + char_width * num_chars, w)
    return img[:, :end_col, :]


def is_empty_image(img: NDArray[np.uint8]) -> bool:
    """
    Check if the image is completely white (255, 255, 255).

    :param img: Input image as (H, W, 3) numpy array
    :return: True if all pixels are white, False otherwise
    """
    return bool(np.all(img == 255))


def is_new_paragraph(
    img: np.ndarray,
    white_threshold: int = 250,
    paragraph_threshold: int = 30,
) -> bool:
    """
    Determine whether a line image represents the start of a new paragraph,
    based on the amount of leading full-white columns.

    :param img: Input line image as (H, W, 3) numpy array.
    :param white_threshold: Minimum pixel value considered as white (0-255).
    :param paragraph_threshold: Left margin (in px) to classify as new paragraph.
    :return: True if this line starts a new paragraph.
    """
    h, w, _ = img.shape
    max_scan = min(w, paragraph_threshold)
    # Integer RGB sum: avoids float mean
    rgb_sum = img[:, :max_scan, :].sum(axis=2, dtype=np.uint16)
    return bool((rgb_sum >= 3 * white_threshold).all())


def encode_image_array(
    img: NDArray[np.uint8],
    format: str = "JPEG",
) -> bytes:
    """
    Encode a single RGB image array into the specified format and return
    the raw image bytes.

    :param img: Image as a numpy array (H, W, 3), dtype=uint8, RGB.
    :param format: Output format ("JPEG" or "PNG").
    :return: Encoded image bytes.
    """
    pil_img = Image.fromarray(img)

    buf = io.BytesIO()
    if format == "JPEG":
        pil_img.save(buf, format=format, quality=95, subsampling=0)
    else:
        pil_img.save(buf, format=format)
    return buf.getvalue()


def concat_image_slices_vertical(
    slices: list[NDArray[np.uint8]],
    format: str = "JPEG",
) -> bytes:
    """
    Vertically concatenate a list of RGB image slices and return the encoded
    image bytes in the specified format.

    :param slices: List of image numpy arrays (H, W, 3).
    :param format: Output image format ("JPEG" or "PNG").
    :return: Encoded image bytes.
    :raises ValueError: If slices is empty.
    """
    if not slices:
        raise ValueError("No slices provided.")
    combined = np.concatenate(slices, axis=0)
    img = Image.fromarray(combined, mode="RGB")
    buf = io.BytesIO()
    format = format.upper()
    if format == "JPEG":
        img.save(buf, format="JPEG", quality=95, subsampling=0)
    else:
        img.save(buf, format=format)
    return buf.getvalue()


def _pil_to_rgb_array(img: Image.Image, white_bg: bool) -> NDArray[np.uint8]:
    """Convert PIL image to RGB numpy array, optionally flattening alpha."""
    if img.mode == "P":
        img = img.convert("RGBA")

    if white_bg and ("A" in img.getbands()):
        img = img.convert("RGBA")
        bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
        bg.paste(img, mask=img.getchannel("A"))
        img = bg.convert("RGB")
    else:
        img = img.convert("RGB")

    return np.array(img, copy=True)
