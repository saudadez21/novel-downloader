#!/usr/bin/env python3
from __future__ import annotations

import os
import sqlite3
import timeit

DB_FILE = "bench.sqlite"

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS chapters (
  id           TEXT    NOT NULL PRIMARY KEY,
  title        TEXT    NOT NULL,
  content      TEXT    NOT NULL,
  need_refetch BOOLEAN NOT NULL DEFAULT 0,
  extra        TEXT
);
"""


def setup_db() -> sqlite3.Connection:
    """Create a fresh SQLite database with the chapters table."""
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    # conn.execute("PRAGMA journal_mode = WAL;")
    # conn.execute("PRAGMA synchronous = NORMAL;")
    conn.executescript(_CREATE_TABLE_SQL)
    conn.commit()
    return conn


def insert_on_conflict(n_rows: int = 1000) -> None:
    """Insert rows using INSERT ... ON CONFLICT DO UPDATE."""
    conn = setup_db()
    cur = conn.cursor()
    stmt = """
    INSERT INTO chapters (id, title, content, need_refetch, extra)
    VALUES (?, ?, ?, ?, ?)
    ON CONFLICT(id) DO UPDATE SET
        title=excluded.title,
        content=excluded.content,
        need_refetch=excluded.need_refetch,
        extra=excluded.extra
    """
    for i in range(n_rows):
        cur.execute(stmt, (f"id{i}", f"title{i}", f"content{i}", i % 2, None))
    conn.commit()
    conn.close()


def insert_or_replace(n_rows: int = 1000) -> None:
    """Insert rows using INSERT OR REPLACE."""
    conn = setup_db()
    cur = conn.cursor()
    stmt = """
    INSERT OR REPLACE INTO chapters
      (id, title, content, need_refetch, extra)
    VALUES (?, ?, ?, ?, ?)
    """
    for i in range(n_rows):
        cur.execute(stmt, (f"id{i}", f"title{i}", f"content{i}", i % 2, None))
    conn.commit()
    conn.close()


def main() -> None:
    """Benchmark two SQLite UPSERT strategies."""
    n_trials: int = 5
    n_rows: int = 1000

    t_conflict: float = timeit.timeit(
        lambda: insert_on_conflict(n_rows), number=n_trials
    )
    t_replace: float = timeit.timeit(lambda: insert_or_replace(n_rows), number=n_trials)

    print(f"INSERT ... ON CONFLICT DO UPDATE: {t_conflict:.4f} sec for {n_trials} runs")
    print(f"INSERT OR REPLACE               : {t_replace:.4f} sec for {n_trials} runs")


if __name__ == "__main__":
    main()
