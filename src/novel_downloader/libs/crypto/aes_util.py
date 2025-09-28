#!/usr/bin/env python3
"""
novel_downloader.libs.crypto.aes_util
-------------------------------------

AES decrypt functions.
"""

from __future__ import annotations

__all__ = ["aes_cbc_decrypt"]

from typing import Any

_BLOCK = 16
_VALID_KEY_SIZES = (16, 24, 32)


def _as_bytes(name: str, b: Any) -> bytes:
    if isinstance(b, bytes):
        return b
    if isinstance(b, bytearray | memoryview):
        return bytes(b)
    raise TypeError(f"{name} must be bytes-like, got {type(b).__name__}")


def _validate_inputs(key: bytes, iv: bytes, data: bytes) -> None:
    if len(iv) != _BLOCK:
        raise ValueError(f"iv must be {_BLOCK} bytes, got {len(iv)}")
    if len(key) not in _VALID_KEY_SIZES:
        raise ValueError(
            f"key length must be one of {_VALID_KEY_SIZES} bytes, got {len(key)}"
        )
    if len(data) % _BLOCK != 0:
        raise ValueError(
            f"ciphertext length must be a multiple of {_BLOCK} bytes, got {len(data)}"
        )


try:
    from Crypto.Cipher import AES as _PyAES
    from Crypto.Util.Padding import unpad as _py_unpad

    def aes_cbc_decrypt(
        key: bytes,
        iv: bytes,
        data: bytes,
        *,
        unpad: bool = True,
        block_size: int = _BLOCK,
    ) -> bytes:
        """
        AES-CBC decrypt + PKCS#7 unpad (PyCryptodome).

        :param key: AES key (16/24/32 bytes)
        :param iv: Initialization vector (16 bytes)
        :param data: Ciphertext, length multiple of 16
        :return: Plaintext bytes (unpadded)
        :raises TypeError, ValueError: on invalid inputs
        """
        key_b = _as_bytes("key", key)
        iv_b = _as_bytes("iv", iv)
        data_b = _as_bytes("data", data)
        if not data_b:
            return b""
        _validate_inputs(key_b, iv_b, data_b)
        pt = _PyAES.new(key_b, _PyAES.MODE_CBC, iv_b).decrypt(data_b)
        return _py_unpad(pt, block_size, style="pkcs7") if unpad else pt  # type: ignore[no-any-return]

except ImportError:
    print(
        "crypto_utils: Falling back to pure-Python AES_CBC.\n"
        "Tip: `pip install pycryptodome` for ~800x faster speed."
    )
    from .aes_v2 import AES_CBC

    def aes_cbc_decrypt(
        key: bytes,
        iv: bytes,
        data: bytes,
        *,
        unpad: bool = True,
        block_size: int = _BLOCK,
    ) -> bytes:
        """
        AES-CBC decrypt + PKCS#7 unpad (handled by AES_CBC internally).

        :param key: AES key (16/24/32 bytes)
        :param iv: Initialization vector (16 bytes)
        :param data: Ciphertext, length multiple of 16
        :return: Plaintext bytes (unpadded)
        :raises TypeError, ValueError: on invalid inputs
        """
        key_b = _as_bytes("key", key)
        iv_b = _as_bytes("iv", iv)
        data_b = _as_bytes("data", data)
        if not data_b:
            return b""
        _validate_inputs(key_b, iv_b, data_b)
        return (
            AES_CBC(key_b, iv_b).decrypt_padded(data_b, block_size)
            if unpad
            else AES_CBC(key_b, iv_b).decrypt(data_b)
        )
