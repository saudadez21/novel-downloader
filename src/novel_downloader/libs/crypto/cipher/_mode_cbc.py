#!/usr/bin/env python3
"""
novel_downloader.libs.crypto.cipher._mode_cbc
---------------------------------------------
"""

from __future__ import annotations

from ._mode_base import BaseMode, BlockCipherFunc


def _xor_bytes(a: bytes, b: bytes) -> bytes:
    """XOR two equal-length byte strings."""
    return bytes(x ^ y for x, y in zip(a, b, strict=False))


class CBCMode(BaseMode):
    """
    Cipher Block Chaining (CBC) mode.

    CBC is stateful: each block depends on the previous ciphertext block.
    This instance keeps its chaining value (`iv`) updated after each call.
    """

    def __init__(
        self,
        encrypt_block: BlockCipherFunc,
        decrypt_block: BlockCipherFunc,
        block_size: int,
        iv: bytes | None,
    ) -> None:
        """
        Parameters
        ----------
        encrypt_block, decrypt_block, block_size:
            See BaseMode.

        iv:
            Initialization vector. Must be exactly `block_size` bytes.
            If None, a zero IV is used (useful for tests/learning; not recommended
            for real cryptographic use).
        """
        super().__init__(encrypt_block, decrypt_block, block_size)
        if iv is None:
            iv = bytes(block_size)
        if len(iv) != block_size:
            raise ValueError("Invalid IV size")
        self.iv = bytes(iv)

    def encrypt(self, data: bytes) -> bytes:
        """
        Encrypt data in CBC mode.

        `data` must be a multiple of block size. The internal IV/state will be
        updated to the last ciphertext block after encryption.

        Raises ValueError if length is invalid.
        """
        bs = self.block_size
        if len(data) % bs != 0:
            raise ValueError("Data length not a multiple of block size")

        out = bytearray()
        prev = self.iv

        for i in range(0, len(data), bs):
            block = data[i : i + bs]
            xored = _xor_bytes(block, prev)
            ct = self.encrypt_block(xored)
            out += ct
            prev = ct

        self.iv = prev
        return bytes(out)

    def decrypt(self, data: bytes) -> bytes:
        """
        Decrypt data in CBC mode.

        `data` must be a multiple of block size. The internal IV/state will be
        updated to the last ciphertext block after decryption.

        Raises ValueError if length is invalid.
        """
        bs = self.block_size
        if len(data) % bs != 0:
            raise ValueError("Data length not a multiple of block size")

        out = bytearray()
        prev = self.iv

        for i in range(0, len(data), bs):
            block = data[i : i + bs]
            dec = self.decrypt_block(block)
            pt = _xor_bytes(dec, prev)
            out += pt
            prev = block

        self.iv = prev
        return bytes(out)
