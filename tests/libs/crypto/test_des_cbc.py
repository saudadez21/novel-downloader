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
def test_des_cbc_encrypt_matches_pycryptodome(nblocks: int):
    key = randbytes(8)
    iv = randbytes(8)
    pt = randbytes(8 * nblocks)

    my_cipher = DES.new(key, DES.MODE_CBC, iv=iv)
    ref_cipher = RefDES.new(key, RefDES.MODE_CBC, iv=iv)

    ct_my = my_cipher.encrypt(pt)
    ct_ref = ref_cipher.encrypt(pt)

    assert ct_my == ct_ref


@pytest.mark.parametrize("nblocks", [0, 1, 3, 5, 10])
def test_des_cbc_decrypt_matches_pycryptodome(nblocks: int):
    key = randbytes(8)
    iv = randbytes(8)
    pt = randbytes(8 * nblocks)

    ref_enc = RefDES.new(key, RefDES.MODE_CBC, iv=iv)
    ct = ref_enc.encrypt(pt)

    my_dec = DES.new(key, DES.MODE_CBC, iv=iv)
    pt_my = my_dec.decrypt(ct)

    assert pt_my == pt


def test_des_cbc_streaming_state_matches_pycryptodome():
    """
    CBC is stateful. Encrypting in block-aligned chunks should match one-shot.
    """
    key = randbytes(8)
    iv = randbytes(8)
    pt = randbytes(8 * 6)  # 6 blocks

    # one-shot
    my1 = DES.new(key, DES.MODE_CBC, iv=iv)
    ct_one_shot = my1.encrypt(pt)

    # streaming with same object
    my2 = DES.new(key, DES.MODE_CBC, iv=iv)
    ct_stream = my2.encrypt(pt[: 8 * 2]) + my2.encrypt(pt[8 * 2 :])

    assert ct_stream == ct_one_shot

    # cross-check reference streaming too
    ref2 = RefDES.new(key, RefDES.MODE_CBC, iv=iv)
    ct_ref_stream = ref2.encrypt(pt[: 8 * 2]) + ref2.encrypt(pt[8 * 2 :])
    assert ct_stream == ct_ref_stream


def test_des_cbc_iv_updates_after_encrypt():
    """
    After encryption, CBCMode.iv should equal the last ciphertext block.
    """
    key = randbytes(8)
    iv = randbytes(8)
    pt = randbytes(8 * 3)

    my = DES.new(key, DES.MODE_CBC, iv=iv)
    ct = my.encrypt(pt)

    assert hasattr(my, "iv")
    assert my.iv == ct[-8:]


def test_des_cbc_iv_updates_after_decrypt():
    """
    After decryption, CBCMode.iv should equal the last ciphertext block processed.
    """
    key = randbytes(8)
    iv = randbytes(8)

    ref = RefDES.new(key, RefDES.MODE_CBC, iv=iv)
    pt = randbytes(8 * 3)
    ct = ref.encrypt(pt)

    my = DES.new(key, DES.MODE_CBC, iv=iv)
    _ = my.decrypt(ct)

    assert my.iv == ct[-8:]


def test_des_cbc_rejects_bad_key_size():
    iv = b"\x00" * 8
    with pytest.raises(ValueError):
        DES.new(b"", DES.MODE_CBC, iv=iv)
    with pytest.raises(ValueError):
        DES.new(b"\x00" * 7, DES.MODE_CBC, iv=iv)
    with pytest.raises(ValueError):
        DES.new(b"\x00" * 9, DES.MODE_CBC, iv=iv)


def test_des_cbc_rejects_bad_iv_size():
    key = b"\x00" * 8
    with pytest.raises(ValueError):
        DES.new(key, DES.MODE_CBC, iv=b"")
    with pytest.raises(ValueError):
        DES.new(key, DES.MODE_CBC, iv=b"\x00" * 7)
    with pytest.raises(ValueError):
        DES.new(key, DES.MODE_CBC, iv=b"\x00" * 9)


def test_des_cbc_rejects_non_block_aligned_data():
    key = randbytes(8)
    iv = randbytes(8)
    my = DES.new(key, DES.MODE_CBC, iv=iv)

    with pytest.raises(ValueError):
        my.encrypt(b"\x00" * 7)
    with pytest.raises(ValueError):
        my.decrypt(b"\x00" * 15)


def test_des_cbc_none_iv_defaults_to_zero_iv():
    """
    Your library allows iv=None for CBC and substitutes zero IV.
    PyCryptodome requires IV, so compare to explicit zero IV there.
    """
    key = randbytes(8)
    zero_iv = b"\x00" * 8
    pt = randbytes(8 * 4)

    my = DES.new(key, DES.MODE_CBC, iv=None)
    ref = RefDES.new(key, RefDES.MODE_CBC, iv=zero_iv)

    assert my.encrypt(pt) == ref.encrypt(pt)
