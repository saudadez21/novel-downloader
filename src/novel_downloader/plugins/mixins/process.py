#!/usr/bin/env python3
"""
novel_downloader.plugins.mixins.process
---------------------------------------
"""

import json
import logging
from typing import TYPE_CHECKING, Any, Protocol

from novel_downloader.infra.persistence.chapter_storage import ChapterStorage
from novel_downloader.plugins import registrar
from novel_downloader.schemas import (
    BookConfig,
    BookInfoDict,
    ChapterDict,
    ProcessorConfig,
)

logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from novel_downloader.plugins.protocols import ProcessUI, _ClientContext

    class ProcessClientContext(_ClientContext, Protocol):
        """"""

        PROCESS_BATCH: int

        def _pc_prepare_env(
            self,
            book: BookConfig,
            ui: "ProcessUI | None",
        ) -> tuple[BookInfoDict, list[str], set[str]] | None:
            ...

        def _pc_run_stage(
            self,
            book: BookConfig,
            book_info: BookInfoDict,
            pconf: ProcessorConfig,
            chap_ids: list[str],
            chap_set: set[str],
            prev_output: str,
            completed_stages: list[str],
            ui: "ProcessUI | None",
        ) -> BookInfoDict:
            ...

        def _pc_init_pipeline(
            self,
            book_id: str,
            processors: list[ProcessorConfig],
        ) -> None:
            ...

        def _pc_record_execution(
            self,
            book_id: str,
            pconf: ProcessorConfig,
            completed_stages: list[str],
        ) -> None:
            ...

        def _pc_is_incremental(
            self,
            book_id: str,
            pconf: ProcessorConfig,
            completed_stages: list[str],
        ) -> bool:
            ...

        @staticmethod
        def _pc_hash_config(options: dict[str, Any]) -> str:
            ...

        @staticmethod
        def _utc_now_iso() -> str:
            ...


