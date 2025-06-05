#!/usr/bin/env python3
"""
novel_downloader.utils.chapter_storage
--------------------------------------

Storage module for managing novel chapters in
either JSON file form or an SQLite database.
"""

import contextlib
import json
import sqlite3
import types
from pathlib import Path
from typing import Any, Self, cast

from novel_downloader.models import (
    ChapterDict,
    SaveMode,
    StorageBackend,
)

from .file_utils import save_as_json

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS "{table}" (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    extra TEXT NOT NULL
)
"""


class ChapterStorage:
    """
    Manage storage of chapters in JSON files or an SQLite database.

    :param raw_base: Base directory or file path for storage.
    :param namespace: Novel identifier (subfolder name or DB/table basename).
    :param backend_type: "json" (default) or "sqlite".
    """

    def __init__(
        self,
        raw_base: str | Path,
        namespace: str,
        backend_type: StorageBackend = "json",
        *,
        batch_size: int = 1,
    ) -> None:
        self.raw_base = Path(raw_base)
        self.namespace = namespace
        self.backend = backend_type
        self._batch_size = batch_size
        self._pending = 0
        self._conn: sqlite3.Connection | None = None
        self._existing_ids: set[str] = set()

        if self.backend == "json":
            self._init_json()
        else:
            self._init_sql()

    def _init_json(self) -> None:
        """Prepare directory for JSON files."""
        self._json_dir = self.raw_base / self.namespace
        self._json_dir.mkdir(parents=True, exist_ok=True)
        self._existing_ids = {p.stem for p in self._json_dir.glob("*.json")}

    def _init_sql(self) -> None:
        """Prepare SQLite connection and ensure table exists."""
        self._db_path = self.raw_base / f"{self.namespace}.sqlite"
        self._conn = sqlite3.connect(self._db_path)
        stmt = _CREATE_TABLE_SQL.format(table=self.namespace)
        self._conn.execute(stmt)
        self._conn.commit()

        cur = self._conn.execute(f'SELECT id FROM "{self.namespace}"')
        self._existing_ids = {row[0] for row in cur.fetchall()}

    def _json_path(self, chap_id: str) -> Path:
        """Return Path for JSON file of given chapter ID."""
        return self._json_dir / f"{chap_id}.json"

    def exists(self, chap_id: str) -> bool:
        """
        Check if a chapter exists.

        :param chap_id: Chapter identifier.
        :return: True if found, else False.
        """
        return chap_id in self._existing_ids

    def _load_json(self, chap_id: str) -> ChapterDict:
        raw = self._json_path(chap_id).read_text(encoding="utf-8")
        return cast(ChapterDict, json.loads(raw))

    def _load_sql(self, chap_id: str) -> ChapterDict:
        if self._conn is None:
            raise RuntimeError("ChapterStorage is closed")
        cur = self._conn.execute(
            f'SELECT id, title, content, extra FROM "{self.namespace}" WHERE id = ?',
            (chap_id,),
        )
        row = cur.fetchone()
        return {
            "id": row[0],
            "title": row[1],
            "content": row[2],
            "extra": json.loads(row[3]),
        }

    def get(self, chap_id: str) -> ChapterDict | dict[str, Any]:
        """
        Retrieve chapter by ID.

        :param chap_id: Chapter identifier.
        :return: ChapterDict if exists, else empty dict.
        """
        if not self.exists(chap_id):
            return {}
        return (
            self._load_json(chap_id)
            if self.backend == "json"
            else self._load_sql(chap_id)
        )

    def _save_json(self, data: ChapterDict, on_exist: SaveMode) -> None:
        path = self._json_path(data["id"])
        save_as_json(data, path, on_exist=on_exist)
        self._existing_ids.add(data["id"])

    def _save_sql(self, data: ChapterDict, on_exist: SaveMode) -> None:
        if self._conn is None:
            raise RuntimeError("ChapterStorage is closed")
        sql = (
            f'INSERT OR REPLACE INTO "{self.namespace}" '
            "(id, title, content, extra) VALUES (?, ?, ?, ?)"
            if on_exist == "overwrite"
            else f'INSERT OR IGNORE INTO "{self.namespace}" '
            "(id, title, content, extra) VALUES (?, ?, ?, ?)"
        )
        self._conn.execute(
            sql,
            (
                data["id"],
                data["title"],
                data["content"],
                json.dumps(data["extra"], ensure_ascii=False),
            ),
        )
        self._existing_ids.add(data["id"])
        if self._batch_size == 1:
            self._conn.commit()
        else:
            self._pending += 1
            if self._pending >= self._batch_size:
                self._conn.commit()
                self._pending = 0

    def _save_many_sql(
        self,
        datas: list[ChapterDict],
        on_exist: SaveMode = "overwrite",
    ) -> None:
        """
        Bulk-insert into SQLite using executemany + one commit.

        :param datas: List of ChapterDict to store.
        :param on_exist: "overwrite" to REPLACE, "skip" to IGNORE on conflicts.
        """
        if on_exist not in ("overwrite", "skip"):
            raise ValueError(f"invalid on_exist mode: {on_exist!r}")
        if self._conn is None:
            raise RuntimeError("ChapterStorage is closed")

        sql = (
            f'INSERT OR REPLACE INTO "{self.namespace}" '
            "(id, title, content, extra) VALUES (?, ?, ?, ?)"
            if on_exist == "overwrite"
            else f'INSERT OR IGNORE INTO "{self.namespace}" '
            "(id, title, content, extra) VALUES (?, ?, ?, ?)"
        )

        params = [
            (
                data["id"],
                data["title"],
                data["content"],
                json.dumps(data["extra"], ensure_ascii=False),
            )
            for data in datas
        ]

        with self._conn:
            self._conn.executemany(sql, params)

        self._existing_ids.update(data["id"] for data in datas)

    def save(
        self,
        data: ChapterDict,
        on_exist: SaveMode = "overwrite",
    ) -> None:
        """
        Save a chapter record.

        :param data: ChapterDict to store.
        :param on_exist: What to do if chap_id already exists
        """
        if on_exist not in ("overwrite", "skip"):
            raise ValueError(f"invalid on_exist mode: {on_exist!r}")

        if self.backend == "json":
            self._save_json(data, on_exist)
        else:
            self._save_sql(data, on_exist)

    def save_many(
        self,
        datas: list[ChapterDict],
        on_exist: SaveMode = "overwrite",
    ) -> None:
        """
        Save multiple chapter records in one shot.

        :param datas: List of ChapterDict to store.
        :param on_exist: What to do if chap_id already exists.
        """
        if on_exist not in ("overwrite", "skip"):
            raise ValueError(f"invalid on_exist mode: {on_exist!r}")

        if self.backend == "json":
            for data in datas:
                self._save_json(data, on_exist)
        else:
            self._save_many_sql(datas, on_exist)

    def list_ids(self) -> list[str]:
        """
        List all stored chapter IDs.
        """
        if self.backend == "json":
            return [p.stem for p in self._json_dir.glob("*.json") if p.is_file()]

        if self._conn is None:
            raise RuntimeError("ChapterStorage is closed")
        cur = self._conn.execute(f'SELECT id FROM "{self.namespace}"')
        return [row[0] for row in cur.fetchall()]

    def delete(self, chap_id: str) -> bool:
        """
        Delete a chapter by ID.

        :param chap_id: Chapter identifier.
        :return: True if deleted, False if not found.
        """
        if not self.exists(chap_id):
            return False
        if self.backend == "json":
            self._json_path(chap_id).unlink()
            return True

        if self._conn is None:
            raise RuntimeError("ChapterStorage is closed")
        cur = self._conn.execute(
            f'DELETE FROM "{self.namespace}" WHERE id = ?', (chap_id,)
        )
        self._conn.commit()
        return cur.rowcount > 0

    def count(self) -> int:
        """
        Count total chapters stored.
        """
        if self.backend == "json":
            return len(self.list_ids())

        if self._conn is None:
            raise RuntimeError("ChapterStorage is closed")
        cur = self._conn.execute(f'SELECT COUNT(1) FROM "{self.namespace}"')
        return int(cur.fetchone()[0])

    def flush(self) -> None:
        """
        Write out any leftover rows (< batch_size) at the end.
        """
        if self._conn is not None and self._pending > 0:
            self._conn.commit()
            self._pending = 0

    def close(self) -> None:
        """
        Gracefully close any open resources.
        """
        if self.backend != "sqlite" or self._conn is None:
            return

        with contextlib.suppress(Exception):
            self.flush()

        with contextlib.suppress(Exception):
            self._conn.close()

        self._conn = None

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        tb: types.TracebackType | None,
    ) -> None:
        self.close()

    def __del__(self) -> None:
        self.close()

    def __repr__(self) -> str:
        return (
            f"<ChapterStorage ns='{self.namespace}' "
            f"backend='{self.backend}' "
            f"path='{self.raw_base}'>"
        )
