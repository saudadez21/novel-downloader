#!/usr/bin/env python3
"""
tests.utils.test_hash_store
----------------------------
"""

import json
import logging

import pytest
from PIL import Image

import novel_downloader.utils.hash_store as hs_mod
from novel_downloader.utils.hash_store import ImageHashStore, _BKNode


def test_bknode_add_and_query_simple():
    """_BKNode should add values and query within threshold correctly."""
    node = _BKNode(5)
    # children distances: 7->2, 4->1
    node.add(7, lambda a, b: abs(a - b))
    node.add(4, lambda a, b: abs(a - b))
    # query with threshold=1: should match root (5,0) and child 4 (4,1)
    matches = node.query(5, threshold=1, dist_fn=lambda a, b: abs(a - b))
    assert set(matches) == {(5, 0), (4, 1)}


def test_load_empty_store(tmp_path, caplog):
    """Loading when no file exists should start empty with info log."""
    store_path = tmp_path / "empty.json"
    caplog.set_level(logging.INFO)
    store = ImageHashStore(
        path=store_path,
        auto_save=False,
        hash_func=lambda img: 0,
        ham_dist=lambda a, b: 0,
    )
    # no file -> empty
    assert store.labels() == []
    assert store.hashes("any") == set()
    assert store.query(123) == []
    assert "[ImageHashStore] No file found" in caplog.text


def test_save_and_load_json(tmp_path):
    """Saving to and loading from .json preserves the hash sets."""
    store_path = tmp_path / "store.json"
    store = ImageHashStore(
        path=store_path,
        auto_save=False,
        hash_func=lambda img: 0,
        ham_dist=lambda a, b: 0,
    )
    # manually set internal state
    store._hash = {"a": {1, 2}, "b": {3}}
    store.save()
    # file content
    data = json.loads(store_path.read_text(encoding="utf-8"))
    assert set(data["a"]) == {1, 2}
    assert set(data["b"]) == {3}
    # reload
    reloaded = ImageHashStore(
        path=store_path,
        auto_save=False,
        hash_func=lambda img: 0,
        ham_dist=lambda a, b: 0,
    )
    assert reloaded._hash == {"a": {1, 2}, "b": {3}}
    assert reloaded.labels() == ["a", "b"]


def test_save_and_load_npy(tmp_path):
    """Saving to and loading from .npy preserves the hash sets."""
    npy_path = tmp_path / "store.npy"
    store = ImageHashStore(
        path=npy_path, auto_save=False, hash_func=lambda img: 0, ham_dist=lambda a, b: 0
    )
    store._hash = {"x": {9}}
    store.save()
    # check npy file exists
    assert npy_path.exists()
    # reload
    reloaded = ImageHashStore(
        path=npy_path, auto_save=False, hash_func=lambda img: 0, ham_dist=lambda a, b: 0
    )
    assert reloaded._hash == {"x": {9}}


def test_add_and_remove_image_and_label(tmp_path):
    """add_image, labels, hashes, remove_label, remove_hash by int and by path."""
    # create two 1x1 images: pixel values 10 and 20
    img1 = tmp_path / "i1.png"
    img2 = tmp_path / "i2.png"
    Image.new("L", (1, 1), color=10).save(img1)
    Image.new("L", (1, 1), color=20).save(img2)

    # stub hash_func to return pixel value; absolute diff threshold=5
    store = ImageHashStore(
        path=tmp_path / "h.json",
        auto_save=False,
        hash_func=lambda img: img.getpixel((0, 0)),
        ham_dist=lambda a, b: abs(a - b),
        threshold=5,
    )

    # add first image under label 'foo'
    h1 = store.add_image(img1, "foo")
    assert h1 == 10
    assert store.labels() == ["foo"]
    assert store.hashes("foo") == {10}

    # add second under same label
    h2 = store.add_image(img2, "foo")
    assert h2 == 20
    assert store.hashes("foo") == {10, 20}

    # remove hash by int
    removed = store.remove_hash("foo", 10)
    assert removed is True
    assert store.hashes("foo") == {20}
    # removing again returns False
    assert store.remove_hash("foo", 10) is False

    # remove by image path
    removed2 = store.remove_hash("foo", img2)
    assert removed2 is True
    assert store.hashes("foo") == set()

    # remove nonexistent label
    assert store.remove_label("doesnot") is None
    # remove existing label
    store._hash = {"bar": {1}}
    store.remove_label("bar")
    assert "bar" not in store.labels()


def test_remove_hash_invalid_path(tmp_path, caplog):
    """remove_hash should catch open errors and return False with warning."""
    store = ImageHashStore(
        path=tmp_path / "xx.json",
        auto_save=False,
        hash_func=lambda img: 0,
        ham_dist=lambda a, b: 0,
    )
    # ensure the label exists so we enter the image-open branch
    store._hash["any"] = set()

    # create a non-image file
    bad = tmp_path / "bad.txt"
    bad.write_text("not an image", encoding="utf-8")

    caplog.set_level(logging.WARNING)
    result = store.remove_hash("any", bad)
    assert result is False

    # now we should see the warning from inside the except block
    assert "[ImageHashStore] Could not open image" in caplog.text


