#!/usr/bin/env python3
import argparse
import contextlib
import json
import random
import shutil
import sqlite3
import string
import time
from pathlib import Path
from typing import Any, TypedDict, cast

# --- Constants Configuration ---
SCRIPT_DIR = Path(__file__).resolve().parent
CHAPTER_DATA_DIR = SCRIPT_DIR / "chapter_data"
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

        result: dict[str, ChapterDict | None] = dict.fromkeys(chap_ids)
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
def load_best_chapter_json(data_dir: Path, chap_id: str) -> ChapterDict | None:
    """
    Look in each source subdirectory for chap_id.json, in order of priority,
    and return the first found ChapterDict.
    """
    # sort source IDs by their priority (lower number first)
    for src_id in sorted(PRIORITIES, key=lambda k: PRIORITIES[k]):
        path = data_dir / str(src_id) / f"{chap_id}.json"
        if path.exists():
            with open(path) as f:
                raw = json.load(f)
            return ChapterDict(
                id=raw["id"],
                title=raw["title"],
                content=raw["content"],
                extra=raw.get("extra", {}),
            )
    return None


def generate_volumes(num_volumes: int, chapters_per: int) -> list[dict]:
    volumes = []
    for vi in range(num_volumes):
        vol = {"volume_title": f"Volume {vi + 1}", "chapters": []}
        for ci in range(chapters_per):
            chap_id = f"{vi + 1}-{ci + 1}"
            chap_name = f"chap {ci + 1}"
            vol["chapters"].append({"chapter_name": chap_name, "chapter_id": chap_id})
        volumes.append(vol)
    return volumes


def populate_db(volumes: list[dict]) -> None:
    # Remove old DB file if it exists, then recreate schema
    if DB_PATH.exists():
        DB_PATH.unlink()
    if CHAPTER_DATA_DIR.exists():
        shutil.rmtree(CHAPTER_DATA_DIR)
    CHAPTER_DATA_DIR.mkdir(parents=True)
    for src_id in PRIORITIES:
        (CHAPTER_DATA_DIR / str(src_id)).mkdir()

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
        src_dir = CHAPTER_DATA_DIR / str(src_id)
        for cd in ch_list:
            json_path = src_dir / f"{cd['id']}.json"
            with open(json_path, "w") as f:
                json.dump(cd, f)
        storage.upsert_chapters(ch_list, src_id)

    storage.close()


def test_scenario0(data_dir: Path, volumes: list[dict]) -> None:
    lines: list[str] = []
    for vol in volumes:
        lines.append(vol["volume_title"])
        for chap in vol["chapters"]:
            cd = load_best_chapter_json(data_dir, chap["chapter_id"])
            if not cd:
                continue
            lines.append(cd["title"])
            lines.append(cd["content"])
    _ = "\n".join(lines)  # simulate writing to a text file


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
    _ = "\n".join(lines)


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


def clean_data() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
    if CHAPTER_DATA_DIR.exists():
        shutil.rmtree(CHAPTER_DATA_DIR)


def run_tests() -> None:
    volumes = generate_volumes(NUM_VOLUMES, CHAPTERS_PER_VOLUME)

    print("Generating and upserting test data...")
    populate_db(volumes)

    print("Starting performance tests:")
    times0, times1, times2 = [], [], []

    for i in range(TEST_COUNT):
        # Scenario 0: JSON-by-chapter with best-source helper
        t0 = time.perf_counter()
        test_scenario0(CHAPTER_DATA_DIR, volumes)
        t1 = time.perf_counter()
        times0.append(t1 - t0)

        # Scenario 1: single-chapter DB queries
        t0 = time.perf_counter()
        storage = ChapterStorage(SCRIPT_DIR, PRIORITIES)
        storage.connect()
        test_scenario1(storage, volumes)
        storage.close()
        t1 = time.perf_counter()
        times1.append(t1 - t0)

        # Scenario 2: batched-chapter DB queries
        t0 = time.perf_counter()
        storage = ChapterStorage(SCRIPT_DIR, PRIORITIES)
        storage.connect()
        test_scenario2(storage, volumes)
        storage.close()
        t1 = time.perf_counter()
        times2.append(t1 - t0)

        print(
            f"  Iteration {i + 1}/{TEST_COUNT} - "
            f"Scenario 0: {times0[-1]:.4f}s, "
            f"Scenario 1: {times1[-1]:.4f}s, "
            f"Scenario 2: {times2[-1]:.4f}s"
        )

    print("\nTests completed:")
    print(f"  Average time Scenario 0: {sum(times0) / TEST_COUNT:.4f} seconds")
    print(f"  Average time Scenario 1: {sum(times1) / TEST_COUNT:.4f} seconds")
    print(f"  Average time Scenario 2: {sum(times2) / TEST_COUNT:.4f} seconds")


# --- Main Flow ---
def main():
    parser = argparse.ArgumentParser(description="Benchmark chapter-loading scenarios")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run the benchmark tests",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean out existing database and JSON data before running",
    )
    args = parser.parse_args()

    if args.clean:
        clean_data()
        print("Cleaned existing DB and JSON data.")

    if args.test or (not args.clean and not args.test):
        run_tests()


if __name__ == "__main__":
    main()
