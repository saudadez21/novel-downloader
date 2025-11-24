#!/usr/bin/env python3
"""
novel_downloader.libs.crypto.cipher._mode_ecb
---------------------------------------------
"""

from __future__ import annotations

from ._mode_base import BaseMode, BlockCipherFunc


class ECBMode(BaseMode):
    """
    Electronic Code Book (ECB) mode.

    ECB is stateless: each block is encrypted/decrypted independently.
    """

    def __init__(
        self,
        encrypt_block: BlockCipherFunc,
        decrypt_block: BlockCipherFunc,
        block_size: int,
    ) -> None:
        """
        Parameters
        ----------
        encrypt_block, decrypt_block, block_size:
            See BaseMode.
        """
        super().__init__(encrypt_block, decrypt_block, block_size)

    def encrypt(self, data: bytes) -> bytes:
        """
        Encrypt data in ECB mode.

        Parameters
        ----------
        data:
            Plaintext bytes. Length must be a multiple of `block_size`.

        Returns
        -------
        bytes
            Ciphertext bytes of the same length.

        Raises
        ------
        ValueError
            If `len(data)` is not a multiple of `block_size`.
        """
        bs = self.block_size
        if len(data) % bs != 0:
            raise ValueError("Data length not a multiple of block size")

        out = bytearray()
        for i in range(0, len(data), bs):
            out += self.encrypt_block(data[i : i + bs])
        return bytes(out)

    def decrypt(self, data: bytes) -> bytes:
        """
        Decrypt data in ECB mode.

        Parameters
        ----------
        data:
            Ciphertext bytes. Length must be a multiple of `block_size`.

        Returns
        -------
        bytes
            Plaintext bytes of the same length.

        Raises
        ------
        ValueError
            If `len(data)` is not a multiple of `block_size`.
        """
        bs = self.block_size
        if len(data) % bs != 0:
            raise ValueError("Data length not a multiple of block size")

        out = bytearray()
        for i in range(0, len(data), bs):
            out += self.decrypt_block(data[i : i + bs])
        return bytes(out)
