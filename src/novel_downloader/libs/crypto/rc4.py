#!/usr/bin/env python3
"""
novel_downloader.libs.crypto.rc4
--------------------------------

Minimal RC4 stream cipher implementation.
"""


def rc4_init(key: bytes) -> list[int]:
    """
    Key-Scheduling Algorithm (KSA)
    """
    S = list(range(256))
    j = 0
    klen = len(key)
    for i in range(256):
        j = (j + S[i] + key[i % klen]) & 0xFF
        S[i], S[j] = S[j], S[i]
    return S


def rc4_stream(S_init: list[int], data: bytes) -> bytes:
    """
    Pseudo-Random Generation Algorithm (PRGA)
    """
    # make a copy of S since it mutates during PRGA
    S = S_init.copy()
    i = 0
    j = 0
    out = bytearray(len(data))
    for idx, ch in enumerate(data):
        i = (i + 1) & 0xFF
        j = (j + S[i]) & 0xFF
        S[i], S[j] = S[j], S[i]
        K = S[(S[i] + S[j]) & 0xFF]
        out[idx] = ch ^ K

    return bytes(out)


def rc4_cipher(key: bytes, data: bytes) -> bytes:
    """
    RC4 stream cipher.

    It performs the standard Key-Scheduling Algorithm (KSA) and
    Pseudo-Random Generation Algorithm (PRGA) to produce the RC4 keystream.

    :param key: RC4 key as bytes (must not be empty)
    :param data: plaintext or ciphertext as bytes
    :return: XORed bytes (encrypt/decrypt are identical)
    """
    S = rc4_init(key)
    return rc4_stream(S, data)
