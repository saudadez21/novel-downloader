from novel_downloader.libs.html_builder.models import (
    HtmlChapter,
    HtmlFont,
    HtmlImage,
    HtmlVolume,
    IndexDocument,
    escape,
)


# ---------------------------------------------------------------------
# escape()
# ---------------------------------------------------------------------
def test_escape_basic():
    assert escape("<a&b>") == "&lt;a&amp;b&gt;"
    assert escape('"hello"') == "&quot;hello&quot;"
    assert escape("a'b") == "a&#x27;b"


# ---------------------------------------------------------------------
# HtmlImage
# ---------------------------------------------------------------------
def test_html_image_basic():
    img = HtmlImage(filename="a.jpg", data=b"abc")
    assert img.filename == "a.jpg"
    assert img.data == b"abc"


# ---------------------------------------------------------------------
# HtmlFont
# ---------------------------------------------------------------------
def test_html_font_effective_selectors_default():
    f = HtmlFont(filename="a.ttf", data=b"x", family="F")
    assert f.effective_selectors == (".chapter-content",)


def test_html_font_effective_selectors_custom():
    f = HtmlFont(filename="a.ttf", data=b"x", family="F", selectors=(".x",))
    assert f.effective_selectors == (".x",)


def test_html_font_build_css():
    f = HtmlFont(filename="my.woff", data=b"x", family="Fam")
    css = f.build_css(font_url_prefix="../fonts/")
    assert "Fam" in css
    assert "my.woff" in css
    assert "format(" in css


# ---------------------------------------------------------------------
# HtmlChapter
# ---------------------------------------------------------------------
def test_html_chapter_to_html_basic():
    chap = HtmlChapter(filename="1.html", title="T", content="C")
    html = chap.to_html()
    assert "<title>T</title>" in html or "T" in html  # depending on template
    assert "C" in html


def test_html_chapter_extra_block():
    chap = HtmlChapter(filename="1.html", title="T", content="C", extra_content="EX")
    html = chap.to_html()
    assert "extra-block" in html
    assert "EX" in html


def test_html_chapter_font_styles():
    f1 = HtmlFont(filename="A.ttf", data=b"x", family="F1")
    f2 = HtmlFont(filename="B.ttf", data=b"x", family="F2", selectors=(".x",))
    chap = HtmlChapter(
        filename="c.html",
        title="T",
        content="C",
        fonts=[f1, f2],
    )
    html = chap.to_html()
    # font-face emitted
    assert "@font-face" in html
    assert "F1" in html and "F2" in html
    # selector mapping emitted
    assert ".chapter-content" in html
    assert ".x" in html


# ---------------------------------------------------------------------
# HtmlVolume
# ---------------------------------------------------------------------
def test_html_volume_basic():
    v = HtmlVolume(title="Vol", intro="Intro")
    assert v.title == "Vol"
    assert v.intro == "Intro"


# ---------------------------------------------------------------------
# IndexDocument
# ---------------------------------------------------------------------
def test_index_document_add_volume():
    chap = HtmlChapter(filename="c.html", title="CT", content="C")
    v = HtmlVolume(title="V", intro="I", chapters=[chap])

    idx = IndexDocument(title="Book")
    idx.add_volume(v)

    assert len(idx.toc_blocks) == 1
    block = idx.toc_blocks[0]
    assert "V" in block
    assert "I" in block
    assert "c.html" in block
    assert "CT" in block


def test_index_document_add_chapter():
    chap = HtmlChapter(filename="x.html", title="T", content="C")
    idx = IndexDocument(title="Book")
    idx.add_chapter(chap)

    assert len(idx.toc_blocks) == 1
    block = idx.toc_blocks[0]
    assert "x.html" in block
    assert "T" in block


def test_index_document_header_all_fields():
    idx = IndexDocument(
        title="Book",
        author="A",
        description="Desc",
        subject=["tag1", "tag2"],
        serial_status="ongoing",
        word_count="12345",
    )
    idx.cover_filename = "cover.jpg"

    html = idx.to_html()
    # header
    assert "Book" in html
    assert "A" in html
    assert "Desc" in html
    assert "tag1" in html
    assert "ongoing" in html
    assert "12345" in html
    assert "cover.jpg" in html


def test_index_document_clear():
    idx = IndexDocument(title="B")
    chap = HtmlChapter(filename="1.html", title="T", content="C")
    idx.add_chapter(chap)
    assert idx.toc_blocks
    idx.clear()
    assert idx.toc_blocks == []
