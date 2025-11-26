import pytest

from novel_downloader.libs.filesystem.file import write_file


def test_write_file_text(tmp_path):
    """Write text content normally."""
    p = tmp_path / "test.txt"
    out = write_file("hello", p)
    assert out == p
    assert p.read_text("utf-8") == "hello"


def test_write_file_bytes(tmp_path):
    """Write binary content normally."""
    p = tmp_path / "bin.dat"
    out = write_file(b"\x01\x02", p)
    assert out == p
    assert p.read_bytes() == b"\x01\x02"


def test_write_file_skip_if_exists(tmp_path):
    """If file exists and on_exist=skip, do not overwrite."""
    p = tmp_path / "skip.txt"
    p.write_text("old")

    out = write_file("new", p, on_exist="skip")
    assert out == p
    assert p.read_text("utf-8") == "old"  # must not change


def test_write_file_overwrite(tmp_path):
    """overwrite path forces replacement."""
    p = tmp_path / "ow.txt"
    p.write_text("old")

    out = write_file("new", p, on_exist="overwrite")
    assert out == p
    assert p.read_text("utf-8") == "new"


def test_write_file_sanitize_filename(tmp_path, monkeypatch):
    """Filename must be sanitized before writing."""
    # Fake sanitize_filename to observe behavior
    monkeypatch.setattr(
        "novel_downloader.libs.filesystem.file.sanitize_filename",
        lambda name: name.replace("?", "_safe_"),
    )

    p = tmp_path / "bad?.txt"
    out = write_file("x", p)

    # The output path must use sanitized name
    assert out.name == "bad_safe_.txt"
    assert out.exists()
    assert out.read_text("utf-8") == "x"


def test_write_file_atomic(tmp_path):
    """
    Ensure write_file uses a temp file then replaces.
    We detect this by checking:
        - dest file contains new content
        - no leftover temporary files remain
    """
    p = tmp_path / "atomic.txt"
    out = write_file("atomic", p)

    assert out.exists()
    assert out.read_text("utf-8") == "atomic"

    # No stray temp files
    leftovers = [x for x in tmp_path.iterdir() if x.name != "atomic.txt"]
    assert leftovers == []


def test_write_file_cleanup_on_error(tmp_path, monkeypatch):
    """If writing fails, temporary file must be deleted."""
    tmp_created = []

    class FakeTmp:
        def __init__(self, *a, **k):
            real = tmp_path / "fake_temp.tmp"
            real.write_text("temp")
            tmp_created.append(real)
            self.name = str(real)

        def write(self, *_):
            raise OSError("write failed")  # FAIL on first write

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(
        "novel_downloader.libs.filesystem.file.tempfile.NamedTemporaryFile",
        FakeTmp,
    )

    p = tmp_path / "err.txt"

    with pytest.raises(IOError):
        write_file("xxx", p)

    # ensure temporary file is cleaned up
    assert not tmp_created[0].exists()
    assert not p.exists()
