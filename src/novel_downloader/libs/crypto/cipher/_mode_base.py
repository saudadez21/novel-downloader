#!/usr/bin/env python3
"""
novel_downloader.libs.crypto.cipher._mode_base
----------------------------------------------
"""

from abc import ABC, abstractmethod
from collections.abc import Callable

BlockCipherFunc = Callable[[bytes], bytes]


class BaseMode(ABC):
    """
    Base class for block-cipher modes of operation.

    A mode object wraps a *block cipher primitive* (encrypt/decrypt one block)
    and provides streaming encrypt()/decrypt() over arbitrary-length data.
    """

    def __init__(
        self,
        encrypt_block: BlockCipherFunc,
        decrypt_block: BlockCipherFunc,
        block_size: int,
    ) -> None:
        """
        Initialize a mode instance.

        Parameters
        ----------
        encrypt_block:
            Callable that encrypts a single block of length `block_size`.
            Signature: (block: bytes) -> bytes.

        decrypt_block:
            Callable that decrypts a single block of length `block_size`.
            Signature: (block: bytes) -> bytes.

        block_size:
            Block size in bytes (e.g. 16 for AES, 8 for DES).
        """
        self.encrypt_block = encrypt_block
        self.decrypt_block = decrypt_block
        self.block_size = block_size

    @abstractmethod
    def encrypt(self, data: bytes) -> bytes:
        """
        Encrypt plaintext.

        Parameters
        ----------
        data:
            Plaintext bytes. Length must be a multiple of `block_size`
            (no padding is applied here).

        Returns
        -------
        bytes
            Ciphertext bytes of the same length.

        Raises
        ------
        ValueError
            If `len(data)` is not a multiple of `block_size`.
        """
        ...

    @abstractmethod
    def decrypt(self, data: bytes) -> bytes:
        """
        Decrypt ciphertext.

        Parameters
        ----------
        data:
            Ciphertext bytes. Length must be a multiple of `block_size`
            (no unpadding is applied here).

        Returns
        -------
        bytes
            Plaintext bytes of the same length.

        Raises
        ------
        ValueError
            If `len(data)` is not a multiple of `block_size`.
        """
        ...
