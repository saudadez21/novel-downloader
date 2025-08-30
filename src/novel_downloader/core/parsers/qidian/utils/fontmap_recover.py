#!/usr/bin/env python3
"""
novel_downloader.core.parsers.qidian.utils.fontmap_recover
----------------------------------------------------------

Tools for generating and applying font character mappings
to recover obfuscated Qidian text.
"""

__all__ = [
    "generate_font_map",
    "apply_font_mapping",
]

import json
import logging
from pathlib import Path

import numpy as np
from fontTools.ttLib import TTFont
from PIL import ImageFont

logger = logging.getLogger(__name__)
CHAR_FONT_SIZE = 52


def generate_font_map(
    fixed_font_path: Path,
    random_font_path: Path,
    char_set: set[str],
    refl_set: set[str],
    cache_dir: Path,
    batch_size: int = 32,
) -> dict[str, str]:
    """
    Build a mapping from scrambled font chars to real chars.

    Uses OCR to compare rendered glyphs from a known (fixed) font and an
    obfuscated (random) font. Results are cached in JSON so repeated runs
    are faster.

    :param fixed_font_path: fixed font file.
    :param random_font_path: random font file.
    :param char_set: Characters to match directly.
    :param refl_set: Characters to match in flipped form.
    :param cache_dir: Directory to save/load cached results.
    :param batch_size: How many chars to OCR per batch.

    :return: { obf_char: real_char, ... }
    """
    try:
        from novel_downloader.utils.fontocr import get_font_ocr

        font_ocr = get_font_ocr(batch_size=batch_size)
    except ImportError:
        logger.warning("[QidianParser] FontOCR not available, font decoding will skip")
        return {}

    mapping_result: dict[str, str] = {}
    fixed_map_file = cache_dir / "fixed_font_map" / f"{Path(fixed_font_path).stem}.json"
    fixed_map_file.parent.mkdir(parents=True, exist_ok=True)

    # load existing cache
    try:
        with open(fixed_map_file, encoding="utf-8") as f:
            fixed_map = json.load(f)
        cached_chars = set(fixed_map.keys())
        mapping_result.update({ch: fixed_map[ch] for ch in char_set if ch in fixed_map})
        mapping_result.update({ch: fixed_map[ch] for ch in refl_set if ch in fixed_map})
        char_set = set(char_set) - cached_chars
        refl_set = set(refl_set) - cached_chars
    except Exception:
        fixed_map = {}
        cached_chars = set()

    # prepare font renderers and cmap sets
    try:
        fixed_ttf = TTFont(fixed_font_path)
        fixed_chars = {chr(c) for c in fixed_ttf.getBestCmap()}
        fixed_font = ImageFont.truetype(str(fixed_font_path), CHAR_FONT_SIZE)

        random_ttf = TTFont(random_font_path)
        random_chars = {chr(c) for c in random_ttf.getBestCmap()}
        random_font = ImageFont.truetype(str(random_font_path), CHAR_FONT_SIZE)
    except Exception as e:
        logger.error("[FontOCR] Failed to load TTF fonts: %s", e)
        return mapping_result

    def _render_batch(chars: list[tuple[str, bool]]) -> list[tuple[str, np.ndarray]]:
        out = []
        for ch, reflect in chars:
            if ch in fixed_chars:
                font = fixed_font
            elif ch in random_chars:
                font = random_font
            else:
                continue
            img = font_ocr.render_char_image_array(ch, font, reflect)
            if img is not None:
                out.append((ch, img))
        return out

    # process normal and reflected sets together
    for chars, reflect in [(list(char_set), False), (list(refl_set), True)]:
        for batch_chars in font_ocr._chunked(chars, font_ocr._batch_size):
            # render all images in this batch
            to_render = [(ch, reflect) for ch in batch_chars]
            rendered = _render_batch(to_render)
            if not rendered:
                continue

            # query OCR+vec simultaneously
            imgs_to_query = [img for (ch, img) in rendered]
            fused = font_ocr.predict(imgs_to_query, top_k=1)

            # pick best per char, apply threshold + cache
            for (ch, _), preds in zip(rendered, fused, strict=False):
                if not preds:
                    continue
                real_char, _ = preds[0]
                mapping_result[ch] = real_char
                fixed_map[ch] = real_char

    # persist updated fixed_map
    try:
        with open(fixed_map_file, "w", encoding="utf-8") as f:
            json.dump(fixed_map, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error("[FontOCR] Failed to save fixed map: %s", e)

    return mapping_result


def apply_font_mapping(text: str, font_map: dict[str, str]) -> str:
    """
    Replace each character in `text` using `font_map`,
    leaving unmapped characters unchanged.

    :param text: The input string, possibly containing obfuscated font chars.
    :param font_map: A dict mapping obfuscated chars to real chars.
    :return: The de-obfuscated text.
    """
    return "".join(font_map.get(ch, ch) for ch in text)
