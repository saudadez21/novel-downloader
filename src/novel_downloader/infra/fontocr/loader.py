#!/usr/bin/env python3
"""
novel_downloader.infra.fontocr.loader
-------------------------------------

Lazily load the FontOCR class.
"""

import logging
from typing import TYPE_CHECKING

from novel_downloader.schemas import FontOCRConfig

if TYPE_CHECKING:
    from .core import FontOCR

logger = logging.getLogger(__name__)

_FONT_OCR: "FontOCR | None" = None


def get_font_ocr(cfg: FontOCRConfig) -> "FontOCR | None":
    """
    Try to initialize and return a singleton FontOCR instance.
    Returns None if FontOCR or its dependencies are not available.
    """
    global _FONT_OCR
    if _FONT_OCR is None:
        try:
            from .core import FontOCR

            _FONT_OCR = FontOCR(
                model_name=cfg.model_name,
                model_dir=cfg.model_dir,
                input_shape=cfg.input_shape,
                device=cfg.device,
                precision=cfg.precision,
                cpu_threads=cfg.cpu_threads,
                enable_hpi=cfg.enable_hpi,
            )
        except ImportError:
            logger.warning(
                "FontOCR dependency not available "
                "(paddleocr / numpy / pillow / fonttools). "
                "Font decoding will be skipped."
            )
            return None
        except Exception as e:
            logger.warning("FontOCR initialization failed: %s", e, exc_info=True)
            return None

    return _FONT_OCR
