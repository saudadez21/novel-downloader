#!/usr/bin/env python3
"""
novel_downloader.libs.fontocr.core
----------------------------------

This class provides utility methods for optical character recognition (OCR),
primarily used for decrypting custom font encryption.
"""

import io
from pathlib import Path
from typing import Any

import numpy as np
from fontTools.ttLib import TTFont
from numpy.typing import NDArray
from paddleocr import TextRecognition
from PIL import Image, ImageDraw, ImageFont
from PIL.Image import Transpose


class FontOCR:
    """
    Version 4 of the FontOCR utility.
    """

    WHITE = np.array([255, 255, 255])

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
        images: list[NDArray[np.uint8]],
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
    ) -> NDArray[np.uint8]:
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

    @classmethod
    def load_image_array_bytes(
        cls, data: bytes, white_bg: bool = False
    ) -> NDArray[np.uint8]:
        """
        Decode image bytes into an RGB NumPy array.

        Reads common image formats (e.g. PNG/JPEG/WebP) from an
        in-memory byte buffer using Pillow, converts the image to RGB,
        and returns a NumPy array suitable for OCR inference.

        :param data: Image file content as raw bytes.
        :param white_bg: If True, flatten images with transparency onto white.
        :return: NumPy array of shape (H, W, 3), dtype=uint8, in RGB order.
        :raises PIL.UnidentifiedImageError, OSError: If input bytes cannot be decoded.
        """
        with Image.open(io.BytesIO(data)) as img:
            return cls._pil_to_rgb_array(img, white_bg)

    @classmethod
    def load_image_array_path(
        cls, path: Path, white_bg: bool = False
    ) -> NDArray[np.uint8]:
        """
        Convert a GIF image into a numpy array with white background.

        :param path: Image file path.
        :param white_bg: If True, flatten images with transparency onto white.
        :return: Numpy array representing the image (H, W, 3)
        """
        with Image.open(path) as img:
            return cls._pil_to_rgb_array(img, white_bg)

    @staticmethod
    def filter_orange_watermark(img: NDArray[np.uint8]) -> NDArray[np.uint8]:
        """
        Remove orange-like watermark colors by replacing them with white.

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

    @staticmethod
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

    @classmethod
    def split_by_white_lines(
        cls, img_arr: NDArray[np.uint8], padding: int = 4
    ) -> list[NDArray[np.uint8]]:
        """
        Split an RGB image (numpy array) into multiple blocks using full-white
        horizontal separator lines, then add fixed white padding to the top and
        bottom of each block.

        :param img_arr: Input RGB image array with shape (H, W, 3).
        :param padding: Number of white pixels to pad on the top and bottom.
        :return: List of sliced blocks as numpy arrays.
        """
        height = img_arr.shape[0]

        white_rows = [row for row in range(height) if np.all(img_arr[row] == cls.WHITE)]

        if not white_rows:
            blocks = [(0, height)]
        else:
            cut_points = [0] + white_rows + [height]
            blocks = [
                (cut_points[i - 1], cut_points[i])
                for i in range(1, len(cut_points))
                if cut_points[i] - cut_points[i - 1] > 1
            ]

        results = []
        for start, end in blocks:
            block = img_arr[start:end]

            padded_block = np.pad(
                block,
                pad_width=((padding, padding), (0, 0), (0, 0)),
                mode="constant",
                constant_values=255,
            )

            results.append(padded_block)

        return results

    @staticmethod
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

    @staticmethod
    def is_empty_image(img: NDArray[np.uint8]) -> bool:
        """
        Check if the image is completely white (255, 255, 255).

        :param img: Input image as (H, W, 3) numpy array
        :return: True if all pixels are white, False otherwise
        """
        return bool(np.all(img == 255))

    @staticmethod
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
        gray = img.mean(axis=2)
        max_scan = min(w, paragraph_threshold)
        return all(gray[:, col].min() >= white_threshold for col in range(max_scan))

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

    @staticmethod
    def _pil_to_rgb_array(img: Image.Image, white_bg: bool) -> NDArray[np.uint8]:
        """Convert PIL image to RGB numpy array, optionally flattening alpha."""
        if white_bg and ("A" in img.getbands()):
            img = img.convert("RGBA")
            bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
            bg.paste(img, mask=img.getchannel("A"))
            img = bg.convert("RGB")
        else:
            img = img.convert("RGB")

        return np.asarray(img)
