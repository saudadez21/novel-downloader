import sqlite3
from collections.abc import Generator
from pathlib import Path

import pytest
from novel_downloader.infra.persistence.chapter_storage import ChapterStorage
from novel_downloader.schemas import ChapterDict


@pytest.fixture()
def tmp_storage(tmp_path: Path) -> Generator[ChapterStorage, None, None]:
    """Create a temporary ChapterStorage connected to an SQLite file."""
    store = ChapterStorage(tmp_path, "chapters.sqlite")
    store.connect()
    yield store
    store.close()
    assert not store._refetch_flags  # cache cleared after close


def _make_chapter(idx: int) -> ChapterDict:
    return ChapterDict(
        id=f"chap{idx}",
        title=f"Title {idx}",
        content=f"Content {idx}",
        extra={"i": idx},
    )


# ---------------------------------------------------------------------
# Basic lifecycle and connection handling
# ---------------------------------------------------------------------


def test_connect_and_close(tmp_path: Path):
    store = ChapterStorage(tmp_path, "t.db")
    assert not store._conn
    store.connect()
    assert isinstance(store.conn, sqlite3.Connection)
    assert store._db_path.exists()
    store.close()
    with pytest.raises(RuntimeError):
        _ = store.conn  # accessing after close should fail


def test_context_manager(tmp_path: Path):
    """Using context manager should auto-connect and auto-close."""
    with ChapterStorage(tmp_path, "book.db") as store:
        assert store._conn is not None
        store.upsert_chapter(_make_chapter(1))
    assert store._conn is None  # closed on exit


# ---------------------------------------------------------------------
# Insert / update
# ---------------------------------------------------------------------


def test_upsert_and_get_single(tmp_storage: ChapterStorage):
    ch = _make_chapter(1)
    tmp_storage.upsert_chapter(ch)
    got = tmp_storage.get_chapter(ch["id"])
    assert got is not None
    assert got["title"] == ch["title"]
    assert got["extra"] == ch["extra"]

    # update content and mark dirty
    ch["content"] = "new content"
    tmp_storage.upsert_chapter(ch, need_refetch=True)
    got2 = tmp_storage.get_chapter(ch["id"])
    assert got2 is not None
    assert got2["content"] == "new content"
    assert tmp_storage.need_refetch(ch["id"]) is True


def test_upsert_many_and_get_chapters(tmp_storage: ChapterStorage):
    chapters = [_make_chapter(i) for i in range(3)]
    tmp_storage.upsert_chapters(chapters)
    ids = [c["id"] for c in chapters]
    results = tmp_storage.get_chapters(ids)
    assert set(results) == set(ids)
    for cid in ids:
        item = results[cid]
        assert item is not None
        assert item["id"] == cid
        assert isinstance(item["content"], str)
    assert tmp_storage.exists("chap1") is True
    assert tmp_storage.need_refetch("chap0") is False


def test_upsert_chapters_empty_list(tmp_storage: ChapterStorage):
    """Calling upsert_chapters([]) should be a no-op."""
    tmp_storage.upsert_chapters([])
    assert tmp_storage.existing_ids() == set()


# ---------------------------------------------------------------------
# Caching / flag tracking
# ---------------------------------------------------------------------


def test_dirty_and_clean_ids(tmp_storage: ChapterStorage):
    clean = _make_chapter(1)
    dirty = _make_chapter(2)
    tmp_storage.upsert_chapter(clean, need_refetch=False)
    tmp_storage.upsert_chapter(dirty, need_refetch=True)

    assert tmp_storage.clean_ids() == {clean["id"]}
    assert tmp_storage.dirty_ids() == {dirty["id"]}
    assert tmp_storage.existing_ids() == {clean["id"], dirty["id"]}


# ---------------------------------------------------------------------
# Loading from DB
# ---------------------------------------------------------------------


def test_load_existing_keys(tmp_path: Path):
    store = ChapterStorage(tmp_path, "chap.db")
    store.connect()
    store.upsert_chapter(_make_chapter(1))
    # reopen to trigger _load_existing_keys
    store2 = ChapterStorage(tmp_path, "chap.db")
    store2.connect()
    assert store2.exists("chap1")
    assert store2.need_refetch("chap1") is False


# ---------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------


@pytest.mark.parametrize(
    "data,expected",
    [
        ('{"a":1}', {"a": 1}),
        ("", {}),
        ("not json", {}),
        ("null", {}),
    ],
)
def test_load_dict_various_inputs(data, expected):
    assert ChapterStorage._load_dict(data) == expected


def test_repr(tmp_path: Path):
    s = ChapterStorage(tmp_path, "x.db")
    assert str(tmp_path) in repr(s)
