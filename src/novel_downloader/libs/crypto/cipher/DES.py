#!/usr/bin/env python3
"""
novel_downloader.libs.crypto.cipher.DES
---------------------------------------
"""

from __future__ import annotations

from ._mode_base import BaseMode

block_size = 8
key_size = (8,)

MODE_ECB = 1  #: Electronic Code Book
MODE_CBC = 2  #: Cipher-Block Chaining

# fmt: off
IP = [
    58, 50, 42, 34, 26, 18, 10, 2,
    60, 52, 44, 36, 28, 20, 12, 4,
    62, 54, 46, 38, 30, 22, 14, 6,
    64, 56, 48, 40, 32, 24, 16, 8,
    57, 49, 41, 33, 25, 17, 9,  1,
    59, 51, 43, 35, 27, 19, 11, 3,
    61, 53, 45, 37, 29, 21, 13, 5,
    63, 55, 47, 39, 31, 23, 15, 7,
]

FP = [
    40, 8, 48, 16, 56, 24, 64, 32,
    39, 7, 47, 15, 55, 23, 63, 31,
    38, 6, 46, 14, 54, 22, 62, 30,
    37, 5, 45, 13, 53, 21, 61, 29,
    36, 4, 44, 12, 52, 20, 60, 28,
    35, 3, 43, 11, 51, 19, 59, 27,
    34, 2, 42, 10, 50, 18, 58, 26,
    33, 1, 41, 9,  49, 17, 57, 25,
]

E = [
    32, 1,  2,  3,  4,  5,
    4,  5,  6,  7,  8,  9,
    8,  9,  10, 11, 12, 13,
    12, 13, 14, 15, 16, 17,
    16, 17, 18, 19, 20, 21,
    20, 21, 22, 23, 24, 25,
    24, 25, 26, 27, 28, 29,
    28, 29, 30, 31, 32, 1,
]

P = [
    16, 7,  20, 21,
    29, 12, 28, 17,
    1,  15, 23, 26,
    5,  18, 31, 10,
    2,  8,  24, 14,
    32, 27, 3,  9,
    19, 13, 30, 6,
    22, 11, 4,  25,
]

PC1 = [
    57, 49, 41, 33, 25, 17, 9,
    1,  58, 50, 42, 34, 26, 18,
    10, 2,  59, 51, 43, 35, 27,
    19, 11, 3,  60, 52, 44, 36,
    63, 55, 47, 39, 31, 23, 15,
    7,  62, 54, 46, 38, 30, 22,
    14, 6,  61, 53, 45, 37, 29,
    21, 13, 5,  28, 20, 12, 4,
]

PC2 = [
    14, 17, 11, 24, 1,  5,
    3,  28, 15, 6,  21, 10,
    23, 19, 12, 4,  26, 8,
    16, 7,  27, 20, 13, 2,
    41, 52, 31, 37, 47, 55,
    30, 40, 51, 45, 33, 48,
    44, 49, 39, 56, 34, 53,
    46, 42, 50, 36, 29, 32,
]

SHIFTS = [1, 1, 2, 2, 2, 2, 2, 2, 1, 2, 2, 2, 2, 2, 2, 1]

