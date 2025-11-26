from __future__ import annotations

import random

import pytest
from Crypto.Util.Padding import pad as ref_pad
from Crypto.Util.Padding import unpad as ref_unpad

from novel_downloader.libs.crypto.padding import pad as my_pad
from novel_downloader.libs.crypto.padding import unpad as my_unpad

_rng = random.Random(20251123)


def randbytes(n: int) -> bytes:
    """Reproducible random bytes using Python's random.Random."""
    return bytes(_rng.randrange(0, 256) for _ in range(n))


@pytest.mark.parametrize("style", ["pkcs7", "x923", "iso7816"])
@pytest.mark.parametrize("block_size", [1, 2, 3, 8, 16, 32])
@pytest.mark.parametrize(
    "data",
    [
        b"",  # empty
        b"\x00",
        b"\x01\x02\x03",
        b"hello",
        b"\xff" * 7,
        b"\x10" * 16,
        b"The quick brown fox jumps over the lazy dog",
    ],
)
def test_pad_matches_pycryptodome_known(style: str, block_size: int, data: bytes):
    got = my_pad(data, block_size, style=style)
    exp = ref_pad(data, block_size, style=style)
    assert got == exp


@pytest.mark.parametrize("style", ["pkcs7", "x923", "iso7816"])
@pytest.mark.parametrize("block_size", [1, 2, 3, 8, 16, 32])
@pytest.mark.parametrize("n", list(range(0, 4 * 32 + 1)))  # 0..128 bytes
def test_pad_matches_pycryptodome_random(style: str, block_size: int, n: int):
    data = randbytes(n)
    got = my_pad(data, block_size, style=style)
    exp = ref_pad(data, block_size, style=style)
    assert got == exp


@pytest.mark.parametrize("style", ["pkcs7", "x923", "iso7816"])
@pytest.mark.parametrize("block_size", [1, 2, 3, 8, 16, 32])
@pytest.mark.parametrize("n", [0, 1, 2, 7, 8, 15, 16, 17, 31, 32, 33, 63, 64, 65])
def test_unpad_roundtrip_and_matches_pycryptodome(style: str, block_size: int, n: int):
    data = randbytes(n)

    padded_my = my_pad(data, block_size, style=style)
    padded_ref = ref_pad(data, block_size, style=style)
    assert padded_my == padded_ref

    unp_my = my_unpad(padded_my, block_size, style=style)
    unp_ref = ref_unpad(padded_ref, block_size, style=style)
    assert unp_my == data
    assert unp_my == unp_ref


def test_pad_invalid_block_size():
    with pytest.raises(ValueError):
        my_pad(b"abc", 0, style="pkcs7")
    with pytest.raises(ValueError):
        my_pad(b"abc", 256, style="pkcs7")


def test_unpad_invalid_block_size():
    with pytest.raises(ValueError):
        my_unpad(b"abcd", 0, style="pkcs7")
    with pytest.raises(ValueError):
        my_unpad(b"abcd", 256, style="pkcs7")


def test_pad_unknown_style():
    with pytest.raises(ValueError):
        my_pad(b"abc", 16, style="nope")


def test_unpad_unknown_style():
    with pytest.raises(ValueError):
        my_unpad(b"abc" * 16, 16, style="nope")


@pytest.mark.parametrize("style", ["pkcs7", "x923", "iso7816"])
def test_unpad_rejects_non_multiple_length(style: str):
    with pytest.raises(ValueError):
        my_unpad(b"\x00" * 15, 16, style=style)


@pytest.mark.parametrize("block_size", [8, 16])
def test_unpad_pkcs7_tamper(block_size: int):
    data = b"attack at dawn"
    padded = my_pad(data, block_size, style="pkcs7")
    bad = padded[:-1] + bytes([padded[-1] ^ 0x01])  # flip last byte
    with pytest.raises(ValueError):
        my_unpad(bad, block_size, style="pkcs7")
    with pytest.raises(ValueError):
        ref_unpad(bad, block_size, style="pkcs7")


@pytest.mark.parametrize("block_size", [8, 16])
def test_unpad_x923_tamper(block_size: int):
    data = b"attack at dusk"
    padded = my_pad(data, block_size, style="x923")

    # break the zero-fill part if padding_len > 1
    pad_len = padded[-1]
    if pad_len > 1:
        idx = len(padded) - pad_len  # first byte of padding
        bad = bytearray(padded)
        bad[idx] ^= 0xFF
        bad = bytes(bad)
        with pytest.raises(ValueError):
            my_unpad(bad, block_size, style="x923")
        with pytest.raises(ValueError):
            ref_unpad(bad, block_size, style="x923")
    else:
        # padding_len == 1: just flip the last byte
        bad = padded[:-1] + bytes([padded[-1] ^ 0x01])
        with pytest.raises(ValueError):
            my_unpad(bad, block_size, style="x923")
        with pytest.raises(ValueError):
            ref_unpad(bad, block_size, style="x923")


@pytest.mark.parametrize("block_size", [8, 16])
def test_unpad_iso7816_tamper(block_size: int):
    data = b"hello world"
    padded = my_pad(data, block_size, style="iso7816")

    bad = bytearray(padded)
    last_block_start = len(bad) - block_size
    for i in range(block_size):
        if bad[last_block_start + i] == 0x80:
            bad[last_block_start + i] = 0x81
            break
    bad = bytes(bad)

    with pytest.raises(ValueError):
        my_unpad(bad, block_size, style="iso7816")
    with pytest.raises(ValueError):
        ref_unpad(bad, block_size, style="iso7816")
