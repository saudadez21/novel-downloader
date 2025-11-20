import zipfile
from pathlib import Path

from novel_downloader.libs.epub_builder.constants import (
    CSS_DIR,
    ROOT_PATH,
    TEXT_DIR,
)
from novel_downloader.libs.epub_builder.core import EpubBuilder
from novel_downloader.libs.epub_builder.models import (
    EpubChapter,
    EpubVolume,
)


# ---------------------------------------------------------
# Minimal helpers
# ---------------------------------------------------------
def make_temp_image(tmp_path: Path, name="img.png", data=b"\x89PNG\r\n\x1a\nxxx"):
    """Create a minimal valid PNG header so detect_image_format returns png."""
    p = tmp_path / name
    p.write_bytes(data)
    return p


def make_temp_font(tmp_path: Path, name="font.ttf"):
    """
    Create a fake TTF font header so detect_font_format returns 'ttf'.
    Real TTF starts with 00 01 00 00.
    """
    p = tmp_path / name
    p.write_bytes(b"\x00\x01\x00\x00FAKEFONTDATA")
    return p


# ---------------------------------------------------------
# Test: EpubBuilder basic initialization
# ---------------------------------------------------------
def test_builder_initial_state():
    builder = EpubBuilder(
        title="MyBook", author="Author", description="Desc", uid="UID123"
    )

    # intro must be registered in manifest/spine/nav/ncx
    assert builder.items[0].id == "intro"
    assert builder.opf.manifest_lines  # contains nav + ncx + style + intro
    assert builder.opf.spine_lines  # intro added to spine
    assert builder.nav.lines  # intro added
    assert builder.ncx.lines  # intro added


def test_builder_with_cover(tmp_path):
    # Create fake PNG cover file
    cover = tmp_path / "cover.png"
    # Minimal PNG header
    cover.write_bytes(b"\x89PNG\r\n\x1a\nxxxx")

    b = EpubBuilder(
        title="Book", author="A", description="D", cover_path=cover, uid="UID"
    )

    assert any(img.id == "cover-img" for img in b.images)

    cover_img = next(img for img in b.images if img.id == "cover-img")
    assert cover_img.filename.startswith("cover.")
    assert cover_img.media_type == "image/png"

    assert any(
        'properties="cover-image"' in line and "cover-img" in line
        for line in b.opf.manifest_lines
    )

    assert any(item.id == "cover" for item in b.items)
    cover_page = next(item for item in b.items if item.id == "cover")
    assert cover_page.filename == "cover.xhtml"

    assert any('idref="cover"' in line for line in b.opf.spine_lines)

    assert any("cover.xhtml" in ln for ln in b.nav.lines)
    assert any("cover.xhtml" in ln for ln in b.ncx.lines)


# ---------------------------------------------------------
# Test: Add image file (dedupe + manifest registration)
# ---------------------------------------------------------
def test_add_image_file(tmp_path):
    img = make_temp_image(tmp_path)

    b = EpubBuilder("T")
    fn1 = b.add_image(img)
    fn2 = b.add_image(img)  # dedupe

    assert fn1 == fn2  # dedupe OK
    assert len(b.images) == 1  # only 1 registered

    # check manifest contains the image entry
    assert any("img_0" in line for line in b.opf.manifest_lines)


# ---------------------------------------------------------
# Test: Add image bytes
# ---------------------------------------------------------
def test_add_image_bytes():
    # minimal PNG header
    data = b"\x89PNG\r\n\x1a\nxxxx"

    b = EpubBuilder("T")
    fn = b.add_image_bytes(data)
    assert fn.endswith(".png")
    assert len(b.images) == 1


# ---------------------------------------------------------
# Test: Add font file (dedupe + manifest)
# ---------------------------------------------------------
def test_add_font_file(tmp_path):
    font = make_temp_font(tmp_path)

    b = EpubBuilder("T")
    f1 = b.add_font(font)
    f2 = b.add_font(font)  # dedupe

    assert f1
    assert f1 is f2
    assert len(b.fonts) == 1
    assert f1.filename.endswith(".ttf")


# ---------------------------------------------------------
# Test: Add font bytes
# ---------------------------------------------------------
def test_add_font_bytes():
    data = b"\x00\x01\x00\x00FAKEFONTDATA"

    b = EpubBuilder("T")
    f = b.add_font_bytes(data)

    assert f
    assert f.filename.endswith(".ttf")


# ---------------------------------------------------------
# Test: Add chapter
# ---------------------------------------------------------
def test_add_chapter():
    b = EpubBuilder("T")
    ch = EpubChapter(id="c1", filename="c1.xhtml", title="Chapter 1")

    b.add_chapter(ch)

    # registered
    assert ch in b.items
    assert any("c1.xhtml" in line for line in b.opf.manifest_lines)
    assert any("c1" in line for line in b.opf.spine_lines)
    assert any("Chapter 1" in ln for ln in b.nav.lines)
    assert any("Chapter 1" in ln for ln in b.ncx.lines)


# ---------------------------------------------------------
# Test: Add volume with chapters
# ---------------------------------------------------------
def test_add_volume(tmp_path):
    img = make_temp_image(tmp_path)
    ch1 = EpubChapter(id="c1", filename="c1.xhtml", title="Ch1")
    ch2 = EpubChapter(id="c2", filename="c2.xhtml", title="Ch2")

    volume = EpubVolume(
        id="v", title="Vol1", intro="Intro text", cover_path=img, chapters=[ch1, ch2]
    )

    b = EpubBuilder("Book")
    b.add_volume(volume)

    # volume cover or title page must appear
    assert any("vol_0" in item.id for item in b.items)

    # chapters registered
    assert any("c1.xhtml" in line for line in b.opf.manifest_lines)
    assert any("c2.xhtml" in line for line in b.opf.manifest_lines)

    # nav & ncx entries added
    assert any("Vol1" in ln for ln in b.nav.lines)
    assert any("Vol1" in ln for ln in b.ncx.lines)


# ---------------------------------------------------------
# Test: Export EPUB and check ZIP file content
# ---------------------------------------------------------
def test_export_epub(tmp_path):
    b = EpubBuilder(title="Book")

    # add a tiny chapter
    ch = EpubChapter(id="ch", filename="ch.xhtml", title="Chap")
    b.add_chapter(ch)

    out = tmp_path / "out.epub"
    b.export(out)

    assert out.exists()

    # Check EPUB structure
    with zipfile.ZipFile(out, "r") as z:
        names = z.namelist()

        # mandatory files
        assert "mimetype" in names
        assert "META-INF/container.xml" in names

        # core doc paths
        assert f"{ROOT_PATH}/nav.xhtml" in names
        assert f"{ROOT_PATH}/toc.ncx" in names
        assert f"{ROOT_PATH}/content.opf" in names

        # item we added
        assert f"{ROOT_PATH}/{TEXT_DIR}/ch.xhtml" in names

        # default style file
        assert f"{ROOT_PATH}/{CSS_DIR}/style.css" in names


# ---------------------------------------------------------
# Test: Export EPUB basic validity ("mimetype" must be stored)
# ---------------------------------------------------------
def test_export_mimetype_stored(tmp_path):
    b = EpubBuilder("Book")
    out = tmp_path / "ok.epub"
    b.export(out)

    with zipfile.ZipFile(out, "r") as z:
        info = z.getinfo("mimetype")
        # Compression must be ZIP_STORED (0)
        assert info.compress_type == zipfile.ZIP_STORED
