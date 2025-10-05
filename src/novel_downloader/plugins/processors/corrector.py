#!/usr/bin/env python3
"""
novel_downloader.plugins.processors.corrector
---------------------------------------------

Runs Chinese text correction using pycorrector engines (kenlm/MacBERT/T5/etc.)
on book metadata and chapter content.
"""

from __future__ import annotations

import copy
import logging
from collections.abc import Callable
from typing import Any

from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import BookInfoDict, ChapterDict

logger = logging.getLogger(__name__)

SingleHandler = Callable[[str], str]
BatchHandler = Callable[[list[str]], list[str]]


@registrar.register_processor()
class CorrectorProcessor:
    """
    Implements the Processor protocol using pycorrector.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        self._apply_title = bool(config.get("apply_title", True))
        self._apply_content = bool(config.get("apply_content", True))
        self._apply_author = bool(config.get("apply_author", False))
        self._apply_tags = bool(config.get("apply_tags", False))

        self._skip_if_len_le = config.get("skip_if_len_le")

        self._engine = (config.get("engine") or "kenlm").lower()
        self._batch_handler = self._build_batch_handler(self._engine, config)

    def process_book_info(self, book_info: BookInfoDict) -> BookInfoDict:
        """
        Apply correction to book metadata and nested structures.
        """
        bi = copy.deepcopy(book_info)

        # Title-like
        if self._apply_title and isinstance(name := bi.get("book_name"), str):
            bi["book_name"] = self._correct_text(name)
        if self._apply_author and isinstance(author := bi.get("author"), str):
            bi["author"] = self._correct_text(author)

        # Content-like
        if self._apply_content and isinstance(summary := bi.get("summary"), str):
            bi["summary"] = self._correct_text(summary)

        # Tags
        if self._apply_tags and isinstance(tags := bi.get("tags"), list):
            bi["tags"] = [
                self._correct_text(t) if isinstance(t, str) else t for t in tags
            ]

        # Volumes & chapters
        if isinstance(volumes := bi.get("volumes"), list):
            for vol in volumes:
                if self._apply_title and isinstance(
                    vname := vol.get("volume_name"), str
                ):
                    vol["volume_name"] = self._correct_text(vname)

                if self._apply_content and isinstance(
                    intro := vol.get("volume_intro"), str
                ):
                    vol["volume_intro"] = self._correct_text(intro)

                if isinstance(chapters := vol.get("chapters"), list):
                    for cinfo in chapters:
                        if self._apply_title and isinstance(
                            ctitle := cinfo.get("title"), str
                        ):
                            cinfo["title"] = self._correct_text(ctitle)

        return bi

    def process_chapter(self, chapter: ChapterDict) -> ChapterDict:
        """
        Apply correction to a single chapter (title + content).
        """
        ch = copy.deepcopy(chapter)

        if self._apply_title and isinstance(title := ch.get("title"), str):
            ch["title"] = self._correct_text(title)
        if self._apply_content and isinstance(content := ch.get("content"), str):
            ch["content"] = self._correct_text(content)

        return ch

    def _build_batch_handler(self, engine: str, cfg: dict[str, Any]) -> BatchHandler:
        """Create engine-specific batch handler with normalized outputs."""
        try:
            import pycorrector  # ~13s import
        except ImportError as e:
            missing = getattr(e, "name", "unknown")
            raise ImportError(
                f"Failed while importing pycorrector "
                f"for engine='{engine}'. Missing dependency: '{missing}'.\n"
                "To install pycorrector:\n"
                "    pip install pycorrector\n"
                "To install torch (CPU version):\n"
                "    pip install torch torchvision torchaudio\n"
                "For GPU (CUDA) setup, see: https://pytorch.org/get-started/locally/"
            ) from e

        # Construct engine
        kwargs = self._engine_kwargs(engine, cfg)
        if engine == "kenlm":
            model = pycorrector.Corrector(**kwargs)

        elif engine == "macbert":
            model = pycorrector.MacBertCorrector(**kwargs)

        elif engine == "t5":
            model = pycorrector.T5Corrector(**kwargs)

        elif engine == "ernie_csc":
            model = pycorrector.ErnieCscCorrector(**kwargs)

        elif engine == "gpt":
            from pycorrector.gpt.gpt_corrector import GptCorrector

            model = GptCorrector(**kwargs)

        elif engine == "mucgec_bart":
            from pycorrector.mucgec_bart.mucgec_bart_corrector import (
                MuCGECBartCorrector,
            )

            model = MuCGECBartCorrector(**kwargs)

        else:
            raise ValueError(f"Unknown pycorrector engine: {engine}")

        try:
            _ = model.correct_batch(["。"])
        except (ModuleNotFoundError, ImportError) as e:
            missing = getattr(e, "name", "unknown")
            raise ImportError(
                "pycorrector runtime dependency missing while testing "
                f"engine='{engine}': '{missing}'."
            ) from e
        except Exception as e:
            logger.warning(
                "Self-test failed for engine='%s'; "
                "continuing with passthrough. Error: %s",
                engine,
                e,
            )

        # Normalizer
        def _norm(item: Any, original: str) -> str:
            if isinstance(item, dict):
                tgt = item.get("target")
                return tgt if isinstance(tgt, str) else original
            if isinstance(item, str):
                return item
            return original

        # Normalized handlers
        def _batch(texts: list[str]) -> list[str]:
            if not texts:
                return []
            try:
                rv = model.correct_batch(texts)
                if isinstance(rv, list) and rv and len(rv) == len(texts):
                    return [_norm(item, texts[i]) for i, item in enumerate(rv)]
            except (ModuleNotFoundError, ImportError) as e:
                missing = getattr(e, "name", "unknown")
                raise ImportError(
                    f"Missing runtime dependency '{missing}' "
                    f"during .correct_batch() for engine='{engine}'."
                ) from e
            except Exception as e:
                logger.warning(
                    ".correct_batch() failed for engine='%s'; "
                    "falling back per-item. Error: %s",
                    engine,
                    e,
                )

            out: list[str] = []
            for t in texts:
                try:
                    res = model.correct(t)
                    out.append(_norm(res, t))
                except (ModuleNotFoundError, ImportError) as e:
                    missing = getattr(e, "name", "unknown")
                    raise ImportError(
                        f"Missing runtime dependency '{missing}' "
                        f"during .correct() for engine='{engine}'."
                    ) from e
            return out

        return _batch

    def _correct_text(self, text: str) -> str:
        """
        Correct a single string. Optionally line-by-line to preserve structure.
        Uses engine-normalized handlers to avoid pycorrector's type unions.
        """
        if not isinstance(text, str):
            return text

        lines: list[str] = text.splitlines()
        if not lines:
            return text

        th = self._skip_if_len_le

        def _needs(seg: str) -> bool:
            s = seg.strip()
            if not s:
                return False
            if th is not None and len(s) <= int(th):
                return False
            return True

        mask = [_needs(seg) for seg in lines]
        batch = [seg for seg, m in zip(lines, mask, strict=False) if m]

        if not batch:
            return "\n".join(lines)

        fixed = self._batch_handler(batch)

        if not isinstance(fixed, list) or len(fixed) != sum(mask):
            logger.warning("Batch handler size mismatch; using per-item fallback.")
            fixed = []
            for seg in batch:
                x = self._batch_handler([seg])
                fixed.append(x[0] if isinstance(x, list) and x else seg)

        it = iter(fixed)
        out_lines = [
            next(it) if m else seg for seg, m in zip(lines, mask, strict=False)
        ]
        return "\n".join(out_lines)

    @staticmethod
    def _engine_kwargs(engine: str, cfg: dict[str, Any]) -> dict[str, Any]:
        """
        Build constructor kwargs for the given engine, using only user-provided config.
        """
        if engine == "kenlm":
            return _subset(
                cfg,
                "language_model_path",
                "custom_confusion_path_or_dict",
                "proper_name_path",
                "common_char_path",
                "same_pinyin_path",
                "same_stroke_path",
            )
        elif engine == "macbert" or engine == "t5" or engine == "ernie_csc":
            return _subset(cfg, "model_name_or_path")
        elif engine == "gpt":
            return _subset(cfg, "model_name_or_path", "model_type", "peft_name")
        elif engine == "mucgec_bart":
            return _subset(cfg, "model_name_or_path")
        else:
            raise ValueError(f"Unknown pycorrector engine: {engine}")


def _subset(d: dict[str, Any], *keys: str) -> dict[str, Any]:
    """Return only keys present in d."""
    return {k: d[k] for k in keys if k in d}
