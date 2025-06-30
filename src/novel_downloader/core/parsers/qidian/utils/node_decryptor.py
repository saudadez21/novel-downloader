#!/usr/bin/env python3
"""
novel_downloader.core.parsers.qidian.utils.node_decryptor
---------------------------------------------------------

Provides QidianNodeDecryptor, which ensures a Node.js environment,
downloads or installs the required JS modules (Fock + decrypt script),
and invokes a Node.js subprocess to decrypt Qidian chapter content.
"""

import json
import logging
import shutil
import subprocess
import uuid
from pathlib import Path

from novel_downloader.utils.constants import (
    JS_SCRIPT_DIR,
    QD_DECRYPT_SCRIPT_PATH,
)

from .decryptor_fetcher import ensure_decryptor

logger = logging.getLogger(__name__)


class QidianNodeDecryptor:
    """
    A decryptor that uses Node.js plus Qidian's Fock JavaScript module
    to decrypt encrypted chapter payloads.

    On initialization, this class will:
      1. Verify that `node` is on PATH.
      2. Copy our bundled `qidian_decrypt_node.js` into `JS_SCRIPT_DIR`.
      3. Download the remote Fock module JS if not already present.

    Calling `decrypt()` will:
      - Write a temp JSON input file with [ciphertext, chapter_id, fkp, fuid].
      - Spawn `node qidian_decrypt_node.js <in> <out>`.
      - Read and return the decrypted text.
      - Clean up the temp files.
    """

    QIDIAN_FOCK_JS_URL: str = (
        "https://cococdn.qidian.com/coco/s12062024/4819793b.qeooxh.js"
    )
    QIDIAN_FOCK_JS_PATH: Path = JS_SCRIPT_DIR / "4819793b.qeooxh.js"
    QIDIAN_DECRYPT_SCRIPT_FILE: str = "qidian_decrypt_node.js"
    QIDIAN_DECRYPT_SCRIPT_PATH: Path = JS_SCRIPT_DIR / QIDIAN_DECRYPT_SCRIPT_FILE

    def __init__(self) -> None:
        """
        Initialise the decryptor environment and decide which executable will be
        used (`node` script or the pre-built binary).
        """
        self.script_dir: Path = JS_SCRIPT_DIR
        self.script_dir.mkdir(parents=True, exist_ok=True)

        self._script_cmd: list[str] | None = None
        self._check_environment()

    def _check_environment(self) -> None:
        """
        Decide which decryptor backend to use and make sure it is ready.
        """
        try:
            # 1) Check Node.js
            if not shutil.which("node"):
                raise OSError("Node.js is not installed or not in PATH.")

            # 2) Copy bundled decrypt script into place if missing
            if not self.QIDIAN_DECRYPT_SCRIPT_PATH.exists():
                try:
                    resource = QD_DECRYPT_SCRIPT_PATH
                    shutil.copyfile(str(resource), str(self.QIDIAN_DECRYPT_SCRIPT_PATH))
                except Exception as e:
                    logger.error("[decryptor] Failed to copy decrypt script: %s", e)
                    raise

            # 3) Download the Fock JS module from Qidian CDN if missing
            if not self.QIDIAN_FOCK_JS_PATH.exists():
                from novel_downloader.utils.network import download_js_file

                try:
                    download_js_file(
                        self.QIDIAN_FOCK_JS_URL,
                        self.script_dir,
                        on_exist="overwrite",
                    )
                except Exception as e:
                    logger.error("[decryptor] Failed to download Fock JS module: %s", e)
                    raise
            self._script_cmd = ["node", str(self.QIDIAN_DECRYPT_SCRIPT_PATH)]
            return
        except Exception:
            try:
                self._script_cmd = [str(ensure_decryptor(self.script_dir))]
            except Exception as exc:
                raise OSError(
                    "Neither Node.js nor fallback binary is available."
                ) from exc

    def decrypt(
        self,
        ciphertext: str | bytes,
        chapter_id: str,
        fkp: str,
        fuid: str,
    ) -> str:
        """
        Decrypt a chapter payload via our Node.js script.

        :param ciphertext: Base64-encoded encrypted content (str or bytes).
        :param chapter_id: The chapter's numeric ID.
        :param fkp: Base64-encoded Fock key param from the page.
        :param fuid: Fock user ID param from the page.
        :return: The decrypted plain-text content.
        :raises RuntimeError: if the Node.js subprocess exits with a non-zero code.
        """
        if not self._script_cmd:
            return ""
        if not (ciphertext and chapter_id and fkp and fuid):
            return ""
        # Normalize inputs
        cipher_str = (
            ciphertext.decode("utf-8")
            if isinstance(ciphertext, (bytes | bytearray))
            else str(ciphertext)
        )
        chapter_str = str(chapter_id)

        # Create unique temp file names
        task_id = uuid.uuid4().hex
        input_path = self.script_dir / f"input_{task_id}.json"
        output_path = self.script_dir / f"output_{task_id}.txt"

        try:
            # Write arguments as JSON array
            input_path.write_text(
                json.dumps([cipher_str, chapter_str, fkp, fuid]),
                encoding="utf-8",
            )

            cmd = self._script_cmd + [input_path.name, output_path.name]
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.script_dir),
            )

            if proc.returncode != 0:
                raise RuntimeError(f"Node error: {proc.stderr.strip()}")

            # Return decrypted content
            return output_path.read_text(encoding="utf-8").strip()

        finally:
            # Clean up temp files
            input_path.unlink(missing_ok=True)
            output_path.unlink(missing_ok=True)


_decryptor: QidianNodeDecryptor | None = None


def get_decryptor() -> QidianNodeDecryptor:
    """
    Return the singleton QidianNodeDecryptor, initializing it on first use.
    """
    global _decryptor
    if _decryptor is None:
        _decryptor = QidianNodeDecryptor()
    return _decryptor
