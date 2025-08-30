#!/usr/bin/env python3
"""
novel_downloader.utils.fontocr
------------------------------

This class provides utility methods for optical character recognition (OCR),
primarily used for decrypting custom font encryption.
"""

__all__ = [
    "FontOCR",
    "get_font_ocr",
]
__version__ = "4.0"

import logging
from collections.abc import Generator
from typing import Any, TypeVar

import numpy as np
from paddleocr import TextRecognition  # takes 5 ~ 12 sec to init
from PIL import Image, ImageDraw, ImageFont
from PIL.Image import Transpose

T = TypeVar("T")
logger = logging.getLogger(__name__)


class FontOCR:
    """
    Version 4 of the FontOCR utility.
    """

    def __init__(
        self,
        model_name: str | None = None,
        model_dir: str | None = None,
        input_shape: tuple[int, int, int] | None = None,
        device: str | None = None,
        precision: str = "fp32",
        cpu_threads: int = 10,
        batch_size: int = 32,
        threshold: float = 0.0,
        **kwargs: Any,
    ) -> None:
        """
        Initialize a FontOCR instance.

        :param batch_size: batch size for OCR inference (minimum 1)
        :param ocr_weight: weight factor for OCR-based prediction scores
        :param vec_weight: weight factor for vector-based similarity scores
        :param threshold: minimum confidence threshold for predictions [0.0-1.0]
        :param kwargs: reserved for future extensions
        """
        self._batch_size = batch_size
        self._threshold = threshold
        self._ocr_model = TextRecognition(
            model_name=model_name,
            model_dir=model_dir,
            input_shape=input_shape,
            device=device,
            precision=precision,
            cpu_threads=cpu_threads,
        )

    def predict(
        self,
        images: list[np.ndarray],
        top_k: int = 1,
    ) -> list[list[tuple[str, float]]]:
        """
        Run OCR on input images.

        :param images: list of np.ndarray objects to predict
        :param top_k: number of top candidates to return per image
        :return: list of lists containing (character, score)
        """
        return [
            [(pred.get("rec_text"), pred.get("rec_score"))]
            for pred in self._ocr_model.predict(images, batch_size=self._batch_size)
        ]

    @staticmethod
    def render_char_image(
        char: str,
        render_font: ImageFont.FreeTypeFont,
        is_reflect: bool = False,
        size: int = 64,
    ) -> Image.Image | None:
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

        img_np = np.array(img)
        if np.unique(img_np).size == 1:
            return None

        return img

    @staticmethod
    def render_char_image_array(
        char: str,
        render_font: ImageFont.FreeTypeFont,
        is_reflect: bool = False,
        size: int = 64,
    ) -> np.ndarray | None:
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

        img_np = np.array(img)
        if np.unique(img_np).size == 1:
            return None

        return img_np

    @staticmethod
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

    @staticmethod
    def _chunked(seq: list[T], size: int) -> Generator[list[T], None, None]:
        """
        Yield successive chunks of `seq` of length `size`.
        """
        for i in range(0, len(seq), size):
            yield seq[i : i + size]


_font_ocr: FontOCR | None = None


def get_font_ocr(
    model_name: str | None = None,
    model_dir: str | None = None,
    input_shape: tuple[int, int, int] | None = None,
    batch_size: int = 32,
) -> FontOCR:
    """
    Return the singleton FontOCR, initializing it on first use.
    """
    global _font_ocr
    if _font_ocr is None:
        _font_ocr = FontOCR(
            model_name=model_name,
            model_dir=model_dir,
            input_shape=input_shape,
            batch_size=batch_size,
        )
    return _font_ocr
