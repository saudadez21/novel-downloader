#!/usr/bin/env python3
"""
novel_downloader.infra.persistence.chapter_storage
--------------------------------------------------

Storage module for managing novel chapters in an SQLite database.
"""

__all__ = ["ChapterStorage"]

import contextlib
import json
import sqlite3
import types
from pathlib import Path
from typing import Any, Self

from novel_downloader.schemas import ChapterDict

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS chapters (
  id        TEXT    NOT NULL,
  source_id INTEGER NOT NULL,
  priority  INTEGER NOT NULL DEFAULT 1000,
  title     TEXT    NOT NULL,
  content   TEXT    NOT NULL,
  extra     TEXT,
  PRIMARY KEY (id, source_id)
);

CREATE INDEX IF NOT EXISTS
idx_chapters_id_priority ON chapters(id, priority);
"""


class ChapterStorage:
    """
    Manage storage of chapters in JSON files or an SQLite database.

    Supports storing multiple versions of each chapter from different sources,
    each with a defined priority for selecting the preferred version.
    """

    def __init__(
        self,
        raw_base: str | Path,
        priorities: dict[int, int],
    ) -> None:
        """
        Initialize storage for a specific book.

        :param raw_base: Directory path where the SQLite file will be stored.
        :param priorities: Mapping of source_id to priority value.
                           Lower numbers indicate higher priority.
                           E.X. {0: 10, 1: 100} means source 0 is preferred.
        """
        self._db_path = Path(raw_base) / "chapter_data.sqlite"
        self._conn: sqlite3.Connection | None = None
        self._priorities = priorities
        self._existing_ids: set[tuple[str, int]] = set()  # (chap_id, source_id)

    def connect(self) -> None:
        """
        Open the SQLite connection, enable foreign keys,
        create schema, register initial sources, and cache existing keys.
        """
        if self._conn:
            return
        self._conn = sqlite3.connect(self._db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON;")
        self._conn.executescript(_CREATE_TABLE_SQL)
        self._conn.commit()
        self._load_existing_keys()

    def exists(
        self,
        chap_id: str,
        source_id: int | None = None,
    ) -> bool:
        """
        Check if a chapter exists.

        :param chap_id: Chapter identifier.
        :param source_id: If provided, check existence for that source.
        :return: True if found, else False.
        """
        if source_id is not None:
            return (chap_id, source_id) in self._existing_ids
        return any(key[0] == chap_id for key in self._existing_ids)

    def upsert_chapter(
        self,
        data: ChapterDict,
        source_id: int,
    ) -> None:
        """
        Insert or update a single chapter record.

        :param data: ChapterDict containing id, title, content, extra.
        :param source_id: Integer index of source.
        """
        priority = self._priorities[source_id]
        chap_id = data["id"]
        title = data["title"]
        content = data["content"]
        extra_json = json.dumps(data["extra"])

        self.conn.execute(
            """
            INSERT OR REPLACE INTO chapters
              (id, source_id, priority, title, content, extra)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (chap_id, source_id, priority, title, content, extra_json),
        )
        self._existing_ids.add((chap_id, source_id))
        self.conn.commit()

    def upsert_chapters(
        self,
        data: list[ChapterDict],
        source_id: int,
    ) -> None:
        """
        Insert or update multiple chapters in one batch operation.

        :param data: List of ChapterDicts.
        :param source_id: Integer index of source.
        """
        priority = self._priorities[source_id]
        records = []
        for chapter in data:
            chap_id = chapter["id"]
            title = chapter["title"]
            content = chapter["content"]
            extra_json = json.dumps(chapter["extra"])
            records.append((chap_id, source_id, priority, title, content, extra_json))
            self._existing_ids.add((chap_id, source_id))

        self.conn.executemany(
            """
            INSERT OR REPLACE INTO chapters
              (id, source_id, priority, title, content, extra)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            records,
        )
        self.conn.commit()

    def get_chapter(
        self,
        chap_id: str,
        source_id: int,
    ) -> ChapterDict | None:
        """
        Retrieve a single chapter by id and source.

        :param chap_id: Chapter identifier.
        :param source_id: Integer index of source.
        :return: A ChapterDict if found, else None.
        """
        cur = self.conn.execute(
            """
            SELECT title, content, extra
              FROM chapters
             WHERE id = ? AND source_id = ?
             LIMIT 1
            """,
            (chap_id, source_id),
        )
        row = cur.fetchone()
        if not row:
            return None

        return ChapterDict(
            id=chap_id,
            title=row["title"],
            content=row["content"],
            extra=self._load_dict(row["extra"]),
        )

    def get_chapters(
        self,
        chap_ids: list[str],
        source_id: int,
    ) -> dict[str, ChapterDict | None]:
        """
        Retrieve multiple chapters by their ids for a given source in one query.

        :param chap_ids: List of chapter identifiers.
        :param source_id: Integer index of source.
        :return: A dict mapping chap_id to ChapterDict or None.
        """
        placeholders = ",".join("?" for _ in chap_ids)
        query = f"""
            SELECT id, title, content, extra
              FROM chapters
             WHERE id IN ({placeholders}) AND source_id = ?
        """
        rows = self.conn.execute(query, (*chap_ids, source_id)).fetchall()

        result: dict[str, ChapterDict | None] = {cid: None for cid in chap_ids}
        for row in rows:
            result[row["id"]] = ChapterDict(
                id=row["id"],
                title=row["title"],
                content=row["content"],
                extra=self._load_dict(row["extra"]),
            )
        return result

    def get_best_chapter(
        self,
        chap_id: str,
    ) -> ChapterDict | None:
        """
        Retrieve the chapter with the highest priority (lowest priority number)
        among all sources for the given chap_id.
        """
        cur = self.conn.execute(
            """
            SELECT title, content, extra
              FROM chapters
             WHERE id = ?
             ORDER BY priority ASC
             LIMIT 1
            """,
            (chap_id,),
        )
        row = cur.fetchone()
        if not row:
            return None

        return ChapterDict(
            id=chap_id,
            title=row["title"],
            content=row["content"],
            extra=self._load_dict(row["extra"]),
        )

    def get_best_chapters(
        self,
        chap_ids: list[str],
    ) -> dict[str, ChapterDict | None]:
        """
        Retrieve the best (highest-priority) chapter for each given id
        in a single query using window functions.
        """
        placeholders = ",".join("?" for _ in chap_ids)
        query = f"""
            SELECT chap_id, title, content, extra FROM (
              SELECT id AS chap_id, title, content, extra,
                     ROW_NUMBER() OVER (
                       PARTITION BY id ORDER BY priority ASC
                     ) AS rn
                FROM chapters
               WHERE id IN ({placeholders})
            ) sub
            WHERE rn = 1
        """
        rows = self.conn.execute(query, chap_ids).fetchall()

        result: dict[str, ChapterDict | None] = {chap_id: None for chap_id in chap_ids}
        for row in rows:
            result[row["chap_id"]] = ChapterDict(
                id=row["chap_id"],
                title=row["title"],
                content=row["content"],
                extra=self._load_dict(row["extra"]),
            )
        return result

    def count(self) -> int:
        """
        Count total chapters stored.
        """
        return len(self._existing_ids)

    def close(self) -> None:
        """
        Gracefully close any open resources.
        """
        if self._conn is None:
            return

        with contextlib.suppress(Exception):
            self._conn.close()

        self._conn = None
        self._existing_ids = set()

    @property
    def conn(self) -> sqlite3.Connection:
        """
        Return the active SQLite connection, or raise if not connected.

        :raises RuntimeError: if connect() has not been called.
        """
        if self._conn is None:
            raise RuntimeError(
                "Database connection is not established. Call connect() first."
            )
        return self._conn

    def _load_existing_keys(self) -> None:
        """
        Cache all existing (chapter_id, source_id) pairs for fast upsert.
        """
        cur = self.conn.execute("SELECT id, source_id FROM chapters")
        self._existing_ids = {(row["id"], row["source_id"]) for row in cur.fetchall()}

    @staticmethod
    def _load_dict(data: str) -> dict[str, Any]:
        try:
            return json.loads(data) or {}
        except Exception:
            return {}

    def __enter__(self) -> Self:
        """
        Enter context manager, automatically connecting to the database.
        """
        self.connect()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        tb: types.TracebackType | None,
    ) -> None:
        """
        Exit context manager, closing the database connection.
        """
        self.close()

    def __del__(self) -> None:
        """
        Ensure the database connection is closed upon object deletion.
        """
        self.close()

    def __repr__(self) -> str:
        return (
            f"<ChapterStorage priorities='{self._priorities}' path='{self._db_path}'>"
        )