SBOXES = [
    # S1
    [
        [14, 4,  13, 1,  2,  15, 11, 8,  3,  10, 6,  12, 5,  9,  0,  7],
        [0,  15, 7,  4,  14, 2,  13, 1,  10, 6,  12, 11, 9,  5,  3,  8],
        [4,  1,  14, 8,  13, 6,  2,  11, 15, 12, 9,  7,  3,  10, 5,  0],
        [15, 12, 8,  2,  4,  9,  1,  7,  5,  11, 3,  14, 10, 0,  6,  13],
    ],
    # S2
    [
        [15, 1,  8,  14, 6,  11, 3,  4,  9,  7,  2,  13, 12, 0,  5,  10],
        [3,  13, 4,  7,  15, 2,  8,  14, 12, 0,  1,  10, 6,  9,  11, 5],
        [0,  14, 7,  11, 10, 4,  13, 1,  5,  8,  12, 6,  9,  3,  2,  15],
        [13, 8,  10, 1,  3,  15, 4,  2,  11, 6,  7,  12, 0,  5,  14, 9],
    ],
    # S3
    [
        [10, 0,  9,  14, 6,  3,  15, 5,  1,  13, 12, 7,  11, 4,  2,  8],
        [13, 7,  0,  9,  3,  4,  6,  10, 2,  8,  5,  14, 12, 11, 15, 1],
        [13, 6,  4,  9,  8,  15, 3,  0,  11, 1,  2,  12, 5,  10, 14, 7],
        [1,  10, 13, 0,  6,  9,  8,  7,  4,  15, 14, 3,  11, 5,  2,  12],
    ],
    # S4
    [
        [7,  13, 14, 3,  0,  6,  9,  10, 1,  2,  8,  5,  11, 12, 4,  15],
        [13, 8,  11, 5,  6,  15, 0,  3,  4,  7,  2,  12, 1,  10, 14, 9],
        [10, 6,  9,  0,  12, 11, 7,  13, 15, 1,  3,  14, 5,  2,  8,  4],
        [3,  15, 0,  6,  10, 1,  13, 8,  9,  4,  5,  11, 12, 7,  2,  14],
    ],
    # S5
    [
        [2,  12, 4,  1,  7,  10, 11, 6,  8,  5,  3,  15, 13, 0,  14, 9],
        [14, 11, 2,  12, 4,  7,  13, 1,  5,  0,  15, 10, 3,  9,  8,  6],
        [4,  2,  1,  11, 10, 13, 7,  8,  15, 9,  12, 5,  6,  3,  0,  14],
        [11, 8,  12, 7,  1,  14, 2,  13, 6,  15, 0,  9,  10, 4,  5,  3],
    ],
    # S6
    [
        [12, 1,  10, 15, 9,  2,  6,  8,  0,  13, 3,  4,  14, 7,  5,  11],
        [10, 15, 4,  2,  7,  12, 9,  5,  6,  1,  13, 14, 0,  11, 3,  8],
        [9,  14, 15, 5,  2,  8,  12, 3,  7,  0,  4,  10, 1,  13, 11, 6],
        [4,  3,  2,  12, 9,  5,  15, 10, 11, 14, 1,  7,  6,  0,  8,  13],
    ],
    # S7
    [
        [4,  11, 2,  14, 15, 0,  8,  13, 3,  12, 9,  7,  5,  10, 6,  1],
        [13, 0,  11, 7,  4,  9,  1,  10, 14, 3,  5,  12, 2,  15, 8,  6],
        [1,  4,  11, 13, 12, 3,  7,  14, 10, 15, 6,  8,  0,  5,  9,  2],
        [6,  11, 13, 8,  1,  4,  10, 7,  9,  5,  0,  15, 14, 2,  3,  12],
    ],
    # S8
    [
        [13, 2,  8,  4,  6,  15, 11, 1,  10, 9,  3,  14, 5,  0,  12, 7],
        [1,  15, 13, 8,  10, 3,  7,  4,  12, 5,  6,  11, 0,  14, 9,  2],
        [7,  11, 4,  1,  9,  12, 14, 2,  0,  6,  10, 13, 15, 3,  5,  8],
        [2,  1,  14, 7,  4,  10, 8,  13, 15, 12, 9,  0,  3,  5,  6,  11],
    ],
]
# fmt: on


def _bytes_to_int(b: bytes) -> int:
    return int.from_bytes(b, "big")


def _int_to_bytes(x: int, length: int) -> bytes:
    return x.to_bytes(length, "big")


def _permute(x: int, table: list[int], in_bits: int) -> int:
    """
    Apply a DES permutation table.

    `table` contains 1-based bit positions from the input.
    Bits are read MSB-first.
    """
    out = 0
    for pos in table:
        out = (out << 1) | ((x >> (in_bits - pos)) & 1)
    return out


def _rotl28(x: int, n: int) -> int:
    """Left-rotate a 28-bit value."""
    return ((x << n) & 0x0FFFFFFF) | (x >> (28 - n))


