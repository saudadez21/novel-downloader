import gettext
import types

from novel_downloader.infra import i18n


class FakePath:
    """Fake path object to simulate .mo file behavior."""

    def __init__(self, exists: bool):
        self.exists = exists

    def open(self, mode="rb"):
        if not self.exists:
            raise FileNotFoundError("no mo file")
        # minimal valid .mo header (GNUTranslations can parse)
        return FakeFile()


class FakeFile:
    def read(self, *a, **k):
        # Minimal MO header bytes
        return (
            b"\xDE\x12\x04\x95"  # magic
            b"\x00\x00\x00\x00"  # version
            b"\x00\x00\x00\x00"  # nstrings
            b"\x00\x00\x00\x00"  # orig_tab_offset
            b"\x00\x00\x00\x00"  # trans_tab_offset
        )

    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass


def test_get_translation_missing_mo(monkeypatch):
    """If .mo file does not exist → NullTranslations."""

    def fake_files(_package):
        obj = types.SimpleNamespace()
        obj.joinpath = lambda *p: FakePath(exists=False)
        return obj

    monkeypatch.setattr(i18n, "files", fake_files)

    tr = i18n.get_translation("zh_CN")
    assert isinstance(tr, gettext.NullTranslations)


def test_get_translation_valid_mo(monkeypatch):
    """If .mo exists → return GNUTranslations."""

    def fake_files(_package):
        obj = types.SimpleNamespace()
        obj.joinpath = lambda *p: FakePath(exists=True)
        return obj

    monkeypatch.setattr(i18n, "files", fake_files)

    tr = i18n.get_translation("zh_CN")
    assert isinstance(tr, gettext.GNUTranslations)
