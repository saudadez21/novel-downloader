#!/usr/bin/env python3
"""
novel_downloader.utils.fontocr.core
-----------------------------------

This class provides utility methods for optical character recognition (OCR),
primarily used for decrypting custom font encryption.
"""

import io
from pathlib import Path
from typing import Any

import numpy as np
from fontTools.ttLib import TTFont
from paddleocr import TextRecognition
from PIL import Image, ImageDraw, ImageFont
from PIL.Image import Transpose


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
        enable_hpi: bool = False,
        **kwargs: Any,
    ) -> None:
        """
        Initialize a FontOCR instance.

        :param model_name: If set to None, PP-OCRv5_server_rec is used.
        :param model_dir: Model storage path.
        :param input_shape: Input image size for the model in the format (C, H, W).
        :param device: Device for inference.
        :param precision: Precision for TensorRT.
        :param cpu_threads: Number of threads to use for inference on CPUs.
        :param kwargs: reserved for future extensions
        """
        self._ocr_model = TextRecognition(  # takes 5 ~ 12 sec to init
            model_name=model_name,
            model_dir=model_dir,
            input_shape=input_shape,
            device=device,
            precision=precision,
            cpu_threads=cpu_threads,
            enable_hpi=enable_hpi,
        )

    def predict(
        self,
        images: list[np.ndarray],
        batch_size: int = 1,
    ) -> list[tuple[str, float]]:
        """
        Run OCR on input images.

        :param images: list of np.ndarray objects to predict
        :param batch_size: batch size for OCR inference (minimum 1)
        :return: list of tuple containing (character, score)
        """
        return [
            (pred.get("rec_text"), pred.get("rec_score"))
            for pred in self._ocr_model.predict(images, batch_size=batch_size)
        ]

    @staticmethod
    def render_char_image(
        char: str,
        render_font: ImageFont.FreeTypeFont,
        is_reflect: bool = False,
        size: int = 64,
    ) -> Image.Image:
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

        return img

    @staticmethod
    def render_char_image_array(
        char: str,
        render_font: ImageFont.FreeTypeFont,
        is_reflect: bool = False,
        size: int = 64,
    ) -> np.ndarray:
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

        return np.array(img)

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
    def load_image_array_bytes(data: bytes) -> np.ndarray:
        """
        Decode image bytes into an RGB NumPy array.

        Reads common image formats (e.g. PNG/JPEG/WebP) from an
        in-memory byte buffer using Pillow, converts the image to RGB,
        and returns a NumPy array suitable for OCR inference.

        :param data: Image file content as raw bytes.
        :return: NumPy array of shape (H, W, 3), dtype=uint8, in RGB order.
        :raises PIL.UnidentifiedImageError, OSError: If input bytes cannot be decoded.
        """
        with Image.open(io.BytesIO(data)) as im:
            im = im.convert("RGB")
            return np.asarray(im)

    @staticmethod
    def load_render_font(
        font_path: Path | str, char_size: int = 52
    ) -> ImageFont.FreeTypeFont:
        """
        Load a FreeType font face at the given pixel size for rendering helpers.

        :param font_path: Path to a TTF/OTF font file.
        :param char_size: Target glyph size in pixels (e.g. 52).
        :return: A PIL `ImageFont.FreeTypeFont` instance.
        :raises OSError: If the font file cannot be opened by PIL.
        """
        return ImageFont.truetype(str(font_path), char_size)

    @staticmethod
    def load_render_font_bytes(
        font_bytes: bytes, char_size: int = 52
    ) -> ImageFont.FreeTypeFont:
        """
        Load a FreeType font face directly from bytes for rendering helpers.

        :param font_bytes: Raw TTF/OTF font data as bytes.
        :param char_size: Target glyph size in pixels (e.g. 52).
        :return: A PIL `ImageFont.FreeTypeFont` instance.
        """
        return ImageFont.truetype(io.BytesIO(font_bytes), char_size)

    @staticmethod
    def extract_font_charset(font_path: Path | str) -> set[str]:
        """
        Extract the set of Unicode characters encoded by a TrueType/OpenType font.

        This reads the font's best available character map (cmap) and returns the
        corresponding set of characters.

        :param font_path: Path to a TTF/OTF font file.
        :return: A set of Unicode characters present in the font's cmap.
        """
        with TTFont(font_path) as font_ttf:
            cmap = font_ttf.getBestCmap() or {}

        charset: set[str] = set()
        for cp in cmap:
            # guard against invalid/surrogate code points
            if 0 <= cp <= 0x10FFFF and not (0xD800 <= cp <= 0xDFFF):
                try:
                    charset.add(chr(cp))
                except ValueError:
                    continue
        return charset

    @staticmethod
    def extract_font_charset_bytes(font_bytes: bytes) -> set[str]:
        """
        Extract the set of Unicode characters encoded by a TrueType/OpenType font
        provided as bytes.

        :param font_bytes: Raw TTF/OTF/WOFF2 font data as bytes.
        :return: A set of Unicode characters present in the font's cmap.
        """
        with TTFont(io.BytesIO(font_bytes)) as font_ttf:
            cmap = font_ttf.getBestCmap() or {}

        charset: set[str] = set()
        for cp in cmap:
            if 0 <= cp <= 0x10FFFF and not (0xD800 <= cp <= 0xDFFF):
                try:
                    charset.add(chr(cp))
                except ValueError:
                    continue
        return charset
