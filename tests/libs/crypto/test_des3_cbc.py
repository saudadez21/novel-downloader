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
def test_des3_cbc_encrypt_matches_pycryptodome(key_len: int, nblocks: int):
    key = make_ref_compatible_key(key_len)
    iv = randbytes(8)
    pt = randbytes(8 * nblocks)

    my_cipher = DES3.new(key, DES3.MODE_CBC, iv=iv)
    ref_cipher = RefDES3.new(key, RefDES3.MODE_CBC, iv=iv)

    ct_my = my_cipher.encrypt(pt)
    ct_ref = ref_cipher.encrypt(pt)

    assert ct_my == ct_ref


@pytest.mark.parametrize("key_len", [16, 24])
@pytest.mark.parametrize("nblocks", [0, 1, 3, 5, 10])
def test_des3_cbc_decrypt_matches_pycryptodome(key_len: int, nblocks: int):
    key = make_ref_compatible_key(key_len)
    iv = randbytes(8)
    pt = randbytes(8 * nblocks)

    ref_enc = RefDES3.new(key, RefDES3.MODE_CBC, iv=iv)
    ct = ref_enc.encrypt(pt)

    my_dec = DES3.new(key, DES3.MODE_CBC, iv=iv)
    pt_my = my_dec.decrypt(ct)

    assert pt_my == pt


def test_des3_cbc_streaming_state_matches_pycryptodome():
    """
    CBC is stateful. Encrypting in block-aligned chunks should match one-shot.
    """
    key = make_ref_compatible_key(24)
    iv = randbytes(8)
    pt = randbytes(8 * 6)

    my1 = DES3.new(key, DES3.MODE_CBC, iv=iv)
    ct_one_shot = my1.encrypt(pt)

    my2 = DES3.new(key, DES3.MODE_CBC, iv=iv)
    ct_stream = my2.encrypt(pt[: 8 * 2]) + my2.encrypt(pt[8 * 2 :])

    assert ct_stream == ct_one_shot

    ref2 = RefDES3.new(key, RefDES3.MODE_CBC, iv=iv)
    ct_ref_stream = ref2.encrypt(pt[: 8 * 2]) + ref2.encrypt(pt[8 * 2 :])
    assert ct_stream == ct_ref_stream


def test_des3_cbc_iv_updates_after_encrypt():
    key = make_ref_compatible_key(16)
    iv = randbytes(8)
    pt = randbytes(8 * 3)

    my = DES3.new(key, DES3.MODE_CBC, iv=iv)
    ct = my.encrypt(pt)

    assert hasattr(my, "iv")
    assert my.iv == ct[-8:]


def test_des3_cbc_iv_updates_after_decrypt():
    key = make_ref_compatible_key(16)
    iv = randbytes(8)
    pt = randbytes(8 * 3)

    ref = RefDES3.new(key, RefDES3.MODE_CBC, iv=iv)
    ct = ref.encrypt(pt)

    my = DES3.new(key, DES3.MODE_CBC, iv=iv)
    _ = my.decrypt(ct)

    assert my.iv == ct[-8:]


def test_des3_cbc_rejects_bad_key_size():
    iv = b"\x00" * 8
    with pytest.raises(ValueError):
        DES3.new(b"", DES3.MODE_CBC, iv=iv)
    with pytest.raises(ValueError):
        DES3.new(b"\x00" * 15, DES3.MODE_CBC, iv=iv)
    with pytest.raises(ValueError):
        DES3.new(b"\x00" * 17, DES3.MODE_CBC, iv=iv)
    with pytest.raises(ValueError):
        DES3.new(b"\x00" * 23, DES3.MODE_CBC, iv=iv)
    with pytest.raises(ValueError):
        DES3.new(b"\x00" * 25, DES3.MODE_CBC, iv=iv)


def test_des3_cbc_rejects_bad_iv_size():
    key = make_ref_compatible_key(16)
    with pytest.raises(ValueError):
        DES3.new(key, DES3.MODE_CBC, iv=b"")
    with pytest.raises(ValueError):
        DES3.new(key, DES3.MODE_CBC, iv=b"\x00" * 7)
    with pytest.raises(ValueError):
        DES3.new(key, DES3.MODE_CBC, iv=b"\x00" * 9)


def test_des3_cbc_rejects_non_block_aligned_data():
    key = make_ref_compatible_key(24)
    iv = randbytes(8)
    my = DES3.new(key, DES3.MODE_CBC, iv=iv)

    with pytest.raises(ValueError):
        my.encrypt(b"\x00" * 7)
    with pytest.raises(ValueError):
        my.decrypt(b"\x00" * 15)


def test_des3_cbc_none_iv_defaults_to_zero_iv():
    key = make_ref_compatible_key(24)
    zero_iv = b"\x00" * 8
    pt = randbytes(8 * 4)

    my = DES3.new(key, DES3.MODE_CBC, iv=None)
    ref = RefDES3.new(key, RefDES3.MODE_CBC, iv=zero_iv)

    assert my.encrypt(pt) == ref.encrypt(pt)
