#!/usr/bin/env python3
"""
novel_downloader.plugins.utils.yuewen.qdfont
--------------------------------------------
"""

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Protocol
from urllib.parse import urlparse

import requests

from novel_downloader.infra.http_defaults import DEFAULT_USER_HEADERS
from novel_downloader.libs.filesystem import write_file

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray

    from novel_downloader.plugins.protocols.parser import _ParserContext

    class YuewenQDFontContext(_ParserContext, Protocol):
        """"""

        _IGNORED_CHARS: set[str]

        @staticmethod
        def _load_or_download_fixed_font(url: str, dest_path: Path) -> bytes: ...

        @staticmethod
        def _load_mapping_cache(path: Path) -> dict[str, str]: ...

        def _build_font_mapping(
            self,
            *,
            fixed_font_bytes: bytes,
            random_font_bytes: bytes,
            direct_chars: set[str],
            reflected_chars: set[str],
            existing_map: dict[str, str],
            batch_size: int = 32,
        ) -> dict[str, str]: ...


class YuewenQDFontMixin:
    """Yuewen/Qidian font obfuscation decoder mixin."""

    _IGNORED_CHARS: set[str] = {" ", "\n", "\u3000"}

    def _decode_qdfont(
        self: "YuewenQDFontContext",
        *,
        text: str,
        fixed_font_url: str,
        random_font_data: bytes,
        reflected_chars: list[str],
    ) -> str:
        if not text:
            return ""

        all_chars = set(text)
        char_set = all_chars - self._IGNORED_CHARS
        refl_set = set(reflected_chars)
        char_set -= refl_set

        if not char_set and not refl_set:
            return text

        fixed_font_url_path = urlparse(fixed_font_url).path
        font_name = fixed_font_url_path.rsplit("/", 1)[-1] or "font.woff2"
        fixed_font_path = self._cache_dir / "fixed_fonts" / font_name
        mapping_cache_path = (
            self._cache_dir / "fixed_font_maps" / f"{fixed_font_path.stem}.json"
        )

        fixed_font_path.parent.mkdir(parents=True, exist_ok=True)
        mapping_cache_path.parent.mkdir(parents=True, exist_ok=True)

        fixed_font_bytes = self._load_or_download_fixed_font(
            fixed_font_url, fixed_font_path
        )
        fixed_map = self._load_mapping_cache(mapping_cache_path)

        mapping = self._build_font_mapping(
            fixed_font_bytes=fixed_font_bytes,
            random_font_bytes=random_font_data,
            direct_chars=char_set,
            reflected_chars=refl_set,
            existing_map=fixed_map,
            batch_size=self._batch_size,
        )

        try:
            with mapping_cache_path.open("w", encoding="utf-8") as f:
                json.dump(fixed_map, f, ensure_ascii=False, indent=2)
        except Exception as exc:
            logger.error(
                "Failed to save font mapping cache %s: %s", mapping_cache_path, exc
            )

        return "".join(mapping.get(ch, ch) for ch in text) if mapping else text

    @staticmethod
    def _load_or_download_fixed_font(url: str, dest_path: Path) -> bytes:
        if dest_path.is_file():
            try:
                return dest_path.read_bytes()
            except Exception as exc:
                logger.warning(
                    "Failed to read cached fixed font %s: %s", dest_path, exc
                )

        logger.debug("Downloading fixed Yuewen font from %s", url)
        resp = requests.get(url, headers=DEFAULT_USER_HEADERS, timeout=10)
        resp.raise_for_status()
        font_bytes = resp.content
        write_file(font_bytes, dest_path, on_exist="overwrite")
        return font_bytes

    @staticmethod
    def _load_mapping_cache(path: Path) -> dict[str, str]:
        if not path.is_file():
            return {}
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except Exception as exc:
            logger.warning("Failed to load font mapping cache %s: %s", path, exc)
            return {}

    def _build_font_mapping(
        self: "YuewenQDFontContext",
        *,
        fixed_font_bytes: bytes,
        random_font_bytes: bytes,
        direct_chars: set[str],
        reflected_chars: set[str],
        existing_map: dict[str, str],
        batch_size: int = 32,
    ) -> dict[str, str]:
        from novel_downloader.libs import font_utils

        # start with cached known mappings
        mapping: dict[str, str] = {
            ch: existing_map[ch]
            for ch in (direct_chars | reflected_chars)
            if ch in existing_map
        }

        remaining_direct = direct_chars - mapping.keys()
        remaining_reflected = reflected_chars - mapping.keys()

        if not remaining_direct and not remaining_reflected:
            return mapping

        fixed_charset = font_utils.extract_font_charset_bytes(fixed_font_bytes)
        fixed_font = font_utils.load_render_font_bytes(fixed_font_bytes)

        random_charset = font_utils.extract_font_charset_bytes(random_font_bytes)
        random_font = font_utils.load_render_font_bytes(random_font_bytes)

        render_tasks: list[tuple[str, NDArray[np.uint8]]] = []

        for chars, reflect in ((remaining_direct, False), (remaining_reflected, True)):
            for ch in chars:
                if ch in fixed_charset:
                    font_obj = fixed_font
                elif ch in random_charset:
                    font_obj = random_font
                else:
                    continue

                img = font_utils.render_char_image_array(ch, font_obj, reflect)
                render_tasks.append((ch, img))

        if not render_tasks:
            return mapping

        images = [img for _, img in render_tasks]

        try:
            predictions = self._extract_text_from_image(images, batch_size=batch_size)
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
