#!/usr/bin/env python3
"""
novel_downloader.utils.hash_utils
---------------------------------

Utilities for image perceptual hashing and comparison.

Implements a perceptual hash (pHash) based on DCT, following the method
described in:
https://www.hackerfactor.com/blog/index.php?/archives/432-Looks-Like-It.html

Provides:
- pHash computation via DCT and median thresholding
- Integer hash representation
- Fast Hamming distance between hashes
"""

import numpy as np
from numpy.typing import NDArray
from PIL import Image
from scipy.fft import dct as dct_1d

ANTIALIAS = Image.Resampling.LANCZOS
HASH_SIZE = 10  # default is 8
HASH_DISTANCE_THRESHOLD = 5


def hash_to_int(hash_array: NDArray[np.bool_]) -> int:
    """
    Convert a boolean hash array to an integer.

    :param hash_array: A binary array (dtype=bool) from a hash function.
    :type hash_array: np.ndarray
    :return: Integer representation of the binary hash.
    :rtype: int
    """
    result = 0
    for bit in hash_array:
        result = (result << 1) | int(bit)
    return result


def fast_hamming_distance(hash_1: int, hash_2: int) -> int:
    """
    Compute the Hamming distance between two integer-based image hashes.

    Uses bitwise XOR and bit count for fast comparison.

    :param hash_1: First image hash (as integer).
    :type hash_1: int
    :param hash_2: Second image hash (as integer).
    :type hash_2: int
    :return: Number of differing bits between the two hashes.
    :rtype: int
    """
    x = hash_1 ^ hash_2
    count = 0
    while x:
        x &= x - 1
        count += 1
    return count


def _threshold_and_pack(dct_low: NDArray[np.float64]) -> int:
    """
    Convert a low-frequency DCT matrix into a binary hash.

    Compares each element to the median, builds a boolean mask,
    then packs it into an integer.
    """
    med = np.median(dct_low)
    diff = dct_low > med
    return hash_to_int(diff.flatten())


def phash(
    image: Image.Image, hash_size: int = HASH_SIZE, highfreq_factor: int = 4
) -> int:
    """
    Compute the perceptual hash (pHash) of an image.

    This method applies a Discrete Cosine Transform (DCT) to extract
    low-frequency features, then compares them to the median to create
    a binary fingerprint of the image.

    :param image: The input image.
    :type image: PIL.Image.Image
    :param hash_size: Size of the resulting hash (NxN).
    :type hash_size: int
    :param highfreq_factor: Multiplier for the image resize to preserve detail.
    :type highfreq_factor: int
    :return: Integer representation of the perceptual hash.
    :rtype: int
    """
    if hash_size < 2:
        raise ValueError("Hash size must be greater than or equal to 2")

    img_size = hash_size * highfreq_factor
    image = image.convert("L").resize((img_size, img_size), ANTIALIAS)
    pixels = np.asarray(image)
    dct = dct_1d(dct_1d(pixels, axis=0, norm="ortho"), axis=1, norm="ortho")
    dctlowfreq = dct[:hash_size, :hash_size]
    return _threshold_and_pack(dctlowfreq)
