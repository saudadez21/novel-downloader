#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.parsers.qidian_parser.session.node_decryptor
------------------------------------------------------------------

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
from typing import Union

from novel_downloader.utils.constants import (
    JS_SCRIPT_DIR,
    QD_DECRYPT_SCRIPT_PATH,
)

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
        Prepare the script directory and verify that both Node.js
        and the necessary JS files are available.
        """
        self.script_dir: Path = JS_SCRIPT_DIR
        self.script_dir.mkdir(parents=True, exist_ok=True)
        self.script_path: Path = self.QIDIAN_DECRYPT_SCRIPT_PATH
        self._check_environment()

    def _check_environment(self) -> None:
        """
        Ensure Node.js is installed, our decrypt script is copied from
        package resources, and the Fock JS module is downloaded.

        :raises EnvironmentError: if `node` is not on the system PATH.
        """
        # 1) Check Node.js
        if not shutil.which("node"):
            raise EnvironmentError("Node.js is not installed or not in PATH.")

        # 2) Copy bundled decrypt script into place if missing
        if not self.QIDIAN_DECRYPT_SCRIPT_PATH.exists():
            try:
                resource = QD_DECRYPT_SCRIPT_PATH
                shutil.copyfile(str(resource), str(self.QIDIAN_DECRYPT_SCRIPT_PATH))
                logger.info(
                    "[decryptor] Copied decrypt script to %s",
                    self.QIDIAN_DECRYPT_SCRIPT_PATH,
                )
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
                logger.info(
                    "[decryptor] Downloaded Fock module to %s", self.QIDIAN_FOCK_JS_PATH
                )
            except Exception as e:
                logger.error("[decryptor] Failed to download Fock JS module: %s", e)
                raise

    def decrypt(
        self,
        ciphertext: Union[str, bytes],
        chapter_id: Union[str, int],
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
        # Normalize inputs
        cipher_str = (
            ciphertext.decode("utf-8")
            if isinstance(ciphertext, (bytes, bytearray))
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

            logger.debug(
                "[decryptor] Invoking Node.js: node %s %s %s",
                self.script_path.name,
                input_path.name,
                output_path.name,
            )

            proc = subprocess.run(
                ["node", self.script_path.name, input_path.name, output_path.name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
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
