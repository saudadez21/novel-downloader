from __future__ import annotations

import random

import pytest
from Crypto.Cipher import DES as RefDES

from novel_downloader.libs.crypto.cipher import DES

_rng = random.Random(20251123)


def randbytes(n: int) -> bytes:
    """Deterministic bytes for reproducible tests."""
    return bytes(_rng.randrange(0, 256) for _ in range(n))


@pytest.mark.parametrize("nblocks", [0, 1, 2, 4, 8, 16])
def test_des_ecb_encrypt_matches_pycryptodome(nblocks: int):
    key = randbytes(8)
    pt = randbytes(8 * nblocks)

    my_cipher = DES.new(key, DES.MODE_ECB)
    ref_cipher = RefDES.new(key, RefDES.MODE_ECB)

    ct_my = my_cipher.encrypt(pt)
    ct_ref = ref_cipher.encrypt(pt)

    assert ct_my == ct_ref


@pytest.mark.parametrize("nblocks", [0, 1, 3, 5, 10])
def test_des_ecb_decrypt_matches_pycryptodome(nblocks: int):
    key = randbytes(8)
    pt = randbytes(8 * nblocks)

    ref_enc = RefDES.new(key, RefDES.MODE_ECB)
    ct = ref_enc.encrypt(pt)

    my_dec = DES.new(key, DES.MODE_ECB)
    pt_my = my_dec.decrypt(ct)

    assert pt_my == pt


def test_des_ecb_streaming_equals_one_shot_and_matches_ref():
    """
    ECB is stateless. Encrypting in block-aligned chunks
    should match one-shot encryption.
    """
    key = randbytes(8)
    pt = randbytes(8 * 6)  # 6 blocks

    # one-shot
    my1 = DES.new(key, DES.MODE_ECB)
    ct_one_shot = my1.encrypt(pt)

    # streaming with same object
    my2 = DES.new(key, DES.MODE_ECB)
    ct_stream = my2.encrypt(pt[: 8 * 2]) + my2.encrypt(pt[8 * 2 :])

    assert ct_stream == ct_one_shot

    # reference streaming
    ref2 = RefDES.new(key, RefDES.MODE_ECB)
    ct_ref_stream = ref2.encrypt(pt[: 8 * 2]) + ref2.encrypt(pt[8 * 2 :])
    assert ct_stream == ct_ref_stream


def test_des_ecb_multiple_calls_independent():
    """
    ECB keeps no chaining state, so multiple calls should be independent.
    """
    key = randbytes(8)
    pt1 = randbytes(8 * 2)
    pt2 = randbytes(8 * 3)

    my = DES.new(key, DES.MODE_ECB)
    ref = RefDES.new(key, RefDES.MODE_ECB)

    assert my.encrypt(pt1) == ref.encrypt(pt1)
    assert my.encrypt(pt2) == ref.encrypt(pt2)


def test_des_ecb_rejects_bad_key_size():
    with pytest.raises(ValueError):
        DES.new(b"", DES.MODE_ECB)
    with pytest.raises(ValueError):
        DES.new(b"\x00" * 7, DES.MODE_ECB)
    with pytest.raises(ValueError):
        DES.new(b"\x00" * 9, DES.MODE_ECB)


def test_des_ecb_rejects_non_block_aligned_data():
    key = randbytes(8)
    my = DES.new(key, DES.MODE_ECB)

    with pytest.raises(ValueError):
        my.encrypt(b"\x00" * 7)
    with pytest.raises(ValueError):
        my.decrypt(b"\x00" * 15)
