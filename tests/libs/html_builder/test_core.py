import pytest

from novel_downloader.libs.html_builder.core import HtmlBuilder
from novel_downloader.libs.html_builder.models import (
    HtmlChapter,
    HtmlVolume,
)


# ---------------------------------------------------------------------
# Helpers - place fake css/js templates via monkeypatch
# ---------------------------------------------------------------------
@pytest.fixture
def fake_templates(tmp_path, monkeypatch):
    css_index = tmp_path / "index.css"
    css_index.write_text("/*index*/")
    css_chapter = tmp_path / "chapter.css"
    css_chapter.write_text("/*chapter*/")
    js_main = tmp_path / "main.js"
    js_main.write_text("//js")

    # patch paths in html_builder.core
    monkeypatch.setattr(
        "novel_downloader.libs.html_builder.core.HTML_CSS_INDEX_PATH",
        css_index,
    )
    monkeypatch.setattr(
        "novel_downloader.libs.html_builder.core.HTML_CSS_CHAPTER_PATH",
        css_chapter,
    )
    monkeypatch.setattr(
        "novel_downloader.libs.html_builder.core.HTML_JS_MAIN_PATH",
        js_main,
    )
    return tmp_path


# ---------------------------------------------------------------------
# Basic initialization
# ---------------------------------------------------------------------
def test_builder_initial_state():
    b = HtmlBuilder("Title", author="A", description="D")
    assert b.title == "Title"
    assert b.lang == "zh-Hans"
    assert b.images == []
    assert b.fonts == []
    assert b._chapters == []


# ---------------------------------------------------------------------
# add_image - valid file + dedupe
# ---------------------------------------------------------------------
def test_add_image(tmp_path):
    p = tmp_path / "a.jpg"
    p.write_bytes(b"img")

    b = HtmlBuilder("X")
    name = b.add_image(p)
    assert name.startswith("img_0.")
    assert len(b.images) == 1

    # dedupe
    name2 = b.add_image(p)
    assert name2 == name
    assert len(b.images) == 1


# ---------------------------------------------------------------------
# add_image_bytes + dedupe
# ---------------------------------------------------------------------
def test_add_image_bytes():
    b = HtmlBuilder("X")
    name = b.add_image_bytes(b"imgdata")
    assert name.startswith("img_0.")

    # dedupe
    name2 = b.add_image_bytes(b"imgdata")
    assert name == name2


# ---------------------------------------------------------------------
# add_font (file) + dedupe
# ---------------------------------------------------------------------
def test_add_font(tmp_path):
    f = tmp_path / "font.ttf"
    f.write_bytes(b"fontdata")

    b = HtmlBuilder("Book")
    font = b.add_font(f, family="Fam", selectors=(".x",))
    assert font
    assert font.family == "Fam"
    assert font.selectors == (".x",)

    # dedupe
    font2 = b.add_font(f)
    assert font2 is font


# ---------------------------------------------------------------------
# add_font_bytes + dedupe
# ---------------------------------------------------------------------
def test_add_font_bytes():
    data = b"fontraw"
    b = HtmlBuilder("Book")
    f1 = b.add_font_bytes(data)
    f2 = b.add_font_bytes(data)
    assert f1 is f2


# ---------------------------------------------------------------------
# add_chapter -> index entry & chapter list
# ---------------------------------------------------------------------
def test_add_chapter_to_index():
    b = HtmlBuilder("Book")
    chap = HtmlChapter(filename="c.html", title="T", content="body")
    b.add_chapter(chap)

    assert b._chapters == [chap]
    assert len(b._index.toc_blocks) == 1
    assert "c.html" in b._index.toc_blocks[0]


# ---------------------------------------------------------------------
# add_volume -> index + chapters flattened
# ---------------------------------------------------------------------
def test_add_volume_to_index():
    b = HtmlBuilder("Book")
    ch1 = HtmlChapter(filename="1.html", title="T1", content="C1")
    v = HtmlVolume(title="Vol", intro="I", chapters=[ch1])

    b.add_volume(v)
    assert b._chapters == [ch1]
    assert "Vol" in b._index.toc_blocks[0]
    assert "1.html" in b._index.toc_blocks[0]


# ---------------------------------------------------------------------
# cover image written correctly
# ---------------------------------------------------------------------
def test_cover_written(tmp_path, fake_templates):
    cover = b"fakeimg"
    b = HtmlBuilder("Book", cover=cover)

    out = b.export(tmp_path)
    media = out / "media"
    assert media.exists()

    # cover.xxx exists
    cover_files = list(media.glob("cover.*"))
    assert len(cover_files) == 1
    assert cover_files[0].read_bytes() == cover


# ---------------------------------------------------------------------
# export folder structure + index + chapters
# ---------------------------------------------------------------------
def test_export_builds_full_structure(tmp_path, fake_templates):
    b = HtmlBuilder("Book", cover=b"img")

    ch1 = HtmlChapter(filename="1.html", title="C1", content="AAA")
    ch2 = HtmlChapter(filename="2.html", title="C2", content="BBB")
    b.add_chapter(ch1)
    b.add_chapter(ch2)

    out = b.export(tmp_path)
    assert out.exists()

    # check basic dirs
    assert (out / "css").exists()
    assert (out / "js").exists()
    assert (out / "chapters").exists()

    # index.html exists
    assert (out / "index.html").exists()

    # chapters exist + prev/next links present
    c1 = (out / "chapters" / "1.html").read_text("utf-8")
    c2 = (out / "chapters" / "2.html").read_text("utf-8")

    assert "next_link" not in c1  # links merged in template; test content instead
    assert "2.html" in c1  # next chapter
    assert "1.html" in c2  # prev chapter


# ---------------------------------------------------------------------
# images written on export
# ---------------------------------------------------------------------
def test_export_writes_images(tmp_path, fake_templates):
    img_path = tmp_path / "pic.png"
    img_path.write_bytes(b"rawimg")

    b = HtmlBuilder("Book")
    name = b.add_image(img_path)

    out = b.export(tmp_path)
    media = out / "media"

    assert (media / name).read_bytes() == b"rawimg"


# ---------------------------------------------------------------------
# fonts written on export
# ---------------------------------------------------------------------
def test_export_writes_fonts(tmp_path, fake_templates):
    font_path = tmp_path / "font.ttf"
    font_path.write_bytes(b"fontbin")

    b = HtmlBuilder("Book")
    f = b.add_font(font_path, family="Fam")
    out = b.export(tmp_path)

    fdir = out / "fonts"
    assert f
    assert (fdir / f.filename).read_bytes() == b"fontbin"
