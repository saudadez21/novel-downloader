import hashlib

from novel_downloader.libs.filesystem.filename import (
    DEFAULT_FONT_SUFFIX,
    DEFAULT_IMAGE_SUFFIX,
    SafeDict,
    font_filename,
    format_filename,
    image_filename,
    url_to_hashed_name,
)

# ----------------------------------------------------------------------
# SafeDict
# ----------------------------------------------------------------------


def test_safe_dict_missing():
    s = SafeDict()
    assert s["unknown"] == "{unknown}"


# ----------------------------------------------------------------------
# url_to_hashed_name
# ----------------------------------------------------------------------


def test_url_to_hashed_name_preserve_suffix():
    url = "http://example.com/img/photo.jpg"
    name = url_to_hashed_name(url, allowed_suffixes={".jpg"}, default_suffix=".png")
    assert name.endswith(".jpg")  # preserved


def test_url_to_hashed_name_disallowed_suffix():
    url = "http://example.com/img/photo.bmp"
    name = url_to_hashed_name(url, allowed_suffixes={".jpg"}, default_suffix=".png")
    assert name.endswith(".png")  # fallback to default suffix


def test_url_to_hashed_name_no_suffix_and_default():
    url = "http://example.com/file"
    name = url_to_hashed_name(url, default_suffix=".bin")
    assert name.endswith(".bin")


def test_url_to_hashed_name_custom_name():
    url = "http://example.com/a.png"
    assert (
        url_to_hashed_name(url, name="custom", allowed_suffixes={".png"})
        == "custom.png"
    )


def test_url_to_hashed_name_hash_name():
    url = "http://example.com/a.png"
    expected = hashlib.sha1(url.encode("utf-8")).hexdigest() + ".png"
    assert url_to_hashed_name(url, allowed_suffixes={".png"}) == expected


# ----------------------------------------------------------------------
# image_filename
# ----------------------------------------------------------------------


def test_image_filename_allows_common_ext():
    url = "https://cdn.xx.com/a/b/c.jpeg"
    assert image_filename(url).endswith(".jpeg")


def test_image_filename_fallback_default_suffix():
    url = "https://cdn.xx.com/a/b/c.xyz"
    assert image_filename(url).endswith(DEFAULT_IMAGE_SUFFIX)


def test_image_filename_custom_name():
    url = "https://cdn.xx.com/a/b/c.png"
    assert image_filename(url, name="pic") == "pic.png"


# ----------------------------------------------------------------------
# font_filename
# ----------------------------------------------------------------------


def test_font_filename_valid_ext():
    url = "https://fonts.xx.com/f.woff2"
    assert font_filename(url).endswith(".woff2")


def test_font_filename_fallback_default():
    url = "https://fonts.xx.com/f.abc"
    assert font_filename(url).endswith(DEFAULT_FONT_SUFFIX)


def test_font_filename_custom_name():
    url = "https://fonts.xx.com/font.ttf"
    assert font_filename(url, name="myfont") == "myfont.ttf"


# ----------------------------------------------------------------------
# format_filename
# ----------------------------------------------------------------------


def test_format_filename_basic_ext():
    name = format_filename("book_{id}", id="1", append_timestamp=False, ext="txt")
    assert name == "book_1.txt"


def test_format_filename_no_ext():
    name = format_filename("x_{a}", a="y", append_timestamp=False, ext="")
    assert name == "x_y"


def test_format_filename_timestamp_added():
    n = format_filename("file", append_timestamp=True, ext="log")

    assert n.startswith("file_")
    assert n.endswith(".log")
    ts = n[len("file_") : -4]
    assert len(ts) == len("20251111_123413")


def test_format_filename_missing_field_safe():
    # missing field → SafeDict returns {missing}
    name = format_filename("item_{missing}", append_timestamp=False, ext="txt")
    assert name == "item_{missing}.txt"
