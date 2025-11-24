from __future__ import annotations

import random

import pytest
from Crypto.Cipher import DES3 as RefDES3
from novel_downloader.libs.crypto.cipher import DES3

_rng = random.Random(20251123)


def randbytes(n: int) -> bytes:
    """Deterministic bytes for reproducible tests."""
    return bytes(_rng.randrange(0, 256) for _ in range(n))


def make_ref_compatible_key(key_len: int) -> bytes:
    assert key_len in (16, 24)
    for _ in range(1000):
        raw = randbytes(key_len)
        key = RefDES3.adjust_key_parity(raw)
        try:
            RefDES3.new(key, RefDES3.MODE_ECB)
            return key
        except ValueError:
            continue
    raise RuntimeError("Failed to generate a PyCryptodome-compatible DES3 key")


@pytest.mark.parametrize("key_len", [16, 24])
@pytest.mark.parametrize("nblocks", [0, 1, 2, 4, 8, 16])
def test_des3_ecb_encrypt_matches_pycryptodome(key_len: int, nblocks: int):
    key = make_ref_compatible_key(key_len)
    pt = randbytes(8 * nblocks)

    my_cipher = DES3.new(key, DES3.MODE_ECB)
    ref_cipher = RefDES3.new(key, RefDES3.MODE_ECB)

    ct_my = my_cipher.encrypt(pt)
    ct_ref = ref_cipher.encrypt(pt)

    assert ct_my == ct_ref


@pytest.mark.parametrize("key_len", [16, 24])
@pytest.mark.parametrize("nblocks", [0, 1, 3, 5, 10])
def test_des3_ecb_decrypt_matches_pycryptodome(key_len: int, nblocks: int):
    key = make_ref_compatible_key(key_len)
    pt = randbytes(8 * nblocks)

    ref_enc = RefDES3.new(key, RefDES3.MODE_ECB)
    ct = ref_enc.encrypt(pt)

    my_dec = DES3.new(key, DES3.MODE_ECB)
    pt_my = my_dec.decrypt(ct)

    assert pt_my == pt


def test_des3_ecb_streaming_equals_one_shot_and_matches_ref():
    key = make_ref_compatible_key(24)
    pt = randbytes(8 * 6)

    my1 = DES3.new(key, DES3.MODE_ECB)
    ct_one_shot = my1.encrypt(pt)

    my2 = DES3.new(key, DES3.MODE_ECB)
    ct_stream = my2.encrypt(pt[: 8 * 2]) + my2.encrypt(pt[8 * 2 :])

    assert ct_stream == ct_one_shot

    ref2 = RefDES3.new(key, RefDES3.MODE_ECB)
    ct_ref_stream = ref2.encrypt(pt[: 8 * 2]) + ref2.encrypt(pt[8 * 2 :])
    assert ct_stream == ct_ref_stream


def test_des3_ecb_multiple_calls_independent():
    key = make_ref_compatible_key(16)
    pt1 = randbytes(8 * 2)
    pt2 = randbytes(8 * 3)

    my = DES3.new(key, DES3.MODE_ECB)
    ref = RefDES3.new(key, RefDES3.MODE_ECB)

    assert my.encrypt(pt1) == ref.encrypt(pt1)
    assert my.encrypt(pt2) == ref.encrypt(pt2)


def test_des3_ecb_rejects_bad_key_size():
    with pytest.raises(ValueError):
        DES3.new(b"", DES3.MODE_ECB)
    with pytest.raises(ValueError):
        DES3.new(b"\x00" * 15, DES3.MODE_ECB)
    with pytest.raises(ValueError):
        DES3.new(b"\x00" * 17, DES3.MODE_ECB)
    with pytest.raises(ValueError):
        DES3.new(b"\x00" * 23, DES3.MODE_ECB)
    with pytest.raises(ValueError):
        DES3.new(b"\x00" * 25, DES3.MODE_ECB)


def test_des3_ecb_rejects_non_block_aligned_data():
    key = make_ref_compatible_key(24)
    my = DES3.new(key, DES3.MODE_ECB)

    with pytest.raises(ValueError):
        my.encrypt(b"\x00" * 7)
    with pytest.raises(ValueError):
        my.decrypt(b"\x00" * 15)