def test_add_from_map(tmp_path, caplog):
    """add_from_map should add existing images and warn on failures."""
    # setup two images
    imgA = tmp_path / "A.png"
    imgB = tmp_path / "B.png"
    Image.new("L", (1, 1), color=5).save(imgA)
    Image.new("L", (1, 1), color=15).save(imgB)
    # create mapping JSON with one bad entry
    mapping = {"A.png": "L1", "missing.png": "LX", "B.png": "L2"}
    mapfile = tmp_path / "map.json"
    mapfile.write_text(json.dumps(mapping), encoding="utf-8")

    # stub hash_func
    store = ImageHashStore(
        path=tmp_path / "mm.json",
        auto_save=False,
        hash_func=lambda img: img.getpixel((0, 0)),
        ham_dist=lambda a, b: 0,
    )
    caplog.set_level(logging.WARNING)
    store.add_from_map(mapfile)

    # should have added only A.png and B.png
    assert set(store.labels()) == {"L1", "L2"}
    assert store.hashes("L1") == {5}
    assert store.hashes("L2") == {15}
    # warning for missing.png
    assert "Failed to add image" in caplog.text


def test_query_with_int_and_image_and_k_and_threshold(tmp_path):
    """query should accept int or Image, respect k and threshold, and compute scores."""
    # create two images
    img1 = tmp_path / "one.png"
    img2 = tmp_path / "two.png"
    Image.new("L", (1, 1), color=10).save(img1)
    Image.new("L", (1, 1), color=20).save(img2)

    # hash_func is pixel value, ham_dist absolute diff, threshold=100
    store = ImageHashStore(
        path=tmp_path / "qq.json",
        auto_save=False,
        hash_func=lambda img: img.getpixel((0, 0)),
        ham_dist=lambda a, b: abs(a - b),
        threshold=100,
    )
    store.add_image(img1, "A")
    store.add_image(img2, "B")

    # query by int
    res_int = store.query(10, k=2)
    # scores: A->1.0, B->1 - 10/100=0.9; sorted by ascending score (lowest first)
    assert res_int == [("B", 0.9), ("A", 1.0)]

    # query by image
    pic = Image.new("L", (1, 1), color=20)
    res_img = store.query(pic, k=1)
    # only lowest score:
    # A distance=10->score=0.9,
    # B distance=0->score=1.0 -> lowest is A
    assert res_img == [("A", 0.9)]


def test_maybe_save_direct(monkeypatch, tmp_path):
    """_maybe_save should call save() only when auto_save is True."""
    store = ImageHashStore(path=tmp_path / "store.json", auto_save=False)
    called = []
    monkeypatch.setattr(store, "save", lambda: called.append("saved"))

    # auto_save=False -> no save
    store._maybe_save()
    assert called == []

    # flip to auto_save=True
    store._auto = True
    store._maybe_save()
    assert called == ["saved"]


# ensure module‐level instance exists
def test_module_instance_present():
    """The module should define img_hash_store as an ImageHashStore."""
    assert isinstance(hs_mod.img_hash_store, ImageHashStore)


def test_remove_hash_label_not_present_and_no_save(monkeypatch, tmp_path):
    """remove_hash returns False immediately if label not in store, without saving."""
    store = ImageHashStore(path=tmp_path / "store.json", auto_save=True)
    called = []
    monkeypatch.setattr(store, "save", lambda: called.append("saved"))

    # label 'foo' does not exist
    result = store.remove_hash("foo", 123)
    assert result is False
    assert called == []


def test_remove_hash_auto_save_when_removed(monkeypatch, tmp_path):
    """When auto_save=True and a hash is removed, save() should be called."""
    # create a small image and store
    img_path = tmp_path / "img.png"
    Image.new("L", (1, 1), color=7).save(img_path)

    # define hash_func to return constant, ham_dist unused here
    store = ImageHashStore(
        path=tmp_path / "store.json",
        auto_save=True,
        hash_func=lambda img: img.getpixel((0, 0)),
        ham_dist=lambda a, b: 0,
        threshold=1,
    )
    # add under label 'lbl'
    h = store.add_image(img_path, "lbl")
    assert h == 7
    # patch save
    called = []
    monkeypatch.setattr(store, "save", lambda: called.append("saved"))

    # remove by hash int
    res = store.remove_hash("lbl", h)
    assert res is True
    assert called == ["saved"]


def test_query_with_path(tmp_path):
    """
    query should open an image given by path (str or Path),
    compute its hash via hash_func, and return matching labels.
    """
    img_path = tmp_path / "pic.png"
    Image.new("L", (1, 1), color=42).save(img_path)

    # stub hash_func and ham_dist so only exact matches within threshold
    store = ImageHashStore(
        path=tmp_path / "store.json",
        auto_save=False,
        hash_func=lambda img: img.getpixel((0, 0)),
        ham_dist=lambda a, b: abs(a - b),
        threshold=10,
    )
    # add image under 'P'
    store.add_image(img_path, "P")

    # query by passing the path as a string
    res_str = store.query(str(img_path), k=1)
    assert res_str == [("P", 1.0)] or res_str == [("P", pytest.approx(1.0))]

    # query by passing the Path object
    res_path = store.query(img_path, k=1)
    assert res_path == res_str
