#!/usr/bin/env python3
"""
novel_downloader.core.parsers.qidian.utils.decryptor_fetcher
------------------------------------------------------------

Download and cache the *qidian-decryptor* executable from the project's
GitHub releases.
"""

from __future__ import annotations

import hashlib
import platform
import stat
from pathlib import Path
from typing import Final

import requests

from novel_downloader.utils.constants import JS_SCRIPT_DIR

DEST_ROOT: Final[Path] = JS_SCRIPT_DIR
GITHUB_OWNER: Final = "BowenZ217"
GITHUB_REPO: Final = "qidian-decryptor"
RELEASE_VERSION: Final = "v1.0.1"
BASE_URL: Final = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases/download/{RELEASE_VERSION}"
PLATFORM_BINARIES: Final[dict[str, str]] = {
    "linux": "qidian-decryptor-linux",
    "macos": "qidian-decryptor-macos",
    "win": "qidian-decryptor-win.exe",
}


# --------------------------------------------------------------------------- #
# API
# --------------------------------------------------------------------------- #


def ensure_decryptor(dest_root: Path | None = None) -> Path:
    """
    Ensure that the decryptor executable matching the current platform and
    :data:`RELEASE_VERSION` exists locally; download it if necessary.

    :param dest_root: Root directory used to cache the binary.
                      If *None*, the global constant ``JS_SCRIPT_DIR`` is used.
    :return: Path to the ready-to-use executable (inside the version sub-folder).
    :raises RuntimeError: If the current platform is unsupported.
    :raises ValueError: If the downloaded file fails SHA-256 verification.
    """
    dest_root = DEST_ROOT if dest_root is None else Path(dest_root).expanduser()
    platform_key = _get_platform_key()

    bin_name = PLATFORM_BINARIES[platform_key]
    # 版本: /<version>/<binary>
    version_dir = dest_root / RELEASE_VERSION.lstrip("v")
    dest_path = version_dir / bin_name

    if dest_path.exists():
        return dest_path

    version_dir.mkdir(parents=True, exist_ok=True)
    _download_binary(platform_key, dest_path)
    _make_executable(dest_path)

    return dest_path


# --------------------------------------------------------------------------- #
# helper functions
# --------------------------------------------------------------------------- #


def _get_platform_key() -> str:
    sys = platform.system().lower()
    if "windows" in sys:
        return "win"
    if "linux" in sys:
        return "linux"
    if "darwin" in sys:
        return "macos"
    raise RuntimeError(f"Unsupported platform: {sys}")


def _download_binary(platform_key: str, dest_path: Path) -> None:
    """
    Download the binary for *platform_key*, verify its SHA-256 checksum against
    the release-wide ``SHA256SUMS`` manifest, and write it to *dest_path*.

    :param platform_key: Key in :data:`PLATFORM_BINARIES` ("linux" | "macos" | "win").
    :param dest_path: Target path where the binary will be saved.
    :raises RuntimeError: If the checksum for the binary is missing in the manifest.
    :raises ValueError: If the downloaded file fails SHA-256 verification.
    """
    bin_name = PLATFORM_BINARIES[platform_key]

    manifest_url = f"{BASE_URL}/SHA256SUMS"
    manifest_resp = requests.get(manifest_url, timeout=10)
    manifest_resp.raise_for_status()

    expected_hash: str | None = None
    for line in manifest_resp.text.splitlines():
        parts = line.strip().split()
        if len(parts) == 2 and parts[1] == bin_name:
            expected_hash = parts[0]
            break

    if expected_hash is None:
        raise RuntimeError(f"Checksum for {bin_name!r} not found in SHA256SUMS")

    file_url = f"{BASE_URL}/{bin_name}"
    resp = requests.get(file_url, timeout=30)
    resp.raise_for_status()
    dest_path.write_bytes(resp.content)

    if _sha256sum(dest_path) != expected_hash:
        dest_path.unlink(missing_ok=True)
        raise ValueError("SHA256 mismatch — download corrupted, file removed.")


def _sha256sum(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _make_executable(p: Path) -> None:
    """
    Add executable permission bits on Unix-like systems; keep the file unchanged
    on Windows. Any *PermissionError* raised by ``chmod`` is silently ignored.

    :param p: Path to the downloaded binary that should be made executable.
    """
    try:
        mode = p.stat().st_mode
        p.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    except PermissionError:
        pass


__all__ = [
    "ensure_decryptor",
    "RELEASE_VERSION",
]
