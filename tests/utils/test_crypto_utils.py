#!/usr/bin/env python3
"""
tests.utils.test_crypto_utils
-----------------------------
"""


import pytest

import novel_downloader.utils.crypto_utils as cu


def test_rc4_crypt_roundtrip():
    """Encrypting then decrypting returns the original string."""
    key = "s3cr3t"
    data = "The quick brown fox"
    encrypted = cu.rc4_crypt(key, data, mode="encrypt")
    assert isinstance(encrypted, str)
    decrypted = cu.rc4_crypt(key, encrypted, mode="decrypt")
    assert decrypted == data


def test_rc4_crypt_invalid_mode():
    """Passing an invalid mode raises ValueError."""
    with pytest.raises(ValueError) as exc:
        cu.rc4_crypt("k", "d", mode="foo")
    assert "Mode must be 'encrypt' or 'decrypt'" in str(exc.value)
