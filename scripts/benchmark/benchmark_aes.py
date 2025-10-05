#!/usr/bin/env python3
import os
import random
import string
import timeit

from Crypto.Cipher import AES as PyAES

# from novel_downloader.libs.crypto.aes_v1 import AES_CBC
from novel_downloader.libs.crypto.aes_v2 import AES_CBC

# =======================
# Configuration constants
# =======================
KEY_SIZES = (16, 24, 32)  # AES key sizes in bytes
VERIFY_ROUNDS = 10
TEXT_TEST_SIZE = 3000
BENCHMARK_ROUNDS = 10
BENCHMARK_OPS = 100
BLOCK = 16

RANDOM_SEED: int | None = 42

# =======================
# RNG helpers (seedable)
# =======================
if RANDOM_SEED is not None:
    random.seed(RANDOM_SEED)
_rng = random.Random(RANDOM_SEED) if RANDOM_SEED is not None else None


def _randbytes(n: int) -> bytes:
    """Seeded bytes if RANDOM_SEED is set; otherwise os.urandom()."""
    if _rng is None:
        return os.urandom(n)
    return _rng.getrandbits(8 * n).to_bytes(n, "big")


# =======================
# Utils
# =======================
def _stats(times: list[float]) -> tuple[float, float, float]:
    """Compute (min, avg, max) from a list of timings."""
    return min(times), sum(times) / len(times), max(times)


def _rand_blocks(min_blocks=1, max_blocks=8) -> bytes:
    """Random bytes with length a multiple of 16 (for streaming/no-padding tests)."""
    nblocks = random.randint(min_blocks, max_blocks)
    return _randbytes(nblocks * BLOCK)


def _pkcs7_pad(data: bytes, block_size: int = BLOCK) -> bytes:
    pad_len = block_size - (len(data) % block_size)
    if pad_len == 0:
        pad_len = block_size
    return data + bytes([pad_len]) * pad_len


def _pkcs7_unpad(data: bytes, block_size: int = BLOCK) -> bytes:
    if not data or len(data) % block_size != 0:
        raise ValueError("Invalid data length for PKCS#7 unpad")
    pad_len = data[-1]
    if (
        pad_len < 1
        or pad_len > block_size
        or data[-pad_len:] != bytes([pad_len]) * pad_len
    ):
        raise ValueError("Bad PKCS#7 padding")
    return data[:-pad_len]


def _aligned_size(n: int) -> int:
    """Round n up to a multiple of BLOCK (used for streaming benchmarks)."""
    r = n % BLOCK
    return n if r == 0 else n + (BLOCK - r)


# =======================
# Tests
# =======================
def verify_aes_cbc(key_size: int, rounds: int = VERIFY_ROUNDS) -> bool:
    """
    Verify streaming (no padding) and one-shot PKCS#7 behavior against PyCryptodome.
    """
    key = _randbytes(key_size)
    iv = _randbytes(BLOCK)

    # Streaming encryptors that carry state across rounds
    test_enc = AES_CBC(key, iv)
    ref_enc = PyAES.new(key, PyAES.MODE_CBC, iv)

    for i in range(rounds):
        data = _rand_blocks(1, 4)

        # Capture chaining value for this chunk (IV at this position)
        start_iv = test_enc.iv

        # Encrypt one chunk (streaming, no padding)
        ct_test = test_enc.encrypt(data)
        ct_ref = ref_enc.encrypt(data)

        if ct_test != ct_ref:
            print(
                f"[verify] ciphertext mismatch on round {i+1} for {key_size*8}-bit key"
            )
            return False

        # Decrypt this exact chunk using the correct IV
        test_dec = AES_CBC(key, start_iv)
        pt = test_dec.decrypt(ct_test)
        if pt != data:
            print(
                f"[verify] decryption mismatch on round {i+1} for {key_size*8}-bit key"
            )
            return False

    # One-shot PKCS#7 test (fresh instances)
    data = _randbytes(random.randint(1, 64))
    data_padded = _pkcs7_pad(data)

    test = AES_CBC(key, iv)
    ref = PyAES.new(key, PyAES.MODE_CBC, iv)

    ct_test = test.encrypt(data_padded)
    ct_ref = ref.encrypt(data_padded)
    if ct_test != ct_ref:
        print(f"[verify] PKCS#7 ciphertext mismatch for {key_size*8}-bit key")
        return False

    test_dec = AES_CBC(key, iv)
    pt_padded = test_dec.decrypt(ct_test)
    try:
        pt = _pkcs7_unpad(pt_padded)
    except Exception:
        print(f"[verify] PKCS#7 unpad failed for {key_size*8}-bit key")
        return False

    if pt != data:
        print(f"[verify] PKCS#7 round-trip mismatch for {key_size*8}-bit key")
        return False

    return True


def test_random_text(key_size: int, text_size: int = TEXT_TEST_SIZE) -> bool:
    """
    PKCS#7 one-shot round-trip on random ASCII text and determinism check.
    """
    alphabet = string.ascii_letters + string.digits + string.punctuation + " "
    text = "".join(random.choices(alphabet, k=text_size))
    data = text.encode("utf-8")
    data_padded = _pkcs7_pad(data)

    key = _randbytes(key_size)
    iv = _randbytes(BLOCK)

    c1 = AES_CBC(key, iv)
    ct1 = c1.encrypt(data_padded)

    d1 = AES_CBC(key, iv)
    pt_padded = d1.decrypt(ct1)
    try:
        pt = _pkcs7_unpad(pt_padded)
    except Exception:
        print(f"[text] unpad failed for {key_size*8}-bit key")
        return False

    if pt != data:
        print(f"[text] decryption mismatch for {key_size*8}-bit key")
        return False

    # Determinism with fresh instance and same IV/key
    c2 = AES_CBC(key, iv)
    ct2 = c2.encrypt(_pkcs7_pad(pt))
    if ct2 != ct1:
        print(f"[text] re-encryption mismatch for {key_size*8}-bit key")
        return False

    print(f"[text] random-text round-trip passed for {key_size*8}-bit key")
    return True


