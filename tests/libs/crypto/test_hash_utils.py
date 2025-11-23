import hashlib

from novel_downloader.libs.crypto.hash_utils import (
    hash_bytes,
    hash_file,
)


def test_hash_bytes_basic():
    data = b"hello world"
    expected = hashlib.sha256(data).hexdigest()
    assert hash_bytes(data) == expected


def test_hash_bytes_empty():
    data = b""
    expected = hashlib.sha256(data).hexdigest()
    assert hash_bytes(data) == expected


def test_hash_file_basic(tmp_path):
    fp = tmp_path / "test.bin"
    fp.write_bytes(b"hello world")

    expected = hashlib.sha256(b"hello world").hexdigest()
    assert hash_file(fp) == expected


def test_hash_file_empty(tmp_path):
    fp = tmp_path / "empty.bin"
    fp.write_bytes(b"")

    expected = hashlib.sha256(b"").hexdigest()
    assert hash_file(fp) == expected


def test_hash_file_chunking(tmp_path):
    """
    Ensure hash_file works when data spans multiple chunks.
    """

    fp = tmp_path / "big.bin"
    data = b"A" * 100_000  # definitely > 8192 chunk
    fp.write_bytes(data)

    expected = hashlib.sha256(data).hexdigest()

    # Deliberately set a small chunk_size to force looping
    assert hash_file(fp, chunk_size=1024) == expected
