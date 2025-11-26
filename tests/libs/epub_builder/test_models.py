import pytest

from novel_downloader.libs.epub_builder.constants import (
    DEFAULT_FONT_FALLBACK_STACK,
)
from novel_downloader.libs.epub_builder.models import (
    EpubChapter,
    EpubCover,
    EpubFont,
    EpubIntro,
    EpubVolumeTitle,
    EpubXhtmlContent,
    NavDocument,
    NCXDocument,
    OpfDocument,
    escape_label,
    escape_text,
)


# ---------------------------------------------------------
# Escape functions
# ---------------------------------------------------------
def test_escape_label():
    assert escape_label("&<>") == "&amp;&lt;&gt;"


def test_escape_text():
    assert escape_text("<&\">'") == "&lt;&amp;&quot;&gt;&#x27;"


# ---------------------------------------------------------
# Font model
# ---------------------------------------------------------
def test_epub_font_face_css():
    font = EpubFont(
        id="f1",
        filename="font.ttf",
        media_type="font/ttf",
        data=b"xxx",
        format="truetype",
        family="MyFont",
    )
    css = font.face_css
    assert "MyFont" in css
    assert "font.ttf" in css
    assert "@font-face" in css or "src:" in css


# ---------------------------------------------------------
# EpubXhtmlContent & font styles
# ---------------------------------------------------------
def test_epub_xhtml_content_font_styles():
    font1 = EpubFont(
        id="f1",
        filename="A.ttf",
        media_type="font/ttf",
        data=b"x",
        format="truetype",
        family="F1",
        selectors=("body",),
    )
    font2 = EpubFont(
        id="f2",
        filename="B.ttf",
        media_type="font/ttf",
        data=b"x",
        format="truetype",
        family="F2",
        selectors=None,  # default selector
    )

    c = EpubXhtmlContent(
        id="c", filename="c.xhtml", title="T", content="Hello", fonts=[font1, font2]
    )

    styles = c._build_font_styles()
    assert "@font-face" in styles
    assert '"F1"' in styles
    assert '"F2"' in styles
    assert DEFAULT_FONT_FALLBACK_STACK in styles


def test_epub_xhtml_no_fonts():
    c = EpubXhtmlContent(id="c", filename="c.xhtml", title="T")
    assert c._build_font_styles() == ""


# ---------------------------------------------------------
# EpubCover
# ---------------------------------------------------------
def test_epub_cover_xhtml():
    cover = EpubCover()
    x = cover.to_xhtml()
    assert "cover" in x.lower()
    assert "xhtml" in cover.filename.lower()


# ---------------------------------------------------------
# EpubVolumeTitle splitting
# ---------------------------------------------------------
@pytest.mark.parametrize(
    "title,expected",
    [
        ("Title - Subtitle", ("Title", "Subtitle")),
        ("A:B", ("A", "B")),
        ("NoSplit", ("", "NoSplit")),
    ],
)
def test_volume_title_split(title, expected):
    assert EpubVolumeTitle._split_volume_title(title) == expected


def test_epub_volume_title_xhtml():
    v = EpubVolumeTitle(id="vt", filename="v.xhtml", full_title="Main - Sub")
    x = v.to_xhtml()
    assert "Main" in x
    assert "Sub" in x


# ---------------------------------------------------------
# EpubIntro
# ---------------------------------------------------------
def test_epub_intro_info_blocks():
    intro = EpubIntro(
        id="i",
        filename="i.xhtml",
        title="Intro",
        book_title="MyBook",
        author="AU",
        word_count="1000",
        serial_status="连载",
        subject=["a", "b"],
        description="Line1\nLine2",
    )
    x = intro.to_xhtml()

    assert "MyBook" in x
    assert "AU" in x
    assert "1000" in x
    assert "连载" in x
    assert "标签" in x
    assert "<p>Line1</p>" in x


# ---------------------------------------------------------
# EpubChapter
# ---------------------------------------------------------
def test_epub_chapter_extra_block():
    ch = EpubChapter(
        id="c", filename="c.xhtml", title="T", content="C", extra_content="EXTRA"
    )
    x = ch.to_xhtml()
    assert "EXTRA" in x


def test_epub_chapter_no_extra():
    ch = EpubChapter(id="c", filename="c.xhtml", title="T")
    assert '<div class="extra-block">' not in ch.to_xhtml()


# ---------------------------------------------------------
# NavDocument
# ---------------------------------------------------------
def test_nav_document_add_chapter():
    nav = NavDocument(id="nav", filename="nav.xhtml")
    nav.add_chapter("c1", "标签&<", "c1.xhtml")
    x = nav.to_xhtml()

    assert "&amp;&lt;" in x  # escaped
    assert "c1.xhtml" in x


def test_nav_document_add_volume():
    nav = NavDocument(id="nav", filename="nav.xhtml")
    nav.add_volume("v1", "卷一", "v1.xhtml", chapters=[("c1", "第一章", "c1.xhtml")])
    x = nav.to_xhtml()
    assert "卷一" in x
    assert "第一章" in x
    assert "<ol>" in x


# ---------------------------------------------------------
# NCXDocument
# ---------------------------------------------------------
def test_ncx_document():
    ncx = NCXDocument(id="ncx", filename="toc.ncx", title="Book", uid="u1")
    ncx.add_chapter("c1", "Chap1", "c1.xhtml")
    xml = ncx.to_xml()

    assert "Chap1" in xml
    assert "c1.xhtml" in xml
    assert "navPoint" in xml
    assert "u1" in xml


# ---------------------------------------------------------
# OpfDocument
# ---------------------------------------------------------
def test_opf_document_basic():
    opf = OpfDocument(
        id="opf", filename="opf.xml", title="Book", author="AU", uid="UID123"
    )

    opf.add_manifest_item("c1", "c1.xhtml", "application/xhtml+xml")
    opf.add_spine_item("c1")

    xml = opf.to_xml()

    assert "Book" in xml
    assert "AU" in xml
    assert "UID123" in xml
    assert "manifest" in xml or "<item" in xml
    assert '<itemref idref="c1"' in xml


def test_opf_document_cover_and_toc_detection():
    opf = OpfDocument(id="opf", filename="opf.xml", uid="UID")

    opf.add_manifest_item("cover", "cover.jpg", "image/jpeg", properties="cover-image")
    opf.add_manifest_item("ncx", "toc.ncx", "application/x-dtbncx+xml")
    opf.add_spine_item("ncx")

    xml = opf.to_xml()

    # cover meta tag added
    assert 'name="cover"' in xml
    assert "application/x-dtbncx+xml" in xml
    assert 'toc="ncx"' in xml
