#!/usr/bin/env python3
"""
novel_downloader.utils.fontocr.ocr_v1
-------------------------------------

This class provides utility methods for optical character recognition (OCR)
and font mapping, primarily used for decrypting custom font encryption
on web pages (e.g., the Qidian website).
"""

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import paddle
from fontTools.ttLib import TTFont
from paddleocr import PaddleOCR
from PIL import Image, ImageDraw, ImageFont
from PIL.Image import Transpose

from novel_downloader.utils.constants import (
    REC_CHAR_MODEL_FILES,
    REC_IMAGE_SHAPE_MAP,
)
from novel_downloader.utils.hash_store import img_hash_store

from .model_loader import get_rec_chinese_char_model_dir

logger = logging.getLogger(__name__)


class FontOCRV1:
    """
    Version 1 of the FontOCR utility.

    :param use_freq: if True, weight OCR scores by character frequency
    :param cache_dir: base path to store font-map JSON data
    :param threshold: minimum confidence threshold [0.0-1.0]
    :param font_debug: if True, dump per-char debug images under cache_dir
    """

    # Default constants
    CHAR_IMAGE_SIZE = 64
    CHAR_FONT_SIZE = 52
    _freq_weight = 0.05

    # shared resources
    _global_char_freq_db: dict[str, int] = {}
    _global_ocr: PaddleOCR | None = None

    def __init__(
        self,
        cache_dir: str | Path,
        use_freq: bool = False,
        ocr_version: str = "v1.0",
        threshold: float = 0.0,
        font_debug: bool = False,
        **kwargs: Any,
    ) -> None:
        self.use_freq = use_freq
        self.ocr_version = ocr_version
        self.threshold = threshold
        self.font_debug = font_debug
        self._max_freq = 5

        self._cache_dir = Path(cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._fixed_map_dir = self._cache_dir / "fixed_font_map"
        self._fixed_map_dir.mkdir(exist_ok=True)

        if font_debug:
            self._debug_dir = self._cache_dir / "font_debug" / "badcase"
            self._debug_dir.mkdir(parents=True, exist_ok=True)

        # load shared NLP/OCR + frequency DB once
        self._load_ocr_model()
        if self.use_freq and not FontOCRV1._global_char_freq_db:
            self._load_char_freq_db()

    def _load_ocr_model(self) -> None:
        """
        Initialize the shared PaddleOCR model if not already loaded.
        """
        if FontOCRV1._global_ocr is not None:
            return

        gpu_available = paddle.device.is_compiled_with_cuda()
        self._char_model_dir = get_rec_chinese_char_model_dir(self.ocr_version)

        for fname in REC_CHAR_MODEL_FILES:
            full_path = self._char_model_dir / fname
            if not full_path.exists():
                raise FileNotFoundError(f"[FontOCR] Required file missing: {full_path}")

        char_dict_file = self._char_model_dir / "rec_custom_keys.txt"
        FontOCRV1._global_ocr = PaddleOCR(
            use_angle_cls=False,
            lang="ch",
            det=False,
            use_gpu=gpu_available,
            show_log=self.font_debug,
            rec_model_dir=str(self._char_model_dir),
            rec_char_dict_path=str(char_dict_file),
            rec_image_shape=REC_IMAGE_SHAPE_MAP[self.ocr_version],
            max_text_length=1,
            use_space_char=False,
        )

    def _load_char_freq_db(self) -> bool:
        """
        Loads character frequency data from a JSON file and
        assigns it to the instance variable.

        :return: True if successfully loaded, False otherwise.
        """
        try:
            char_freq_map_file = self._char_model_dir / "char_freq.json"
            with char_freq_map_file.open("r", encoding="utf-8") as f:
                FontOCRV1._global_char_freq_db = json.load(f)
            self._max_freq = max(FontOCRV1._global_char_freq_db.values())
            return True
        except Exception as e:
            logger.warning("[FontOCR] Failed to load char freq DB: %s", e)
            return False

    @staticmethod
    def _generate_char_image(
        char: str,
        render_font: ImageFont.FreeTypeFont,
        is_reflect: bool = False,
    ) -> Image.Image | None:
        """
        Render a single character into a square image.
        If is_reflect is True, flip horizontally.
        """
        size = FontOCRV1.CHAR_IMAGE_SIZE
        img = Image.new("L", (size, size), color=255)
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

    def ocr_text(
        self, img: Image.Image, top_k: int = 1
    ) -> str | list[tuple[str, float]]:
        """
        Run PaddleOCR on a single-image, return best match(es).
        If use_freq, adjust score by frequency bonus.
        """
        if not FontOCRV1._global_ocr:
            self._load_ocr_model()
        try:
            img_np = np.asarray(img)
            assert FontOCRV1._global_ocr is not None
            result = FontOCRV1._global_ocr.ocr(
                img_np, cls=False, det=False
            )  # returns List[List[ (text, score) ]]
            candidates = result[0] if result else []
            # attach frequency weight if enabled
            if self.use_freq and FontOCRV1._global_char_freq_db:
                adjusted = []
                for ch, score in candidates:
                    freq = FontOCRV1._global_char_freq_db.get(ch, self._max_freq)
                    bonus = (
                        FontOCRV1._freq_weight
                        * (self._max_freq - freq)
                        / self._max_freq
                    )
                    adjusted.append((ch, score + bonus))
                candidates = adjusted
            # filter by threshold
            filtered = [c for c in candidates if c[1] >= self.threshold]
            return filtered[0][0] if top_k == 1 and filtered else filtered[:top_k]
        except Exception as e:
            logger.error("[FontOCR] OCR failure: %s", e)
            return "" if top_k == 1 else []

    def query(self, img: Image.Image, top_k: int = 1) -> str | list[tuple[str, float]]:
        """
        First try hash-based lookup via img_hash_store;
        if no hit, fall back to ocr_text().
        """
        # quick hash lookup
        matches = img_hash_store.query(img, k=top_k)
        if matches:
            # matches is List[(label, dist)]
            return matches[0][0] if top_k == 1 else matches

        # fallback to OCR
        return self.ocr_text(img, top_k=top_k)

    def generate_font_map(
        self,
        fixed_font_path: str | Path,
        random_font_path: str | Path,
        char_set: set[str],
        refl_set: set[str],
        chapter_id: str | None = None,
    ) -> dict[str, str]:
        """
        Generates a mapping from encrypted (randomized) font characters to
        their real recognized characters by rendering and OCR-based matching.

        :param fixed_font_path: Path to the reference (fixed) font.
        :param random_font_path: Path to the obfuscated (random) font.
        :param char_set: Characters to process normally.
        :param refl_set: Characters to process as horizontally flipped.
        :param chapter_id: Chapter ID

        :returns mapping_result: { obf_char: real_char, ... }
        """
        mapping_result: dict[str, str] = {}
        fixed_map_file = self._fixed_map_dir / f"{Path(fixed_font_path).stem}.json"

        # 1) load or init fixed_font_map
        if fixed_map_file.exists():
            try:
                with open(fixed_map_file, encoding="utf-8") as f:
                    fixed_map = json.load(f)
            except Exception as e:
                logger.debug("[FontOCR] Failed to load fixed map file: %s", e)
                fixed_map = {}
        else:
            fixed_map = {}

        # prepare font renderers and cmap sets
        try:
            fixed_ttf = TTFont(fixed_font_path)
            fixed_chars = {chr(c) for c in fixed_ttf.getBestCmap()}
            fixed_font = ImageFont.truetype(str(fixed_font_path), self.CHAR_FONT_SIZE)

            random_ttf = TTFont(random_font_path)
            random_chars = {chr(c) for c in random_ttf.getBestCmap()}
            random_font = ImageFont.truetype(str(random_font_path), self.CHAR_FONT_SIZE)
        except Exception as e:
            logger.error("[FontOCR] Failed to load TTF fonts: %s", e)
            return mapping_result

        def _process(chars: set[str], reflect: bool = False) -> None:
            for ch in chars:
                try:
                    if ch in fixed_map:
                        mapping_result[ch] = fixed_map[ch]
                        logger.debug(
                            "[FontOCR] Using cached mapping: '%s' -> '%s'",
                            ch,
                            fixed_map[ch],
                        )
                        continue

                    if ch in fixed_chars:
                        font_to_use = fixed_font
                    elif ch in random_chars:
                        font_to_use = random_font
                    else:
                        logger.debug("[FontOCR] Skipping unknown char: '%s'", ch)
                        continue

                    img = self._generate_char_image(ch, font_to_use, is_reflect=reflect)
                    if img is None:
                        logger.debug("[FontOCR] Skipping unknown char: '%s'", ch)
                        continue

                    real = self.query(img, top_k=1)
                    if real:
                        real_char = (
                            str(real[0]) if isinstance(real, (list | tuple)) else real
                        )
                        mapping_result[ch] = real_char
                        if ch in fixed_chars:
                            fixed_map[ch] = real_char
                        logger.debug("[FontOCR] Mapped '%s' -> '%s'", ch, real_char)
                    elif self.font_debug and chapter_id:
                        dbg_path = self._debug_dir / f"{ord(ch):05X}_{chapter_id}.png"
                        img.save(dbg_path)
                        logger.debug("[FontOCR] Saved debug image: %s", dbg_path)
                except Exception as e:
                    logger.warning("[FontOCR] Failed to process char '%s': %s", ch, e)

        # process normal + reflected chars
        _process(char_set, reflect=False)
        _process(refl_set, reflect=True)

        # persist updated fixed_map
        try:
            with open(fixed_map_file, "w", encoding="utf-8") as f:
                json.dump(fixed_map, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error("[FontOCR] Failed to save fixed map: %s", e)

        return mapping_result
