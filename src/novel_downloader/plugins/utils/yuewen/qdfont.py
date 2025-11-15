#!/usr/bin/env python3
"""
novel_downloader.plugins.utils.yuewen.qdfont
--------------------------------------------
"""

from __future__ import annotations

__all__ = ["decode_qdfont_text"]

import json
import logging
from pathlib import Path
from urllib.parse import urlparse

import requests

from novel_downloader.infra.http_defaults import DEFAULT_USER_HEADERS
from novel_downloader.libs.filesystem import write_file
from novel_downloader.libs.fontocr import get_font_ocr
from novel_downloader.schemas import FontOCRConfig

logger = logging.getLogger(__name__)
_IGNORED_CHARS: set[str] = {" ", "\n", "\u3000"}


def decode_qdfont_text(
    text: str,
    fixed_font_url: str,
    random_font_data: bytes,
    reflected_chars: list[str],
    cache_root: Path,
    fontocr_config: FontOCRConfig | None = None,
    batch_size: int = 32,
) -> str:
    """
    Decode obfuscated text from Yuewen/QD using fixed + random obfuscated fonts.

    :param text: Raw text containing obfuscated glyphs.
    :param fixed_font_url: URL to the fixed (site-wide) obfuscated font.
    :param random_font_data: Raw bytes of the random/ephemeral font from the page.
    :param reflected_chars: Characters that should also be tried with reflection.
    :param cache_root: Directory used to store fonts and OCR mapping JSON.
    :param fontocr_config: Optional configuration passed to get_font_ocr().
    :param batch_size: Number of characters to OCR in one batch.

    :return: De-obfuscated text with blank lines stripped and lines trimmed.
    """
    if not text:
        return ""

    all_chars = set(text)
    char_set = all_chars - _IGNORED_CHARS
    refl_set = set(reflected_chars)
    char_set -= refl_set

    if not char_set and not refl_set:
        return text

    font_name = _font_filename(fixed_font_url)
    fixed_font_path = cache_root / "fixed_fonts" / font_name
    mapping_cache_path = cache_root / "fixed_font_maps" / f"{fixed_font_path.stem}.json"

    fixed_font_path.parent.mkdir(parents=True, exist_ok=True)
    mapping_cache_path.parent.mkdir(parents=True, exist_ok=True)

    # Load or download fixed font
    fixed_font_bytes = _load_or_download_fixed_font(fixed_font_url, fixed_font_path)

    # Load existing mapping cache
    fixed_map = _load_mapping_cache(mapping_cache_path)

    # Build / update mapping
    mapping = _build_font_mapping(
        fixed_font_bytes=fixed_font_bytes,
        random_font_bytes=random_font_data,
        direct_chars=char_set,
        reflected_chars=refl_set,
        existing_map=fixed_map,
        fontocr_config=fontocr_config,
        batch_size=batch_size,
    )

    _save_mapping_cache(mapping_cache_path, fixed_map)
    return _apply_font_mapping(text, mapping)


def _font_filename(url: str) -> str:
    """Extract filename from URL path reliably."""
    path = urlparse(url).path
    name = path.rsplit("/", 1)[-1]
    return name or "font.woff2"


def _load_or_download_fixed_font(url: str, dest_path: Path) -> bytes:
    """
    Load the fixed font bytes from cache, or download and cache them.

    Returns empty bytes on failure (the decoder will then fall back
    to using only whatever fonts it has).
    """
    if dest_path.is_file():
        try:
            return dest_path.read_bytes()
        except Exception as exc:
            logger.warning("Failed to read cached fixed font %s: %s", dest_path, exc)

    logger.debug("Downloading fixed Yuewen font from %s", url)
    resp = requests.get(url, headers=DEFAULT_USER_HEADERS, timeout=10)
    resp.raise_for_status()
    font_bytes = resp.content
    write_file(font_bytes, dest_path, on_exist="overwrite")
    return font_bytes


def _load_mapping_cache(path: Path) -> dict[str, str]:
    """Load a JSON mapping cache of obf_char -> real_char."""
    if not path.is_file():
        return {}

    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except Exception as exc:
        logger.warning("Failed to load font mapping cache %s: %s", path, exc)
    return {}


def _save_mapping_cache(path: Path, mapping: dict[str, str]) -> None:
    """Save the mapping cache to JSON."""
    try:
        with path.open("w", encoding="utf-8") as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)
    except Exception as exc:
        logger.error("Failed to save font mapping cache %s: %s", path, exc)


def _build_font_mapping(
    fixed_font_bytes: bytes,
    random_font_bytes: bytes,
    direct_chars: set[str],
    reflected_chars: set[str],
    existing_map: dict[str, str],
    fontocr_config: FontOCRConfig | None = None,
    batch_size: int = 32,
) -> dict[str, str]:
    """
    Build a mapping from obfuscated characters to real characters.

    This function:
      * Uses `existing_map` for already-known characters.
      * Uses font OCR with the fixed and random fonts for missing characters.
      * Updates `existing_map` in-place with any new discoveries.
      * Returns a complete mapping for all requested chars.

    :param fixed_font_bytes: Raw bytes of the fixed (site-wide) font.
    :param random_font_bytes: Raw bytes of the random (per-page) font.
    :param direct_chars: Characters to be rendered normally.
    :param reflected_chars: Characters to be rendered with reflection/mirroring.
    :param existing_map: Cache of previously known mappings (mutated in-place).
    :param fontocr_config: Optional configuration passed to the OCR factory.
    :param batch_size: OCR batch size.

    :return: A mapping containing entries for all characters that could be decoded.
    """
    font_ocr = get_font_ocr(fontocr_config)
    if not font_ocr:
        logger.debug("Font OCR backend not available; returning existing_map only.")
        return {
            ch: existing_map[ch]
            for ch in (direct_chars | reflected_chars)
            if ch in existing_map
        }

    mapping: dict[str, str] = {
        ch: existing_map[ch]
        for ch in (direct_chars | reflected_chars)
        if ch in existing_map
    }

    remaining_direct = direct_chars - mapping.keys()
    remaining_reflected = reflected_chars - mapping.keys()

    if not remaining_direct and not remaining_reflected:
        return mapping

    fixed_charset = font_ocr.extract_font_charset_bytes(fixed_font_bytes)
    fixed_font = font_ocr.load_render_font_bytes(fixed_font_bytes)

    random_charset = font_ocr.extract_font_charset_bytes(random_font_bytes)
    random_font = font_ocr.load_render_font_bytes(random_font_bytes)

    render_tasks = []  # (char, image_array)

    for chars, reflect in ((remaining_direct, False), (remaining_reflected, True)):
        for ch in chars:
            if ch in fixed_charset:
                font_obj = fixed_font
            elif ch in random_charset:
                font_obj = random_font
            else:
                continue

            img = font_ocr.render_char_image_array(ch, font_obj, reflect)
            render_tasks.append((ch, img))

    images = [img for _, img in render_tasks]
    try:
        predictions = font_ocr.predict(images, batch_size=batch_size)
    except Exception as exc:
        logger.warning("Font OCR predict failed: %s", exc)
        return mapping

    for (ch, _), (real_char, _) in zip(render_tasks, predictions, strict=False):
        if not real_char:
            continue
        real_char = str(real_char)
        mapping[ch] = real_char
        existing_map[ch] = real_char

    return mapping


def _apply_font_mapping(text: str, font_map: dict[str, str]) -> str:
    """
    Replace each character in `text` using `font_map`,
    leaving unmapped characters unchanged.
    """
    if not font_map:
        return text
    return "".join(font_map.get(ch, ch) for ch in text)
