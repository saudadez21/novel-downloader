from __future__ import annotations

import random

import pytest
from Crypto.Cipher import AES as RefAES

from novel_downloader.libs.crypto.cipher import AES

_rng = random.Random(20251123)


def randbytes(n: int) -> bytes:
    """Deterministic bytes for reproducible tests."""
    return bytes(_rng.randrange(0, 256) for _ in range(n))


@pytest.mark.parametrize("key_len", [16, 24, 32])
@pytest.mark.parametrize("nblocks", [0, 1, 2, 4, 8])
def test_aes_ecb_encrypt_matches_pycryptodome(key_len: int, nblocks: int):
    key = randbytes(key_len)
    pt = randbytes(16 * nblocks)

    my_cipher = AES.new(key, AES.MODE_ECB)
    ref_cipher = RefAES.new(key, RefAES.MODE_ECB)

    ct_my = my_cipher.encrypt(pt)
    ct_ref = ref_cipher.encrypt(pt)

    assert ct_my == ct_ref


@pytest.mark.parametrize("key_len", [16, 24, 32])
@pytest.mark.parametrize("nblocks", [0, 1, 3, 5, 10])
def test_aes_ecb_decrypt_matches_pycryptodome(key_len: int, nblocks: int):
    key = randbytes(key_len)
    pt = randbytes(16 * nblocks)

    ref_enc = RefAES.new(key, RefAES.MODE_ECB)
    ct = ref_enc.encrypt(pt)

    my_dec = AES.new(key, AES.MODE_ECB)
    pt_my = my_dec.decrypt(ct)

    assert pt_my == pt


def test_aes_ecb_streaming_equals_one_shot_and_matches_ref():
    key = randbytes(32)
    pt = randbytes(16 * 6)  # 6 blocks

    # one-shot
    my1 = AES.new(key, AES.MODE_ECB)
    ct_one_shot = my1.encrypt(pt)

    my2 = AES.new(key, AES.MODE_ECB)
    ct_stream = my2.encrypt(pt[: 16 * 2]) + my2.encrypt(pt[16 * 2 :])

    assert ct_stream == ct_one_shot

    ref2 = RefAES.new(key, RefAES.MODE_ECB)
    ct_ref_stream = ref2.encrypt(pt[: 16 * 2]) + ref2.encrypt(pt[16 * 2 :])
    assert ct_stream == ct_ref_stream


def test_aes_ecb_multiple_calls_independent():
    key = randbytes(16)
    pt1 = randbytes(16 * 2)
    pt2 = randbytes(16 * 3)

    my = AES.new(key, AES.MODE_ECB)
    ref = RefAES.new(key, RefAES.MODE_ECB)

    assert my.encrypt(pt1) == ref.encrypt(pt1)
    assert my.encrypt(pt2) == ref.encrypt(pt2)


def test_aes_ecb_rejects_bad_key_size():
    with pytest.raises(ValueError):
        AES.new(b"", AES.MODE_ECB)
    with pytest.raises(ValueError):
        AES.new(b"\x00" * 15, AES.MODE_ECB)
    with pytest.raises(ValueError):
        AES.new(b"\x00" * 17, AES.MODE_ECB)


def test_aes_ecb_rejects_non_block_aligned_data():
    key = randbytes(16)
    my = AES.new(key, AES.MODE_ECB)

    with pytest.raises(ValueError):
        my.encrypt(b"\x00" * 15)
    with pytest.raises(ValueError):
        my.decrypt(b"\x00" * 31)
