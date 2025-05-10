"""
novel_downloader.utils.crypto_utils
-----------------------------------

Generic cryptographic utilities
"""

from __future__ import annotations

import base64
import hashlib
import json
import random
import time
from typing import Any, Dict, List


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
        out: List[int] = []
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


def _get_key() -> str:
    encoded = "Lj1qYxMuaXBjMg=="
    decoded = base64.b64decode(encoded)
    key = "".join([chr(b ^ 0x5A) for b in decoded])
    return key


def _d(b64str: str) -> str:
    return base64.b64decode(b64str).decode()


def patch_qd_payload_token(
    enc_token: str,
    new_uri: str,
    *,
    key: str = "",
) -> str:
    """
    Patch a timestamp-bearing token with fresh timing and checksum info.

    :param enc_token: Encrypted token string from a live request.
    :type enc_token: str
    :param new_uri: URI used in checksum generation.
    :type new_uri: str
    :param key: RC4 key extracted from front-end JavaScript (optional).
    :type key: str, optional

    :return: Updated token with new timing and checksum values.
    :rtype: str
    """
    if not key:
        key = _get_key()

    # Step 1 – decrypt --------------------------------------------------
    decrypted_json: str = rc4_crypt(key, enc_token, mode="decrypt")
    payload: Dict[str, Any] = json.loads(decrypted_json)

    # Step 2 – rebuild timing fields -----------------------------------
    loadts = int(time.time() * 1000)  # ms since epoch
    # Simulate the JS duration: N(600, 150)  pushed into [300, 1000]
    duration = max(300, min(1000, int(random.normalvariate(600, 150))))
    timestamp = loadts + duration

    # Step 3 – recalculate ------------------------------------
    fp_key = _d("ZmluZ2VycHJpbnQ=")
    ab_key = _d("YWJub3JtYWw=")
    ck_key = _d("Y2hlY2tzdW0=")
    lt_key = _d("bG9hZHRz")
    ts_key = _d("dGltZXN0YW1w")

    fp_val = payload.get(fp_key, "")
    ab_val = payload.get(ab_key, "0" * 32)
    comb = f"{new_uri}{loadts}{fp_val}"
    ck_val = hashlib.md5(comb.encode("utf-8")).hexdigest()

    new_payload = {
        lt_key: loadts,
        ts_key: timestamp,
        fp_key: fp_val,
        ab_key: ab_val,
        ck_key: ck_val,
    }

    # Step 4 – encrypt and return --------------------------------------
    return rc4_crypt(
        key, json.dumps(new_payload, separators=(",", ":")), mode="encrypt"
    )