class ProcessMixin:
    """
    Provides the `process_book()` API for clients.
    """

    PROCESS_BATCH = 200

    def process_book(
        self: "ProcessClientContext",
        book: BookConfig,
        processors: list[ProcessorConfig],
        *,
        ui: "ProcessUI | None" = None,
        **kwargs: Any,
    ) -> None:
        """
        Run all processors for a single book.

        :param book: BookConfig to process.
        :param ui: Optional ProcessUI to report progress.
        """
        prep = self._pc_prepare_env(book, ui)
        if prep is None:
            return

        book_info, chap_ids, chap_set = prep

        stage_name: str = "Unknown"
        prev_output = "chapter.raw.sqlite"
        completed_stages: list[str] = []
        self._pc_init_pipeline(book.book_id, processors)

        try:
            for pconf in processors:
                stage_name = pconf.name
                if ui:
                    ui.on_stage_start(book, stage_name)

                book_info = self._pc_run_stage(
                    book,
                    book_info,
                    pconf,
                    chap_ids,
                    chap_set,
                    prev_output,
                    completed_stages,
                    ui,
                )

                self._pc_record_execution(book.book_id, pconf, completed_stages)
                completed_stages.append(stage_name)
                prev_output = f"chapter.{stage_name}.sqlite"

                if ui:
                    ui.on_stage_complete(book, stage_name)

            logger.info("All stages completed successfully for book %s", book.book_id)

        except Exception as e:
            logger.warning(
                "Processing failed at stage '%s' for book %s: %s",
                stage_name,
                book.book_id,
                e,
            )

    def _pc_prepare_env(
        self: "ProcessClientContext",
        book: BookConfig,
        ui: "ProcessUI | None",
    ) -> tuple[BookInfoDict, list[str], set[str]] | None:
        book_id = book.book_id
        base_dir = self._raw_data_dir / book_id

        # Check raw stage files
        raw_sqlite = base_dir / "chapter.raw.sqlite"
        raw_info = base_dir / "book_info.raw.json"

        if not raw_sqlite.is_file() or not raw_info.is_file():
            if ui:
                ui.on_missing(book, "raw", raw_sqlite)
            return None

        # Load raw book_info
        book_info = self._load_book_info(book_id, "raw")

        # Extract chapters (range + ignore)
        chap_ids = self._extract_chapter_ids(
            book_info["volumes"], book.start_id, book.end_id, book.ignore_ids
        )
        chap_set = set(chap_ids)

        return (book_info, chap_ids, chap_set)

    def _pc_run_stage(
        self: "ProcessClientContext",
        book: BookConfig,
        book_info: BookInfoDict,
        pconf: ProcessorConfig,
        chap_ids: list[str],
        chap_set: set[str],
        prev_output: str,
        completed_stages: list[str],
        ui: "ProcessUI | None",
    ) -> BookInfoDict:
        book_id = book.book_id
        base_dir = self._raw_data_dir / book_id
        stage_name = pconf.name

        # Determine input + output paths
        in_base = prev_output
        out_base = f"chapter.{stage_name}.sqlite"
        in_path = base_dir / in_base

        if not in_path.is_file():
            raise FileNotFoundError(f"Upstream stage output missing: {in_path.name}")

        # Build processor
        processor = registrar.get_processor(stage_name, pconf.options)

        # Process top-level book info
        book_info = processor.process_book_info(book_info)
        self._save_book_info(book_id, book_info, stage=stage_name)

        incremental = self._pc_is_incremental(book_id, pconf, completed_stages)
        total = len(chap_ids)

        with (
            ChapterStorage(base_dir, in_base) as instore,
            ChapterStorage(base_dir, out_base) as outstore,
        ):
            in_exists = instore.existing_ids()
            missing_input = chap_set - in_exists

            if incremental:
                logger.info(
                    "Book %s stage '%s': incremental mode enabled (deps=%s)",
                    book_id,
                    stage_name,
                    ", ".join(completed_stages) or "none",
                )
                out_exists = outstore.existing_ids()
                clean_upstream = instore.clean_ids()
                reusable = (out_exists & clean_upstream) & chap_set
            else:
                reusable = set()

            to_process = chap_set - reusable - missing_input
            done = len(reusable) + len(missing_input)

            if done and ui:
                ui.on_stage_progress(book, stage_name, done, total)

            to_process_list = list(to_process)
            in_map = instore.get_chapters(to_process_list)

            batch_need: list[ChapterDict] = []
            batch_ok: list[ChapterDict] = []

            def _flush() -> None:
                if batch_need:
                    outstore.upsert_chapters(batch_need, need_refetch=True)
                    batch_need.clear()
                if batch_ok:
                    outstore.upsert_chapters(batch_ok, need_refetch=False)
                    batch_ok.clear()

            for cid in to_process_list:
                src = in_map.get(cid)

                if src is None:
                    done += 1
                    if ui:
                        ui.on_stage_progress(book, stage_name, done, total)
                    continue

                processed = processor.process_chapter(src)

                if instore.need_refetch(cid):
                    batch_need.append(processed)
                else:
                    batch_ok.append(processed)

                if (len(batch_need) + len(batch_ok)) >= self.PROCESS_BATCH:
                    _flush()

                done += 1
                if ui:
                    ui.on_stage_progress(book, stage_name, done, total)

            _flush()

        return book_info

    def _pc_is_incremental(
        self: "ProcessClientContext",
        book_id: str,
        pconf: ProcessorConfig,
        completed_stages: list[str],
    ) -> bool:
        """
        Determine whether a processor can reuse its previous result.

        Logic:
          * overwrite = False
          * prior record exists in pipeline meta
          * file exists
          * config hash unchanged
          * dependencies unchanged
        """
        if pconf.overwrite:
            return False

        base = self._book_dir(book_id)
        # Load full metadata
        meta = self._load_pipeline_meta(book_id)
        rec = meta["executed"].get(pconf.name)
        if not rec or not isinstance(rec, dict):
            return False

        filepath = base / f"chapter.{pconf.name}.sqlite"
        if not filepath.is_file():
            return False

        # Check config hash
        cfg_hash = self._pc_hash_config(pconf.options)
        if rec.get("config_hash") != cfg_hash:
            return False

        # Compare dependency chain
        if rec.get("depends_on") != completed_stages:
            return False

        return True

    @staticmethod
    def _utc_now_iso() -> str:
        from datetime import UTC, datetime

        return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    def _pc_init_pipeline(
        self: "ProcessClientContext",
        book_id: str,
        processors: list[ProcessorConfig],
    ) -> None:
        meta = self._load_pipeline_meta(book_id)
        meta["pipeline"] = [p.name for p in processors]
        self._save_pipeline_meta(book_id, meta)

    def _pc_record_execution(
        self: "ProcessClientContext",
        book_id: str,
        pconf: ProcessorConfig,
        completed_stages: list[str],
    ) -> None:
        """
        Update pipeline metadata after a processor successfully completes.

        Stores:
          * processed_at - current UTC timestamp
          * depends_on - list of completed stages for this run
          * config_hash - hash of processor options
        """
        # Load existing metadata
        meta = self._load_pipeline_meta(book_id)

        # Create/update the record for this processor
        meta.setdefault("executed", {})
        meta["executed"][pconf.name] = {
            "processed_at": self._utc_now_iso(),
            "depends_on": list(completed_stages),
            "config_hash": self._pc_hash_config(pconf.options),
        }

        # Persist to pipeline.json
        self._save_pipeline_meta(book_id, meta)

    @staticmethod
    def _pc_hash_config(options: dict[str, Any]) -> str:
        """
        Return a short, stable hash fingerprint for a processor's config.

        The config dict is canonicalized (sorted keys, compact separators)
        so that equivalent dicts always map to the same hash value.

        :param options: Arbitrary JSON-serializable config.
        :return: 12-character hex hash prefix.
        """
        import hashlib

        payload = json.dumps(options, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]
