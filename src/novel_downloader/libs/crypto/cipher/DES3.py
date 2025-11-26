#!/usr/bin/env python3
"""
novel_downloader.libs.crypto.cipher.DES3
----------------------------------------
"""

from __future__ import annotations

from ._mode_base import BaseMode
from .DES import _DESContext

block_size = 8
key_size = (16, 24)

MODE_ECB = 1  #: Electronic Code Book
MODE_CBC = 2  #: Cipher-Block Chaining


class _DES3Context:
    """
    Internal Triple-DES (3DES / TDES) primitive.

    Construction: EDE (Encrypt-Decrypt-Encrypt)
      - Encryption:  E_K1( D_K2( E_K3( block ) ) )
      - Decryption:  D_K3( E_K2( D_K1( block ) ) )

    Keying options:
      - 16-byte key: K1 || K2, with K3 = K1  (2-key 3DES)
      - 24-byte key: K1 || K2 || K3          (3-key 3DES)
    """

    __slots__ = ("_k1", "_k2", "_k3")

    def __init__(self, key: bytes) -> None:
        if len(key) not in key_size:
            raise ValueError("Invalid key size")

        if len(key) == 16:
            k1 = key[:8]
            k2 = key[8:16]
            k3 = k1
        else:  # 24
            k1 = key[:8]
            k2 = key[8:16]
            k3 = key[16:24]

        self._k1 = _DESContext(k1)
        self._k2 = _DESContext(k2)
        self._k3 = _DESContext(k3)

    def encrypt_block(self, plaintext: bytes) -> bytes:
        """
        Encrypt exactly one 8-byte block with 3DES (EDE).
        """
        if len(plaintext) != 8:
            raise ValueError("Plaintext block must be 8 bytes")

        x = self._k1.encrypt_block(plaintext)
        x = self._k2.decrypt_block(x)
        x = self._k3.encrypt_block(x)
        return x

    def decrypt_block(self, ciphertext: bytes) -> bytes:
        """
        Decrypt exactly one 8-byte block with 3DES (DED).
        """
        if len(ciphertext) != 8:
            raise ValueError("Ciphertext block must be 8 bytes")

        x = self._k3.decrypt_block(ciphertext)
        x = self._k2.encrypt_block(x)
        x = self._k1.decrypt_block(x)
        return x


def new(
    key: bytes | bytearray,
    mode: int,
    iv: bytes | bytearray | None = None,
) -> BaseMode:
    """
    Create a new DES3 cipher object in the requested mode.

    Parameters
    ----------
    key:
        Triple-DES key. Must be 16 bytes (2-key 3DES)
        or 24 bytes (3-key 3DES).

    mode:
        MODE_ECB or MODE_CBC.

    iv:
        Initialization vector for CBC. Must be 8 bytes.
        If None and CBC is selected, a zero IV is used
        (learning/testing aid; not recommended for real security).

    Returns
    -------
    BaseMode:
        A mode object implementing encrypt()/decrypt().

    Raises
    ------
    ValueError:
        If key length is invalid, mode is unknown, or IV length is invalid.
    """
    ctx = _DES3Context(bytes(key))
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
