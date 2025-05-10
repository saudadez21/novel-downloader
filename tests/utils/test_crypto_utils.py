#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests.utils.test_crypto_utils
-----------------------------
"""

import hashlib
import json

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


def test__get_key_and__d():
    """_get_key returns a string and _d decodes base64 correctly."""
    key = cu._get_key()
    assert isinstance(key, str)
    # Test _d with a known base64 string
    assert cu._d("dGVzdA==") == "test"


def test_patch_qd_payload_token_without_explicit_key(monkeypatch):
    """
    If you don't pass `key`, patch_qd_payload_token must call _get_key() itself.
    We verify it produces the same result as when passing _get_key() explicitly.
    """
    # freeze time and randomness
    monkeypatch.setattr(cu.time, "time", lambda: 2_000.0)
    monkeypatch.setattr(cu.random, "normalvariate", lambda mu, sigma: 600)

    # prepare initial payload and encrypt with default key
    fp_key = cu._d("ZmluZ2VycHJpbnQ=")
    ab_key = cu._d("YWJub3JtYWw=")
    initial = {fp_key: "V1", ab_key: "V2"}
    key = cu._get_key()
    init_json = json.dumps(initial, separators=(",", ":"))
    enc_token = cu.rc4_crypt(key, init_json, mode="encrypt")

    new_uri = "/foo/bar"
    # first call without providing key
    out1 = cu.patch_qd_payload_token(enc_token, new_uri)
    # then call with explicit key
    out2 = cu.patch_qd_payload_token(enc_token, new_uri, key=key)

    # they should be identical
    assert out1 == out2

    # decrypt and check fields
    dec = cu.rc4_crypt(key, out1, mode="decrypt")
    payload = json.loads(dec)
    assert payload[cu._d("bG9hZHRz")] == int(2_000.0 * 1000)
    assert payload[cu._d("YWJub3JtYWw=")] == "V2"
    # checksum matches same logic as earlier test
    comb = f"{new_uri}{int(2_000.0*1000)}V1"
    expected_ck = hashlib.md5(comb.encode("utf-8")).hexdigest()
    assert payload[cu._d("Y2hlY2tzdW0=")] == expected_ck


def test_patch_qd_payload_token(monkeypatch):
    """
    patch_qd_payload_token should:
    - decrypt the given token
    - inject fresh loadts and timestamp
    - compute the checksum correctly
    - re-encrypt and produce a valid token
    """
    # 1. Freeze time and randomness
    monkeypatch.setattr(cu.time, "time", lambda: 1_000.0)
    monkeypatch.setattr(cu.random, "normalvariate", lambda mu, sigma: 600)

    # 2. Prepare an initial payload and encrypt it
    fp_key = cu._d("ZmluZ2VycHJpbnQ=")
    ab_key = cu._d("YWJub3JtYWw=")
    initial = {fp_key: "FPVAL", ab_key: "ABVAL"}
    key = cu._get_key()
    init_json = json.dumps(initial, separators=(",", ":"))
    enc_token = cu.rc4_crypt(key, init_json, mode="encrypt")

    # 3. Call patch_qd_payload_token
    new_uri = "/test/uri"
    new_enc = cu.patch_qd_payload_token(enc_token, new_uri, key=key)

    # 4. Decrypt the result and parse
    dec = cu.rc4_crypt(key, new_enc, mode="decrypt")
    out = json.loads(dec)

    # 5. Compute expected values
    loadts = int(1_000.0 * 1000)
    duration = max(300, min(1000, int(600)))
    timestamp = loadts + duration
    comb = f"{new_uri}{loadts}{initial[fp_key]}"
    expected_ck = hashlib.md5(comb.encode("utf-8")).hexdigest()

    lt_key = cu._d("bG9hZHRz")
    ts_key = cu._d("dGltZXN0YW1w")
    ck_key = cu._d("Y2hlY2tzdW0=")

    # 6. Assert the patched payload
    assert out[lt_key] == loadts
    assert out[ts_key] == timestamp
    assert out[fp_key] == "FPVAL"
    assert out[ab_key] == "ABVAL"
    assert out[ck_key] == expected_ck
