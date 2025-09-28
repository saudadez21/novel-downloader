#!/usr/bin/env python3
"""
novel_downloader.infra.jsbridge.decryptor
-----------------------------------------

"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
import uuid
from dataclasses import dataclass
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import Any, Final

from novel_downloader.infra.network import download
from novel_downloader.infra.paths import (
    EXPR_TO_JSON_SCRIPT_PATH,
    JS_SCRIPT_DIR,
    QD_DECRYPT_SCRIPT_PATH,
    QQ_DECRYPT_SCRIPT_PATH,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RemoteAsset:
    url: str
    basename: str


@dataclass(frozen=True)
class LocalScript:
    src: Traversable
    dst_name: str


@dataclass(frozen=True)
class ProviderSpec:
    name: str
    decrypt_script: LocalScript
    fock_asset: RemoteAsset | None = None
    has_binary_fallback: bool = False


QD_SPEC: Final[ProviderSpec] = ProviderSpec(
    name="qd",
    decrypt_script=LocalScript(
        src=QD_DECRYPT_SCRIPT_PATH,
        dst_name="qidian_decrypt_node.js",
    ),
    fock_asset=RemoteAsset(
        basename="4819793b.qeooxh.js",
        url="https://cococdn.qidian.com/coco/s12062024/4819793b.qeooxh.js",
    ),
    has_binary_fallback=True,
)

QQ_SPEC: Final[ProviderSpec] = ProviderSpec(
    name="qq",
    decrypt_script=LocalScript(
        src=QQ_DECRYPT_SCRIPT_PATH,
        dst_name="qq_decrypt_node.js",
    ),
    fock_asset=RemoteAsset(
        basename="cefc2a5d.pz1phw.js",
        url="https://imgservices-1252317822.image.myqcloud.com/coco/s10192022/cefc2a5d.pz1phw.js",
    ),
    has_binary_fallback=False,
)

EVAL_SPEC: Final[LocalScript] = LocalScript(
    src=EXPR_TO_JSON_SCRIPT_PATH,
    dst_name="expr_to_json.js",
)


class NodeDecryptor:
    """
    Decrypts chapter payloads using Node-backed scripts and/or a binary fallback.
    """

    def __init__(self) -> None:
        """
        Initialise the decryptor environment.
        """
        self.script_dir: Path = JS_SCRIPT_DIR
        self.script_dir.mkdir(parents=True, exist_ok=True)

        self.has_node: bool = shutil.which("node") is not None

        # Prepared commands (None => unavailable)
        self._qd_script_cmd: list[str] | None = None
        self._qq_script_cmd: list[str] | None = None
        self._eval_script_cmd: list[str] | None = None

        self._prepare_eval_environment()
        self._prepare_provider(QD_SPEC)  # sets _qd_script_cmd
        self._prepare_provider(QQ_SPEC)  # sets _qq_script_cmd

    def decrypt_qd(
        self,
        ciphertext: str,
        chapter_id: str,
        fkp: str,
        fuid: str,
    ) -> str:
        """
        Qidian decrypt. Uses Node if present; otherwise tries a fallback binary.

        :param ciphertext: Base64-encoded encrypted content.
        :param chapter_id: The chapter's numeric ID.
        :param fkp: Base64-encoded Fock key param from the page.
        :param fuid: Fock user ID param from the page.
        :return: "" if unavailable or inputs are missing.
        :raises RuntimeError: if the Node.js subprocess exits with a non-zero code.
        """
        if not self._qd_script_cmd:
            logger.warning("QD decryptor unavailable (no Node and no fallback).")
            return ""
        if not (ciphertext and chapter_id and fkp and fuid):
            logger.debug("QD decrypt: missing required inputs.")
            return ""

        task_id = uuid.uuid4().hex
        input_path = self.script_dir / f"qd_in_{task_id}.json"
        output_path = self.script_dir / f"qd_out_{task_id}.txt"

        try:
            input_path.write_text(
                json.dumps([ciphertext, chapter_id, fkp, fuid]),
                encoding="utf-8",
            )

            cmd = self._qd_script_cmd + [input_path.name, output_path.name]
            logger.debug("Running QD decrypt: %s (cwd=%s)", cmd, self.script_dir)
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.script_dir,
            )

            if proc.returncode != 0:
                stderr = (proc.stderr or "").strip()
                raise RuntimeError(
                    f"QD decrypt failed: {stderr or 'non-zero exit code'}"
                )

            return output_path.read_text(encoding="utf-8").strip()
        finally:
            input_path.unlink(missing_ok=True)
            output_path.unlink(missing_ok=True)

    def decrypt_qq(
        self,
        ciphertext: str,
        chapter_id: str,
        fkp: str,
        fuid: str,
    ) -> str:
        """
        QQ decrypt. Node-only.

        :param ciphertext: Base64-encoded encrypted content.
        :param chapter_id: The chapter's numeric ID.
        :param fkp: Base64-encoded Fock key param from the page.
        :param fuid: Fock user ID param from the page.
        :return: "" if Node/script not available or inputs missing.
        :raises RuntimeError: if the Node.js subprocess exits with a non-zero code.
        """
        if not self._qq_script_cmd:
            logger.info(
                "QQ decrypt skipped: Node not available or script not prepared."
            )
            return ""
        if not (ciphertext and chapter_id and fkp and fuid):
            logger.debug("QQ decrypt: missing required inputs.")
            return ""

        task_id = uuid.uuid4().hex
        input_path = self.script_dir / f"qq_in_{task_id}.json"
        output_path = self.script_dir / f"qq_out_{task_id}.txt"

        try:
            input_path.write_text(
                json.dumps([ciphertext, chapter_id, fkp, fuid]),
                encoding="utf-8",
            )

            cmd = self._qq_script_cmd + [input_path.name, output_path.name]
            logger.debug("Running QQ decrypt: %s (cwd=%s)", cmd, self.script_dir)
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.script_dir,
            )

            if proc.returncode != 0:
                stderr = (proc.stderr or "").strip()
                raise RuntimeError(
                    f"QQ decrypt failed: {stderr or 'non-zero exit code'}"
                )

            return output_path.read_text(encoding="utf-8").strip()
        finally:
            input_path.unlink(missing_ok=True)
            output_path.unlink(missing_ok=True)

    def eval_to_json(self, js_code: str) -> dict[str, Any]:
        """
        Evaluate JS and parse JSON result. Node-only.

        :return: {} if unavailable or input empty.
        :raises RuntimeError: if the invoked process fails or outputs invalid JSON.
        """
        if not self._eval_script_cmd:
            logger.info(
                "eval_to_json skipped: Node not available or script not prepared."
            )
            return {}
        if not js_code:
            logger.debug("eval_to_json: empty input.")
            return {}

        logger.debug("Running eval_to_json (cwd=%s)", self.script_dir)
        proc = subprocess.run(
            self._eval_script_cmd,
            input=js_code,
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=self.script_dir,
        )
        if proc.returncode != 0:
            stderr = (proc.stderr or "").strip()
            raise RuntimeError(f"eval_to_json failed: {stderr or 'non-zero exit code'}")

        stdout = (proc.stdout or "").strip()
        if not stdout:
            return {}

        try:
            return json.loads(stdout) or {}
        except json.JSONDecodeError as exc:
            logger.error("eval_to_json: invalid JSON output: %s", stdout)
            raise RuntimeError("eval_to_json produced invalid JSON.") from exc

    def _prepare_provider(self, spec: ProviderSpec) -> None:
        """
        Prepare a provider:
          * If Node is available: copy node script and fetch Fock asset
          * Else if provider allows binary fallback (QD): try local binary
          * Else: leave command None (feature disabled)
        """
        dst_script = self.script_dir / spec.decrypt_script.dst_name

        if self.has_node:
            # Prepare Node script + assets
            try:
                if not dst_script.exists():
                    self._copy_from_traversable(spec.decrypt_script.src, dst_script)

                if spec.fock_asset:
                    fock_path = self.script_dir / spec.fock_asset.basename
                    if not fock_path.exists():
                        download(spec.fock_asset.url, self.script_dir)

                cmd: list[str] | None = ["node", str(dst_script)]
                logger.debug("%s decryptor prepared with Node.", spec.name.upper())
            except Exception as exc:
                logger.warning("%s Node prep failed: %s", spec.name.upper(), exc)
                cmd = None
        else:
            # No Node available
            if spec.has_binary_fallback and spec.name == "qd":
                try:
                    from .decryptor_fetcher import ensure_qd_decryptor

                    bin_path = ensure_qd_decryptor(self.script_dir)
                    cmd = [str(bin_path)]
                    logger.debug(
                        "QD decryptor prepared with binary fallback at %s.", bin_path
                    )
                except Exception as exc:
                    logger.error("QD binary fallback unavailable: %s", exc)
                    cmd = None
            else:
                logger.info(
                    "%s decryptor skipped: Node not available.", spec.name.upper()
                )
                cmd = None

        if spec.name == "qd":
            self._qd_script_cmd = cmd
        else:
            self._qq_script_cmd = cmd

    def _prepare_eval_environment(self) -> None:
        """
        Prepare eval script (Node-only).
        """
        if not self.has_node:
            logger.info("eval_to_json skipped: Node not available.")
            self._eval_script_cmd = None
            return

        dst = self.script_dir / EVAL_SPEC.dst_name
        try:
            if not dst.exists():
                self._copy_from_traversable(EVAL_SPEC.src, dst)
            self._eval_script_cmd = ["node", str(dst)]
            logger.debug("eval_to_json prepared with Node.")
        except Exception as exc:
            logger.warning("eval_to_json prep failed; feature disabled. (%s)", exc)
            self._eval_script_cmd = None

    @staticmethod
    def _copy_from_traversable(src: Traversable, dst: Path) -> None:
        """Copy a packaged resource (Traversable) to a filesystem path."""
        dst.parent.mkdir(parents=True, exist_ok=True)
        with src.open("rb") as rf, open(dst, "wb") as wf:
            shutil.copyfileobj(rf, wf)


_DECRYPTOR: NodeDecryptor | None = None


def get_decryptor() -> NodeDecryptor:
    """
    Return the singleton NodeDecryptor.
    """
    global _DECRYPTOR
    if _DECRYPTOR is None:
        _DECRYPTOR = NodeDecryptor()
    return _DECRYPTOR