# =======================
# Benchmarks
# =======================
def benchmark_cbc_encrypt(
    key_size: int,
    data_size: int = TEXT_TEST_SIZE,
    ops: int = BENCHMARK_OPS,
    rounds: int = BENCHMARK_ROUNDS,
) -> None:
    """
    Benchmark AES_CBC.encrypt vs. PyCryptodome AES.MODE_CBC.encrypt.
    """
    key = _randbytes(key_size)
    iv = _randbytes(BLOCK)
    aligned = _aligned_size(data_size)
    data = _randbytes(aligned)

    test = AES_CBC(key, iv)
    ref = PyAES.new(key, PyAES.MODE_CBC, iv)

    timer_test = timeit.Timer(lambda: test.encrypt(data))
    timer_ref = timeit.Timer(lambda: ref.encrypt(data))

    times_test = timer_test.repeat(repeat=rounds, number=ops)
    times_ref = timer_ref.repeat(repeat=rounds, number=ops)

    min_t, avg_t, max_t = _stats(times_test)
    min_r, avg_r, max_r = _stats(times_ref)

    print(
        f"\n--- ENCRYPT | {key_size*8}-bit key | {aligned}-byte buffer "
        f"({ops:,} ops x {rounds} rounds) ---"
    )
    print(f"AES_CBC.encrypt:  min={min_t:.4f}s  avg={avg_t:.4f}s  max={max_t:.4f}s")
    print(f"PyCrypto encrypt: min={min_r:.4f}s  avg={avg_r:.4f}s  max={max_r:.4f}s")

    if avg_r > 0:
        diff_pct = (avg_t - avg_r) / avg_r * 100.0
        if diff_pct > 0:
            print(f"=> AES_CBC is {diff_pct:.2f}% slower than PyCrypto")
        else:
            print(f"=> AES_CBC is {abs(diff_pct):.2f}% faster than PyCrypto")


def benchmark_cbc_decrypt(
    key_size: int,
    data_size: int = TEXT_TEST_SIZE,
    ops: int = BENCHMARK_OPS,
    rounds: int = BENCHMARK_ROUNDS,
) -> None:
    """
    Benchmark AES_CBC.decrypt vs. PyCryptodome AES.MODE_CBC.decrypt.
    Uses fresh decryptors so decryption starts from the original IV.
    """
    key = _randbytes(key_size)
    iv = _randbytes(BLOCK)
    aligned = _aligned_size(data_size)
    data = _randbytes(aligned)

    # Produce ciphertext once (no padding)
    enc_test = AES_CBC(key, iv)
    ct = enc_test.encrypt(data)

    # Fresh decryptors (their internal state will advance during benchmarking)
    dec_test = AES_CBC(key, iv)
    dec_ref = PyAES.new(key, PyAES.MODE_CBC, iv)

    timer_test = timeit.Timer(lambda: dec_test.decrypt(ct))
    timer_ref = timeit.Timer(lambda: dec_ref.decrypt(ct))

    times_test = timer_test.repeat(repeat=rounds, number=ops)
    times_ref = timer_ref.repeat(repeat=rounds, number=ops)

    min_t, avg_t, max_t = _stats(times_test)
    min_r, avg_r, max_r = _stats(times_ref)

    print(
        f"\n--- DECRYPT | {key_size*8}-bit key | {len(ct)}-byte buffer "
        f"({ops:,} ops x {rounds} rounds) ---"
    )
    print(f"AES_CBC.decrypt:  min={min_t:.4f}s  avg={avg_t:.4f}s  max={max_t:.4f}s")
    print(f"PyCrypto decrypt: min={min_r:.4f}s  avg={avg_r:.4f}s  max={max_r:.4f}s")

    if avg_r > 0:
        diff_pct = (avg_t - avg_r) / avg_r * 100.0
        if diff_pct > 0:
            print(f"=> AES_CBC is {diff_pct:.2f}% slower than PyCrypto")
        else:
            print(f"=> AES_CBC is {abs(diff_pct):.2f}% faster than PyCrypto")


# =======================
# Entry
# =======================
def main() -> None:
    """
    Run verification, random-text test, and benchmark for each AES key size.
    """
    if RANDOM_SEED is not None:
        print(f"[info] Using fixed RANDOM_SEED={RANDOM_SEED}")

    for ks in KEY_SIZES:
        print(f"\n=== Testing {ks*8}-bit AES-CBC ===")

        if not verify_aes_cbc(ks):
            print(f"-> Verify failed for {ks*8}-bit")
            continue
        print(f"-> Verify passed for {ks*8}-bit")

        if not test_random_text(ks):
            print(f"-> Random-text test failed for {ks*8}-bit")
            continue

        benchmark_cbc_encrypt(ks)
        benchmark_cbc_decrypt(ks)

    print("\nAll done.")


if __name__ == "__main__":
    main()