def _feistel(r: int, subkey: int) -> int:
    """
    DES Feistel function f(R, K).

    r: 32-bit int
    subkey: 48-bit int
    returns 32-bit int
    """
    # Expansion 32 -> 48
    e = _permute(r, E, 32)  # 48 bits
    x = e ^ subkey

    # S-boxes: 8 chunks of 6 bits -> 4 bits each
    out32 = 0
    for i in range(8):
        chunk = (x >> (42 - 6 * i)) & 0x3F
        row = ((chunk & 0x20) >> 4) | (chunk & 0x01)
        col = (chunk >> 1) & 0x0F
        s = SBOXES[i][row][col]
        out32 = (out32 << 4) | s

    # Permutation P
    return _permute(out32, P, 32)


def _make_subkeys(key8: bytes) -> list[int]:
    """
    Generate 16 48-bit subkeys from a 64-bit (8-byte) DES key.
    Parity bits are ignored (learning-friendly).
    """
    key64 = _bytes_to_int(key8)
    # PC-1: 64 -> 56
    key56 = _permute(key64, PC1, 64)
    c = (key56 >> 28) & 0x0FFFFFFF
    d = key56 & 0x0FFFFFFF

    subkeys: list[int] = []
    for shift in SHIFTS:
        c = _rotl28(c, shift)
        d = _rotl28(d, shift)
        cd = (c << 28) | d
        k48 = _permute(cd, PC2, 56)
        subkeys.append(k48)
    return subkeys


class _DESContext:
    """
    Internal DES core:
    - key expansion
    - single-block encrypt/decrypt (8 bytes)
    """

    __slots__ = ("_subkeys",)

    def __init__(self, key: bytes) -> None:
        if len(key) != 8:
            raise ValueError("Invalid key size")
        self._subkeys = _make_subkeys(key)

    def encrypt_block(self, plaintext: bytes) -> bytes:
        if len(plaintext) != 8:
            raise ValueError("Plaintext block must be 8 bytes")
        return self._crypt_block(plaintext, decrypt=False)

    def decrypt_block(self, ciphertext: bytes) -> bytes:
        if len(ciphertext) != 8:
            raise ValueError("Ciphertext block must be 8 bytes")
        return self._crypt_block(ciphertext, decrypt=True)

    def _crypt_block(self, block: bytes, decrypt: bool) -> bytes:
        x64 = _bytes_to_int(block)

        # Initial permutation (IP)
        ip = _permute(x64, IP, 64)

        left = (ip >> 32) & 0xFFFFFFFF
        right = ip & 0xFFFFFFFF

        keys = self._subkeys[::-1] if decrypt else self._subkeys

        for k in keys:
            left, right = right, left ^ _feistel(right, k)

        # Preoutput is R16 || L16 (swap)
        preout = (right << 32) | left

        # Final permutation (FP)
        fp = _permute(preout, FP, 64)
        return _int_to_bytes(fp, 8)


def new(
    key: bytes | bytearray,
    mode: int,
    iv: bytes | bytearray | None = None,
) -> BaseMode:
    """
    Create a new DES cipher object in the requested mode.

    Parameters
    ----------
    key:
        DES key, exactly 8 bytes. Parity bits are not checked.

    mode:
        MODE_ECB or MODE_CBC.

    iv:
        Required for CBC. Must be 8 bytes.
        If None and CBC is selected, a zero IV is used (learning/testing aid).

    Returns
    -------
    BaseMode:
        A mode object with encrypt()/decrypt().

    Raises
    ------
    ValueError:
        If key length, IV length, or mode is invalid.
    """
    ctx = _DESContext(bytes(key))
    encrypt_block = ctx.encrypt_block
    decrypt_block = ctx.decrypt_block

    if mode == MODE_ECB:
        from ._mode_ecb import ECBMode

        return ECBMode(encrypt_block, decrypt_block, block_size)

    if mode == MODE_CBC:
        from ._mode_cbc import CBCMode

        return CBCMode(
            encrypt_block,
            decrypt_block,
            block_size,
            None if iv is None else bytes(iv),
        )

    raise ValueError("Unknown mode")
