#!/usr/bin/env python3
"""
novel_downloader.infra.persistence.chapter_storage
--------------------------------------------------

Storage module for managing novel chapters in an SQLite database.
"""

from __future__ import annotations

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
  id           TEXT    NOT NULL PRIMARY KEY,
  title        TEXT    NOT NULL,
  content      TEXT    NOT NULL,
  need_refetch BOOLEAN NOT NULL DEFAULT 0,
  extra        TEXT
);
"""


class ChapterStorage:
    """
    Manage storage of chapters in an SQLite database.
    """

    def __init__(self, base_dir: str | Path, filename: str) -> None:
        """
        Initialize storage for a specific book.

        :param base_dir: Directory path where the SQLite file will be stored.
        :param filename: SQLite filename.
        """
        self._db_path = Path(base_dir) / filename
        self._conn: sqlite3.Connection | None = None
        # Cache: chapter id -> need_refetch flag
        self._refetch_flags: dict[str, bool] = {}

    def connect(self) -> None:
        """
        Open the SQLite connection, initialize schema, and warm the cache.
        """
        if self._conn:
            return

        self._conn = sqlite3.connect(self._db_path)
        self._conn.row_factory = sqlite3.Row
        # self._conn.execute("PRAGMA foreign_keys = ON;")
        # self._conn.execute("PRAGMA journal_mode = WAL;")
        # self._conn.execute("PRAGMA synchronous = NORMAL;")
        self._conn.executescript(_CREATE_TABLE_SQL)
        self._conn.commit()
        self._load_existing_keys()

    def exists(self, chap_id: str) -> bool:
        """
        Return True if the chapter id is known (present in cache/DB).

        :param chap_id: Chapter identifier.
        """
        return chap_id in self._refetch_flags

    def need_refetch(self, chap_id: str) -> bool:
        """
        Return True if the chapter is known to require refetch; if the id is
        unknown, default to True (refetch) to be conservative.

        :param chap_id: Chapter identifier.
        """
        return self._refetch_flags.get(chap_id, True)

    def existing_ids(self) -> set[str]:
        """
        All chapter IDs currently present in this store.
        """
        return set(self._refetch_flags.keys())

    def clean_ids(self) -> set[str]:
        """
        Chapter IDs present in this store that DO NOT need refetch.
        """
        return {cid for cid, need in self._refetch_flags.items() if need is False}

    def dirty_ids(self) -> set[str]:
        """
        Chapter IDs present in this store that DO need refetch.
        """
        return {cid for cid, need in self._refetch_flags.items() if need is True}

    def upsert_chapter(self, data: ChapterDict, need_refetch: bool = False) -> None:
        """
        Insert or update a single chapter.

        :param data: ChapterDict containing `id`, `title`, `content`, `extra`.
        :param need_refetch: Whether this chapter should be marked to refetch.
        """
        chap_id = data["id"]
        title = data["title"]
        content = data["content"]
        extra_json = json.dumps(data["extra"], ensure_ascii=False)

        self.conn.execute(
            """
            INSERT INTO chapters (id, title, content, need_refetch, extra)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title=excluded.title,
                content=excluded.content,
                need_refetch=excluded.need_refetch,
                extra=excluded.extra
            """,
            (chap_id, title, content, int(need_refetch), extra_json),
        )
        self.conn.commit()
        self._refetch_flags[chap_id] = need_refetch

    def upsert_chapters(
        self, data: list[ChapterDict], need_refetch: bool = False
    ) -> None:
        """
        Insert or update multiple chapters in a single transaction.

        :param data: List of ChapterDicts.
        :param need_refetch: Whether these chapters should be marked to refetch.
        """
        if not data:
            return

        records = []
        for chapter in data:
            chap_id = chapter["id"]
            title = chapter["title"]
            content = chapter["content"]
            extra_json = json.dumps(chapter["extra"], ensure_ascii=False)
            records.append((chap_id, title, content, int(need_refetch), extra_json))
            self._refetch_flags[chap_id] = need_refetch

        self.conn.executemany(
            """
            INSERT INTO chapters (id, title, content, need_refetch, extra)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title=excluded.title,
                content=excluded.content,
                need_refetch=excluded.need_refetch,
                extra=excluded.extra
            """,
            records,
        )
        self.conn.commit()

    def get_chapter(self, chap_id: str) -> ChapterDict | None:
        """
        Retrieve a single chapter by id.

        :param chap_id: Chapter identifier.
        :return: A ChapterDict if found, else None.
        """
        cur = self.conn.execute(
            "SELECT id, title, content, extra FROM chapters WHERE id = ?",
            (chap_id,),
        )
        row = cur.fetchone()
        if not row:
            return None

        return ChapterDict(
            id=row["id"],
            title=row["title"],
            content=row["content"],
            extra=self._load_dict(row["extra"]),
        )

    def get_chapters(self, chap_ids: list[str]) -> dict[str, ChapterDict | None]:
        """
        Retrieve multiple chapters by their ids in one query.

        :param chap_ids: List of chapter identifiers.
        :return: A dict mapping chap_id to ChapterDict (or None if not found).
        """
        if not chap_ids:
            return {}

        placeholders = ",".join("?" for _ in chap_ids)
        query = f"""
            SELECT id, title, content, extra
              FROM chapters
             WHERE id IN ({placeholders})
        """
        rows = self.conn.execute(query, tuple(chap_ids)).fetchall()

        result: dict[str, ChapterDict | None] = {cid: None for cid in chap_ids}
        for row in rows:
            result[row["id"]] = ChapterDict(
                id=row["id"],
                title=row["title"],
                content=row["content"],
                extra=self._load_dict(row["extra"]),
            )
        return result

    def close(self) -> None:
        """
        Close the database connection and clear in-memory caches.
        """
        if self._conn is None:
            return

        with contextlib.suppress(Exception):
            self._conn.close()

        self._conn = None
        self._refetch_flags.clear()

    @property
    def conn(self) -> sqlite3.Connection:
        """
        Return the active SQLite connection.

        :raises RuntimeError: if connect() has not been called.
        """
        if self._conn is None:
            raise RuntimeError(
                "Database connection is not established. Call connect() first."
            )
        return self._conn

    def _load_existing_keys(self) -> None:
        """
        Populate the in-memory cache from the database.
        """
        cur = self.conn.execute("SELECT id, need_refetch FROM chapters")
        self._refetch_flags = {
            row["id"]: bool(row["need_refetch"]) for row in cur.fetchall()
        }

    @staticmethod
    def _load_dict(data: str) -> dict[str, Any]:
        """
        Parse a JSON string into a dict, returning {} on error/empty.
        """
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

    def __repr__(self) -> str:
        return f"<ChapterStorage path='{self._db_path}'>"
