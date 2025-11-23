#!/usr/bin/env python3
"""
novel_downloader.plugins.utils.ciweimao.my_encryt_extend
--------------------------------------------------------
"""

import base64

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad


def my_decrypt(content: str, keys: list[str], access_key: str) -> str:
    """
    Python version of the ciweimao myDecrypt function.

    :param content: base64 encoded encrypted content
    :param keys: list of base64-encoded AES keys
    :param access_key: string used to derive which keys to pick
    :return: decrypted plaintext string
    """
    if not keys:
        raise ValueError("keys must not be empty")

    o = list(access_key)
    m = len(o)
    t = len(keys)
    if not o:
        raise ValueError("access_key must not be empty")

    selected_keys = [keys[ord(o[m - 1]) % t], keys[ord(o[0]) % t]]

    for k in selected_keys:
        raw = base64.b64decode(content)
        key = base64.b64decode(k)
        iv = raw[:16]
        text = raw[16:]

        decoded = AES.new(key, AES.MODE_CBC, iv).decrypt(text)
        decoded = unpad(decoded, AES.block_size)

        content = decoded.decode("utf-8")

    return content
