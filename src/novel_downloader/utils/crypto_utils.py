#!/usr/bin/env python3
"""
novel_downloader.utils.crypto_utils
-----------------------------------

Generic cryptographic utilities
"""

from __future__ import annotations

import base64


def rc4_crypt(
    key: str,
    data: str,
    *,
    mode: str = "encrypt",
    encoding: str = "utf-8",
) -> str:
    """
    Encrypt or decrypt data using RC4 and Base64.

    :param key: RC4 key (will be encoded using the specified encoding).
    :type key: str
    :param data: Plain-text (for 'encrypt') or Base64 cipher-text (for 'decrypt').
    :type data: str
    :param mode: Operation mode, either 'encrypt' or 'decrypt'. Defaults to 'encrypt'.
    :type mode: str, optional
    :param encoding: Character encoding for key and returned string. Defaults 'utf-8'.
    :type encoding: str, optional

    :return: Base64 cipher-text (for encryption) or decoded plain-text (for decryption).
    :rtype: str

    :raises ValueError: If mode is not 'encrypt' or 'decrypt'.
    """

    def _rc4(key_bytes: bytes, data_bytes: bytes) -> bytes:
        # Key-Scheduling Algorithm (KSA)
        S = list(range(256))
        j = 0
        for i in range(256):
            j = (j + S[i] + key_bytes[i % len(key_bytes)]) % 256
            S[i], S[j] = S[j], S[i]

        # Pseudo-Random Generation Algorithm (PRGA)
        i = j = 0
        out: list[int] = []
        for char in data_bytes:
            i = (i + 1) % 256
            j = (j + S[i]) % 256
            S[i], S[j] = S[j], S[i]
            K = S[(S[i] + S[j]) % 256]
            out.append(char ^ K)

        return bytes(out)

    key_bytes = key.encode(encoding)

    if mode == "encrypt":
        plain_bytes = data.encode(encoding)
        cipher_bytes = _rc4(key_bytes, plain_bytes)
        return base64.b64encode(cipher_bytes).decode(encoding)

    if mode == "decrypt":
        cipher_bytes = base64.b64decode(data)
        plain_bytes = _rc4(key_bytes, cipher_bytes)
        return plain_bytes.decode(encoding, errors="replace")

    raise ValueError("Mode must be 'encrypt' or 'decrypt'.")
