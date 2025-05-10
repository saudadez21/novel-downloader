#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests.utils.test_hash_utils
----------------------------
"""


import numpy as np
import pytest
from PIL import Image

from novel_downloader.utils.hash_utils import (
    HASH_SIZE,
    _threshold_and_pack,
    fast_hamming_distance,
    hash_to_int,
    phash,
)


def test_hash_to_int_basic():
    """Binary array [True, False, True, True] -> int 0b1011 == 11."""
    arr = np.array([True, False, True, True], dtype=bool)
    assert hash_to_int(arr) == 0b1011


def test_hash_to_int_empty():
    """Empty array should map to 0."""
    arr = np.array([], dtype=bool)
    assert hash_to_int(arr) == 0


def test_fast_hamming_distance_zero():
    """Identical hashes -> distance 0."""
    assert fast_hamming_distance(0b101010, 0b101010) == 0


def test_fast_hamming_distance_various():
    """Verify distances on known bit patterns."""
    assert fast_hamming_distance(0b1100, 0b1010) == 2
    assert fast_hamming_distance(0, 0b1111) == 4
    # symmetric
    assert fast_hamming_distance(0b1111, 0) == 4


def test_threshold_and_pack_all_equal():
    """All-equal matrix -> all bits False -> int 0."""
    mat = np.full((4, 4), 7.0)
    assert _threshold_and_pack(mat) == 0


def test_threshold_and_pack_known_pattern():
    """
    2x2 matrix [[1,2],[3,4]] has median 2.5.
    Only '4' > median -> bits [F,F,T,T] -> 0b0011 == 3
    """
    mat = np.array([[1, 2], [3, 4]], dtype=float)
    assert _threshold_and_pack(mat) == 3


def test_phash_raises_on_small_hash_size():
    """hash_size < 2 should raise ValueError."""
    img = Image.new("L", (2, 2))
    with pytest.raises(ValueError):
        phash(img, hash_size=1, highfreq_factor=1)


def test_phash_constant_image_small(tmp_path):
    """
    A constant-gray image resized to 2x2 (hash_size=2, highfreq_factor=1)
    yields DCT with one non-zero at DC and zeros elsewhere -> threshold->0.
    """
    img = Image.new("L", (10, 10), color=128)
    h = phash(img, hash_size=2, highfreq_factor=1)
    assert isinstance(h, int)
    assert h == 8  # bits [T,F,F,F] -> 0b1000 == 8


def test_phash_consistency_identical_images():
    """Identical images must produce identical hashes."""
    img1 = Image.new("L", (8, 8), color=200)
    img2 = Image.new("L", (8, 8), color=200)
    h1 = phash(img1, hash_size=4, highfreq_factor=1)
    h2 = phash(img2, hash_size=4, highfreq_factor=1)
    assert h1 == h2


def test_phash_different_images_have_distance():
    """Black vs white image should have non-zero Hamming distance."""
    img_black = Image.new("L", (8, 8), color=0)
    img_white = Image.new("L", (8, 8), color=255)
    h_black = phash(img_black, hash_size=4, highfreq_factor=1)
    h_white = phash(img_white, hash_size=4, highfreq_factor=1)
    assert fast_hamming_distance(h_black, h_white) > 0


def test_phash_default_parameters(tmp_path):
    """Default hash_size and highfreq_factor run without error and return int."""
    size = HASH_SIZE * 2
    img = Image.new("L", (size, size), color=100)
    h = phash(img)  # uses default HASH_SIZE and highfreq_factor=4
    assert isinstance(h, int)
