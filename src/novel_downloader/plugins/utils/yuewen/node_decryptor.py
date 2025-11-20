#!/usr/bin/env python3
"""
novel_downloader.plugins.utils.yuewen.node_decryptor
----------------------------------------------------

Yuewen Node.js-backed decryptor.
"""

from __future__ import annotations

__all__ = ["AssetSpec", "NodeDecryptor"]

import json
import logging
import shutil
import subprocess
import uuid
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import Literal, TypedDict

import requests

from novel_downloader.infra.http_defaults import DEFAULT_USER_HEADERS
from novel_downloader.infra.paths import JS_SCRIPT_DIR

logger = logging.getLogger(__name__)


class LocalAssetSpec(TypedDict):
    type: Literal["local"]
    src: Traversable | Path
    filename: str


class RemoteAssetSpec(TypedDict):
    type: Literal["remote"]
    url: str
    filename: str


AssetSpec = LocalAssetSpec | RemoteAssetSpec


class NodeDecryptor:
    """
    Yuewen decryptor driven by a Node.js script.

    The Node script is expected to accept:
        node <script> <in_json_filename> <out_txt_filename>

    where <in_json_filename> contains:
        [ciphertext, chapter_id, fkp, fuid]

    and <out_txt_filename> is written by the script.
    """

    def __init__(
        self,
        script: AssetSpec,
        assets: list[AssetSpec] | None = None,
        *,
        script_dir: Path = JS_SCRIPT_DIR,
        node_bin: str = "node",
        request_timeout: float = 15.0,
        headers: dict[str, str] = DEFAULT_USER_HEADERS,
    ) -> None:
        self.script = script
        self.assets = assets or []

        self.script_dir = script_dir
        self.node_bin = node_bin
        self.request_timeout = request_timeout
        self.headers = headers

        self.script_dir.mkdir(parents=True, exist_ok=True)

        self.has_node = shutil.which(node_bin) is not None
        self._prepared = False
        self._script_path: Path | None = None
        self._asset_cache: set[str] = set()

    def decrypt(
        self,
        ciphertext: str,
        chapter_id: str,
        fkp: str,
        fuid: str,
    ) -> str | None:
        """
        Decrypt via Node script.

        :return: None if skipped/unavailable/invalid input
        """
        if not self.has_node:
            logger.info("decrypt skipped: Node.js not available.")
            return None

        if not (ciphertext and chapter_id and fkp and fuid):
            logger.debug("decrypt: missing input parameters.")
            return None

        self._prepare()
        if self._script_path is None:
            logger.info("decrypt skipped: script not available.")
            return None

        task_id = uuid.uuid4().hex
        in_path = self.script_dir / f"in_{task_id}.json"
        out_path = self.script_dir / f"out_{task_id}.txt"

        try:
            in_path.write_text(
                json.dumps([ciphertext, chapter_id, fkp, fuid]),
                encoding="utf-8",
            )

            proc = subprocess.run(
                [self.node_bin, str(self._script_path), in_path.name, out_path.name],
                capture_output=True,
                text=True,
                cwd=self.script_dir,
            )

            if proc.returncode != 0:
                stderr = (proc.stderr or "").strip()
                raise RuntimeError(f"decrypt failed: {stderr or 'non-zero exit code'}")

            return out_path.read_text(encoding="utf-8").strip()

        finally:
            in_path.unlink(missing_ok=True)
            out_path.unlink(missing_ok=True)

    def _prepare(self) -> None:
        """Ensure main script + all assets exist on disk (lazy, once)."""
        if self._prepared:
            return

        if not self.has_node:
            logger.info("decrypt skipped: Node.js not available.")
            return

        try:
            self._script_path = self._ensure_asset(self.script)
            for a in self.assets:
                self._ensure_asset(a)

            self._prepared = True
            logger.debug("NodeDecryptor prepared in %s", self.script_dir)

        except Exception as exc:
            logger.warning("decrypt preparation failed: %s", exc)
            self._script_path = None
            self._prepared = True

    def _ensure_asset(self, spec: AssetSpec) -> Path:
        """Copy/download an asset into script_dir if missing."""
        filename = spec["filename"]
        dst = self.script_dir / filename

        if filename in self._asset_cache or dst.exists():
            self._asset_cache.add(filename)
            return dst

        if spec["type"] == "local":
            src = spec["src"]
            if isinstance(src, Path):
                # local filesystem file
                dst.write_bytes(src.read_bytes())
            else:
                # package Traversable
                dst.write_bytes(src.read_bytes())

        elif spec["type"] == "remote":
            logger.debug("Downloading remote asset: %s", spec["url"])
            resp = requests.get(
                spec["url"], headers=self.headers, timeout=self.request_timeout
            )
            resp.raise_for_status()
            dst.write_bytes(resp.content)

        self._asset_cache.add(filename)
        return dst
