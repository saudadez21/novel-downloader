#!/usr/bin/env python3
import contextlib
import json
import random
import sqlite3
import string
import time
from pathlib import Path
from typing import Any, TypedDict, cast

# --- Constants Configuration ---
SCRIPT_DIR = Path(__file__).resolve().parent
NUM_VOLUMES = 12
CHAPTERS_PER_VOLUME = 600
PRIORITIES = {0: 0, 1: 1}  # source_id -> priority
TEST_COUNT = 20  # number of test iterations
DB_FILENAME = "chapter_data.sqlite"
DB_PATH = SCRIPT_DIR / DB_FILENAME

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


# --- Storage Layer (adapted) ---
class ChapterDict(TypedDict, total=True):
    id: str
    title: str
    content: str
    extra: dict[str, Any]


class ChapterStorage:
    def __init__(self, raw_base: str | Path, priorities: dict[int, int]) -> None:
        self._db_path = Path(raw_base) / DB_FILENAME
        self._conn: sqlite3.Connection | None = None
        self._priorities = priorities

    def connect(self) -> None:
        if self._conn:
            return
        self._conn = sqlite3.connect(self._db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON;")
        self._conn.executescript(_CREATE_TABLE_SQL)
        self._conn.commit()

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError(
                "Database connection is not established. Call connect() first."
            )
        return self._conn

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

        self.conn.executemany(
            """
            INSERT OR REPLACE INTO chapters
              (id, source_id, priority, title, content, extra)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            records,
        )
        self.conn.commit()

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

    def close(self) -> None:
        if self._conn is None:
            return
        with contextlib.suppress(Exception):
            self._conn.close()
        self._conn = None

    @staticmethod
    def _load_dict(data: str) -> dict[str, Any]:
        try:
            return cast(dict[str, Any], json.loads(data))
        except Exception:
            return {}


# --- Helper Functions ---
def generate_volumes(num_volumes: int, chapters_per: int) -> list[dict]:
    volumes = []
    for vi in range(num_volumes):
        vol = {"volume_title": f"Volume {vi+1}", "chapters": []}
        for ci in range(chapters_per):
            chap_id = f"{vi+1}-{ci+1}"
            chap_name = f"chap {ci+1}"
            vol["chapters"].append({"chapter_name": chap_name, "chapter_id": chap_id})
        volumes.append(vol)
    return volumes


def populate_db(volumes: list[dict]) -> None:
    # Remove old DB file if it exists, then recreate schema
    if DB_PATH.exists():
        DB_PATH.unlink()

    storage = ChapterStorage(SCRIPT_DIR, PRIORITIES)
    storage.connect()

    # Prepare per-source lists of ChapterDict
    buffer: dict[int, list[ChapterDict]] = {0: [], 1: []}
    for vol in volumes:
        for j, chap in enumerate(vol["chapters"]):
            cd: ChapterDict = {
                "id": chap["chapter_id"],
                "title": chap["chapter_name"],
                "content": "".join(
                    random.choices(string.ascii_letters + string.digits, k=3000)
                ),
                "extra": {},
            }
            # assign to source buckets
            if j < 200:
                buffer[0].append(cd)
            elif j < 400:
                buffer[0].append(cd)
                buffer[1].append(cd)
            else:
                buffer[1].append(cd)

    # Upsert each bucket
    for src_id, ch_list in buffer.items():
        storage.upsert_chapters(ch_list, src_id)

    storage.close()


def test_scenario1(storage: ChapterStorage, volumes: list[dict]) -> None:
    lines: list[str] = []
    for vol in volumes:
        lines.append(vol["volume_title"])
        for chap in vol["chapters"]:
            data = storage.get_best_chapter(chap["chapter_id"])
            if not data:
                continue
            lines.append(data["title"])
            lines.append(data["content"])
    _ = "\n".join(lines)  # simulate writing to a text file


def test_scenario2(storage: ChapterStorage, volumes: list[dict]) -> None:
    lines: list[str] = []
    for vol in volumes:
        lines.append(vol["volume_title"])
        chap_ids = [c["chapter_id"] for c in vol["chapters"]]
        chap_map = storage.get_best_chapters(chap_ids)
        for cid in chap_ids:
            data = chap_map.get(cid)
            if not data:
                continue
            lines.append(data["title"])
            lines.append(data["content"])
    _ = "\n".join(lines)


# --- Main Flow ---
def main():
    volumes = generate_volumes(NUM_VOLUMES, CHAPTERS_PER_VOLUME)

    print("Generating and upserting test data...")
    populate_db(volumes)

    print("Starting performance tests:")
    times1, times2 = [], []

    for i in range(TEST_COUNT):
        # Scenario 1: single-chapter queries
        t0 = time.perf_counter()
        storage = ChapterStorage(SCRIPT_DIR, PRIORITIES)
        storage.connect()
        test_scenario1(storage, volumes)
        storage.close()
        t1 = time.perf_counter()
        times1.append(t1 - t0)

        # Scenario 2: batched-chapter queries
        t0 = time.perf_counter()
        storage = ChapterStorage(SCRIPT_DIR, PRIORITIES)
        storage.connect()
        test_scenario2(storage, volumes)
        storage.close()
        t1 = time.perf_counter()
        times2.append(t1 - t0)

        print(
            f"  Iteration {i+1}/{TEST_COUNT} - "
            f"Scenario 1: {times1[-1]:.4f}s, "
            f"Scenario 2: {times2[-1]:.4f}s"
        )

    avg1 = sum(times1) / TEST_COUNT
    avg2 = sum(times2) / TEST_COUNT
    print("\nTests completed:")
    print(f"  Average time Scenario 1: {avg1:.4f} seconds")
    print(f"  Average time Scenario 2: {avg2:.4f} seconds")


if __name__ == "__main__":
    main()
