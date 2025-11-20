import pytest
from novel_downloader.libs.crypto.rc4 import (
    rc4_cipher,
    rc4_init,
    rc4_stream,
)


# ------------------------------------------------------
# rc4_init tests
# ------------------------------------------------------
def test_rc4_init_basic():
    key = b"Key"
    S = rc4_init(key)

    # RC4 state must be 256 bytes
    assert len(S) == 256

    # Must be permutation of 0-255
    assert sorted(S) == list(range(256))

    # Deterministic
    assert rc4_init(key) == S


def test_rc4_init_empty_key():
    """Empty key -> modulo zero error (current behavior)."""
    with pytest.raises(ZeroDivisionError):
        rc4_init(b"")


# ------------------------------------------------------
# rc4_stream tests
# ------------------------------------------------------
def test_rc4_stream_no_mutation_of_input_state():
    key = b"Test"
    S1 = rc4_init(key)
    S2 = S1.copy()

    rc4_stream(S1, b"abc")

    # rc4_stream must NOT mutate the given S_init
    assert S1 == S2


def test_rc4_stream_empty_data():
    S = rc4_init(b"abc")
    assert rc4_stream(S, b"") == b""


# ------------------------------------------------------
# rc4_cipher basic property: encrypt -> decrypt
# ------------------------------------------------------
def test_rc4_encrypt_decrypt_roundtrip():
    key = b"secret"
    data = b"hello world"

    encrypted = rc4_cipher(key, data)
    decrypted = rc4_cipher(key, encrypted)

    assert decrypted == data


# ------------------------------------------------------
# Official test vectors (RFC 6229)
# ------------------------------------------------------

# Test Vector 1 from RFC 6229: key = 0x01 0x02 ... 0x05
KEY1 = bytes([1, 2, 3, 4, 5])
# First 16 bytes of RC4 keystream for KEY1
RFC_VECTOR1 = bytes.fromhex(
    "B2 39 63 05 F0 3D C0 27 CC C3 52 4A 0A 11 18 A8".replace(" ", "")
)


def test_rc4_rfc6229_vector1():
    key = KEY1
    S = rc4_init(key)

    # Run PRGA for 16 bytes of zero input -> output is keystream
    output = rc4_stream(S, b"\x00" * 16)
    assert output == RFC_VECTOR1


# Example plaintext xor test
def test_rc4_rfc6229_encrypt_demo():
    key = KEY1
    plaintext = b"1234567890abcdef"  # 16 bytes
    keystream = RFC_VECTOR1
    expected_cipher = bytes([p ^ k for p, k in zip(plaintext, keystream, strict=False)])

    assert rc4_cipher(key, plaintext) == expected_cipher
