#!/usr/bin/env python3
"""
novel_downloader.plugins.utils.ciweimao.image
---------------------------------------------
"""

__all__ = ["split_image"]

from dataclasses import dataclass
from typing import Any, Literal, TypedDict

import numpy as np
from numpy.typing import NDArray

BACKGROUND_COLOR = np.array([248, 239, 218], dtype=np.uint8)


class ImageBlock(TypedDict):
    type: Literal["image"]
    url: str


class ParagraphBlock(TypedDict):
    type: Literal["paragraph"]
    image_idxs: list[int]


@dataclass(slots=True)
class SplitResult:
    images: list[NDArray[np.uint8]]
    blocks: list[ImageBlock | ParagraphBlock]


def split_image(
    img_arr: NDArray[np.uint8],
    image_tsukkomi_list: dict[str, Any],
) -> SplitResult:
    """
    Split a Ciweimao chapter image into OCR-ready text slices and inline image blocks.

    The function uses Tsukkomi metadata (`tsukkomi_list` and `imageInfoMaps`) to
    determine where text lines and image lines are located. Text segments are cropped,
    padded, and added to the `images` list. The reading order is stored in `blocks`
    as either image blocks or paragraph blocks.

    :param img_arr: Input RGB image array of shape (H, W, 3).
    :param image_tsukkomi_list: Tsukkomi metadata.
    :return: SplitResult containing cropped OCR image slices and logical block order.
    """
    tsukkomi_list = image_tsukkomi_list["tsukkomi_list"]
    imageInfoMaps = image_tsukkomi_list["imageInfoMaps"]
    font_height = image_tsukkomi_list["height"]

    images: list[NDArray[np.uint8]] = []
    blocks: list[ImageBlock | ParagraphBlock] = []

    # Precompute multipliers
    fh_1_2 = 1.2 * font_height
    fh_1_5 = int(font_height * 1.5)
    fh_2_2 = 2.2 * font_height
    pad_h = max(1, font_height >> 1)

    h, w, _ = img_arr.shape
    pad_block = np.full((pad_h, w, 3), BACKGROUND_COLOR, dtype=np.uint8)

    now_y = 0.0

    for para_key in sorted(tsukkomi_list.keys(), key=lambda x: int(x)):
        start_line, end_line = tsukkomi_list[para_key]
        para_image_idxs: list[int] = []

        # Process all lines inside the paragraph
        for line in range(start_line, end_line + 1):
            line_str = str(line)

            # -------------------------------
            # IMAGE line
            # -------------------------------
            if line_str in imageInfoMaps:
                info = imageInfoMaps[line_str]
                url = info["path"]

                blocks.append({"type": "image", "url": url})
                now_y += info["height"] + fh_1_2
                continue

            # -------------------------------
            # TEXT line (OCR slice)
            # -------------------------------
            next_y = now_y + fh_2_2
            start_y = int(now_y)
            end_y = start_y + fh_1_5

            # clamp
            start_y = max(0, min(start_y, h))
            end_y = max(0, min(end_y, h))
            if start_y == end_y:
                break

            # slice text block
            block = img_arr[start_y:end_y, :, :]
            block = filter_gray_watermark(block)
            block = np.concatenate((pad_block, block, pad_block), axis=0)

            image_idx = len(images)
            images.append(block)
            para_image_idxs.append(image_idx)

            now_y = next_y

        if para_image_idxs:
            blocks.append(
                {
                    "type": "paragraph",
                    "image_idxs": para_image_idxs,
                }
            )

    return SplitResult(images=images, blocks=blocks)


def filter_gray_watermark(
    img: NDArray[np.uint8], threshold: int = 200
) -> NDArray[np.uint8]:
    """
    Remove gray-like watermark colors by replacing them with white.

    Note: The input array will be modified in-place.

    :param img: Input image as numpy array (H, W, 3)
    :return: Filtered numpy array (H, W, 3)
    """
    img16 = img.astype(np.uint16, copy=False)
    sum_rgb = img16[..., 0] + img16[..., 1]
    sum_rgb += img16[..., 2]

    mask = sum_rgb > threshold * 3
    img[mask] = BACKGROUND_COLOR
    return img
