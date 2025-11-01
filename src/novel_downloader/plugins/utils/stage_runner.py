#!/usr/bin/env python3
"""
novel_downloader.plugins.utils.stage_runner
-------------------------------------------
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from novel_downloader.infra.persistence.chapter_storage import ChapterStorage
from novel_downloader.plugins import registrar
from novel_downloader.schemas import (
    BookConfig,
    BookInfoDict,
    ChapterDict,
    ChapterInfoDict,
    PipelineMeta,
    ProcessorConfig,
    VolumeInfoDict,
)


class StageRunner:
    """
    Encapsulates per-stage I/O, incremental logic, batching, and provenance.
    """

    BATCH = 200

    def __init__(self, base_dir: Path, book: BookConfig) -> None:
        self.base_dir = base_dir
        self.book = book

        book_info_path = base_dir / "book_info.raw.json"
        self.book_info = self._load_book_info(book_info_path)
        self.pipeline_json_path = base_dir / "pipeline.json"
        self.meta = self._load_pipeline_meta(self.pipeline_json_path)
        self.meta["pipeline"] = []
        self._save_pipeline_meta()

        filtered_vols = self._filter_volumes(
            self.book_info.get("volumes", []),
            book.start_id,
            book.end_id,
            set(book.ignore_ids or ()),
        )
        self.chap_ids = self._collect_chapter_ids(filtered_vols)
        self.prev_output_base: str | None = None
        self.completed_stages: list[str] = []

    def run(
        self,
        pconf: ProcessorConfig,
        *,
        on_progress: Callable[[int, int], None],
        chap_ids: list[str] | None = None,
    ) -> None:
        chap_ids = self.chap_ids if chap_ids is None else chap_ids
        stage_name = pconf.name

        in_base = self.prev_output_base or "chapter.raw.sqlite"
        out_base = f"chapter.{stage_name}.sqlite"
        in_path = self.base_dir / in_base
        out_path = self.base_dir / out_base

        if not in_path.is_file():
            raise FileNotFoundError(f"Upstream stage output missing: {in_path.name}")

        processor = registrar.get_processor(stage_name, pconf.options)
        self.book_info = processor.process_book_info(self.book_info)
        self._save_book_info(stage_name)

        incremental = self._is_incremental(pconf)
        chap_set = set(chap_ids)
        total = len(chap_ids)

        with (
            ChapterStorage(self.base_dir, in_base) as instore,
            ChapterStorage(self.base_dir, out_base) as outstore,
        ):
            in_exists = instore.existing_ids()
            missing_input = chap_set - in_exists

            if incremental:
                out_exists = outstore.existing_ids()
                clean_upstream = instore.clean_ids()
                reusable = (out_exists & clean_upstream) & chap_set
            else:
                reusable = set()

            to_process = chap_set - reusable - missing_input
            done = len(reusable) + len(missing_input)
            if done:
                on_progress(done, total)

            to_process_list = list(to_process)
            in_map = instore.get_chapters(to_process_list)

            batch_need: list[ChapterDict] = []
            batch_ok: list[ChapterDict] = []

            for cid in to_process_list:
                src = in_map.get(cid)

                if src is None:
                    done += 1
                    on_progress(done, total)
                    continue

                processed = processor.process_chapter(src)

                if instore.need_refetch(cid):
                    batch_need.append(processed)
                else:
                    batch_ok.append(processed)

                # Flush periodically
                if (len(batch_need) + len(batch_ok)) >= self.BATCH:
                    self._flush(outstore, batch_need, batch_ok)

                done += 1
                on_progress(done, total)

            # Final flush
            self._flush(outstore, batch_need, batch_ok)

        self._update_pipeline_meta(pconf, out_path)
        self.prev_output_base = out_base

    @staticmethod
    def _load_book_info(path: Path) -> BookInfoDict:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise ValueError(f"Corrupt JSON in {path}: {e}") from e
        if not isinstance(data, dict):
            raise ValueError(
                f"Invalid JSON structure in {path}: expected an object at the top"
            )
        return cast(BookInfoDict, data)

    @staticmethod
    def _load_pipeline_meta(path: Path) -> PipelineMeta:
        if not path.is_file():
            return {"pipeline": [], "executed": {}}
        try:
            return cast(PipelineMeta, json.loads(path.read_text(encoding="utf-8")))
        except Exception:
            # Corrupted file -> start fresh; will be overwritten on next save.
            return {"pipeline": [], "executed": {}}

    def _save_book_info(self, stage_name: str) -> None:
        (self.base_dir / f"book_info.{stage_name}.json").write_text(
            json.dumps(self.book_info, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _save_pipeline_meta(self) -> None:
        self.pipeline_json_path.write_text(
            json.dumps(self.meta, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _update_pipeline_meta(self, pconf: ProcessorConfig, out_path: Path) -> None:
        self.meta["executed"][pconf.name] = {
            "file": out_path.name,
            "processed_at": self._utc_now_iso(),
            "depends_on": list(self.completed_stages),
            "config_hash": self._hash_config(pconf.options),
        }
        self.completed_stages.append(pconf.name)
        self.meta["pipeline"] = list(self.completed_stages)
        self._save_pipeline_meta()

    def _is_incremental(self, pconf: ProcessorConfig) -> bool:
        if pconf.overwrite:
            return False

        cfg_hash = self._hash_config(pconf.options)
        filename = f"chapter.{pconf.name}.sqlite"
        filepath = self.base_dir / filename
        rec = self.meta["executed"].get(pconf.name)
        if not rec:
            return False

        return (
            filepath.is_file()
            and rec.get("file") == filename
            and rec.get("config_hash") == cfg_hash
            and rec.get("depends_on") == self.completed_stages
        )

    @staticmethod
    def _flush(
        outstore: ChapterStorage,
        need: list[ChapterDict],
        ok: list[ChapterDict],
    ) -> None:
        if need:
            outstore.upsert_chapters(need, need_refetch=True)
            need.clear()
        if ok:
            outstore.upsert_chapters(ok, need_refetch=False)
            ok.clear()

    @staticmethod
    def _filter_volumes(
        vols: list[VolumeInfoDict],
        start_id: str | None,
        end_id: str | None,
        ignore: set[str],
    ) -> list[VolumeInfoDict]:
        """
        Rebuild volumes to include only chapters within
        the [start_id, end_id] range (inclusive),
        while excluding any chapter IDs in `ignore`.
        """
        if start_id is None and end_id is None and not ignore:
            return vols

        started = start_id is None
        finished = False
        result: list[VolumeInfoDict] = []

        for vol in vols:
            if finished:
                break

            kept: list[ChapterInfoDict] = []

            for ch in vol.get("chapters", []):
                cid = ch.get("chapterId")
                if not cid:
                    continue

                # wait until hit the start_id
                if not started:
                    if cid == start_id:
                        started = True
                    else:
                        continue

                if cid not in ignore:
                    kept.append(ch)

                # check for end_id after keeping
                if end_id is not None and cid == end_id:
                    finished = True
                    break

            if kept:
                result.append(
                    {
                        **vol,
                        "chapters": kept,
                    }
                )

        return result

    @staticmethod
    def _collect_chapter_ids(vols: list[VolumeInfoDict]) -> list[str]:
        """Flatten all chapterIds from a list of volumes."""
        return [
            ch["chapterId"]
            for v in vols
            for ch in v.get("chapters", [])
            if isinstance(ch.get("chapterId"), str)
        ]

    @staticmethod
    def _utc_now_iso() -> str:
        return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    @staticmethod
    def _hash_config(options: dict[str, Any]) -> str:
        """Stable short hash for a processor's options."""
        data = json.dumps(
            options or {}, sort_keys=True, ensure_ascii=False, separators=(",", ":")
        )
        return hashlib.sha256(data.encode("utf-8")).hexdigest()[:12]
