#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.utils.fontocr.ocr_v2
-------------------------------------

This class provides utility methods for optical character recognition (OCR)
and font mapping, primarily used for decrypting custom font encryption
on web pages (e.g., the Qidian website).
"""

import json
import logging
import math
import os
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Set, Tuple, TypeVar, Union

import cv2
import numpy as np
import paddle
from fontTools.ttLib import TTFont
from paddle.inference import Config
from paddle.inference import create_predictor as _create_predictor
from paddleocr.ppocr.postprocess.rec_postprocess import CTCLabelDecode
from PIL import Image, ImageDraw, ImageFont

try:
    # pip install cupy-cuda11x
    import cupy as array_backend  # GPU acceleration
except ImportError:
    import numpy as array_backend  # CPU only

from novel_downloader.utils.constants import (
    REC_CHAR_MODEL_FILES,
    REC_IMAGE_SHAPE_MAP,
)
from novel_downloader.utils.hash_store import img_hash_store
from novel_downloader.utils.model_loader import (
    get_rec_char_vector_dir,
    get_rec_chinese_char_model_dir,
)

T = TypeVar("T")
logger = logging.getLogger(__name__)


class TextRecognizer(object):
    def __init__(
        self,
        rec_model_dir: str,
        rec_image_shape: str,
        rec_batch_num: int,
        rec_char_dict_path: str,
        use_space_char: bool = False,
        use_gpu: bool = False,
        gpu_mem: int = 500,
        gpu_id: Optional[int] = None,
    ):
        self.rec_batch_num = int(rec_batch_num)
        self.rec_image_shape = tuple(map(int, rec_image_shape.split(",")))  # (C, H, W)
        self.postprocess_op = CTCLabelDecode(
            character_dict_path=rec_char_dict_path,
            use_space_char=use_space_char,
        )

        self._create_predictor(
            model_dir=rec_model_dir,
            use_gpu=use_gpu,
            gpu_mem=gpu_mem,
            gpu_id=gpu_id,
        )

    def _get_infer_gpu_id(self) -> int:
        """
        Look at CUDA_VISIBLE_DEVICES or HIP_VISIBLE_DEVICES,
        pick the first entry and return as integer. Fallback to 0.
        """
        if not paddle.device.is_compiled_with_rocm:
            gpu_env = os.environ.get("CUDA_VISIBLE_DEVICES", "0")
        else:
            gpu_env = os.environ.get("HIP_VISIBLE_DEVICES", "0")

        first = gpu_env.split(",")[0]
        try:
            return int(first)
        except ValueError:
            return 0

    def _create_predictor(
        self,
        model_dir: str,
        use_gpu: bool,
        gpu_mem: int,
        gpu_id: Optional[int] = None,
    ) -> None:
        """
        Internal helper to build the Paddle predictor + I/O handles
        """
        model_file = f"{model_dir}/inference.pdmodel"
        params_file = f"{model_dir}/inference.pdiparams"

        cfg = Config(model_file, params_file)
        if use_gpu:
            chosen = gpu_id if gpu_id is not None else self._get_infer_gpu_id()
            cfg.enable_use_gpu(gpu_mem, chosen)
        else:
            cfg.disable_gpu()

        # enable memory optim
        cfg.enable_memory_optim()
        cfg.disable_glog_info()
        # Use zero-copy feed/fetch for speed
        cfg.switch_use_feed_fetch_ops(False)
        # Enable IR optimizations
        cfg.switch_ir_optim(True)

        self.config = cfg
        self.predictor = _create_predictor(cfg)

        in_name = self.predictor.get_input_names()[0]
        self.input_tensor = self.predictor.get_input_handle(in_name)

        out_names = self.predictor.get_output_names()
        preferred = "softmax_0.tmp_0"
        selected = [preferred] if preferred in out_names else out_names
        self.output_tensors = [self.predictor.get_output_handle(n) for n in selected]

    def __call__(self, img_list: List[np.ndarray]) -> List[Tuple[str, float]]:
        """
        Perform batch OCR on a list of images and return (text, confidence) tuples.
        """
        img_num = len(img_list)
        results: List[Tuple[str, float]] = []

        C, H, W0 = self.rec_image_shape

        # Process images in batches
        for start in range(0, img_num, self.rec_batch_num):
            batch = img_list[start : start + self.rec_batch_num]
            # Compute width-to-height ratios for all images in the batch
            wh_ratios = [img.shape[1] / float(img.shape[0]) for img in batch]
            max_wh = max(W0 / H, *wh_ratios)

            B = len(batch)
            # Pre-allocate a numpy array for the batch
            batch_tensor = np.zeros(
                (B, C, H, int(math.ceil(H * max_wh))), dtype=np.float32
            )

            # Normalize and pad each image into the batch tensor
            for i, img in enumerate(batch):
                norm = self.resize_norm_img(img, max_wh)
                batch_tensor[i, :, :, : norm.shape[2]] = norm

            # Run inference
            self.input_tensor.copy_from_cpu(batch_tensor)
            self.predictor.run()

            # Retrieve and post-process outputs
            outputs = [t.copy_to_cpu() for t in self.output_tensors]
            preds = outputs[0] if len(outputs) == 1 else outputs

            rec_batch = self.postprocess_op(
                preds,
                return_word_box=False,
                wh_ratio_list=wh_ratios,
                max_wh_ratio=max_wh,
            )
            results.extend(rec_batch)

        return results

    def resize_norm_img(self, img: np.ndarray, max_wh_ratio: float) -> np.ndarray:
        C, H, W0 = self.rec_image_shape
        if img.ndim == 2:
            # Convert grayscale images to RGB
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        assert (
            img.ndim == 3 and img.shape[2] == C
        ), f"Expect {C}-channel image, got {img.shape}"

        h, w = img.shape[:2]
        # Determine new width based on the height and max width-height ratio
        new_w = min(int(math.ceil(H * (w / h))), int(H * max_wh_ratio))
        resized = cv2.resize(img, (new_w, H)).astype("float32")
        # Change to CHW format and scale to [0,1]
        resized = resized.transpose(2, 0, 1) / 255.0
        # Normalize to [-1, 1]
        resized = (resized - 0.5) / 0.5

        return resized


class FontOCRV2:
    """
    Version 2 of the FontOCR utility.

    :param use_freq: if True, weight scores by character frequency
    :param cache_dir: base path to store font-map JSON data
    :param threshold: minimum confidence threshold [0.0-1.0]
    :param font_debug: if True, dump per-char debug images under cache_dir
    """

    # Default constants
    CHAR_IMAGE_SIZE = 64
    CHAR_FONT_SIZE = 52
    _freq_weight = 0.05

    # shared resources
    _global_char_freq_db: Dict[str, int] = {}
    _global_ocr: Optional[TextRecognizer] = None
    _global_vec_db: Optional[np.ndarray] = None
    _global_vec_label: Tuple[str, ...] = ()
    _global_vec_shape: Tuple[int, int] = (32, 32)

    def __init__(
        self,
        cache_dir: Union[str, Path],
        use_freq: bool = False,
        use_ocr: bool = True,
        use_vec: bool = False,
        batch_size: int = 32,
        ocr_weight: float = 0.6,
        vec_weight: float = 0.4,
        ocr_version: str = "v1.0",
        threshold: float = 0.0,
        font_debug: bool = False,
        **kwargs: Any,
    ) -> None:
        self.use_freq = use_freq
        self.use_ocr = use_ocr
        self.use_vec = use_vec
        self.batch_size = batch_size
        self.ocr_weight = ocr_weight
        self.vec_weight = vec_weight
        self.ocr_version = ocr_version
        self.threshold = threshold
        self.font_debug = font_debug
        self._max_freq = 5

        self._cache_dir = Path(cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._fixed_map_dir = self._cache_dir / "fixed_font_map"
        self._fixed_map_dir.mkdir(parents=True, exist_ok=True)

        if font_debug:
            self._debug_dir = self._cache_dir / "font_debug" / "badcase"
            self._debug_dir.mkdir(parents=True, exist_ok=True)

        # load shared OCR + frequency DB
        if self.use_ocr:
            self._load_ocr_model()
        if self.use_freq:
            self._load_char_freq_db()
        if self.use_vec:
            self._load_char_vec_db()

    def _load_ocr_model(self) -> None:
        """
        Initialize the shared PaddleOCR model if not already loaded.
        """
        if FontOCRV2._global_ocr is not None:
            return

        gpu_available = paddle.device.is_compiled_with_cuda()
        self._char_model_dir = get_rec_chinese_char_model_dir(self.ocr_version)

        for fname in REC_CHAR_MODEL_FILES:
            full_path = self._char_model_dir / fname
            if not full_path.exists():
                raise FileNotFoundError(f"[FontOCR] Required file missing: {full_path}")

        char_dict_file = self._char_model_dir / "rec_custom_keys.txt"
        FontOCRV2._global_ocr = TextRecognizer(
            rec_model_dir=str(self._char_model_dir),
            rec_char_dict_path=str(char_dict_file),
            rec_image_shape=REC_IMAGE_SHAPE_MAP[self.ocr_version],
            rec_batch_num=self.batch_size,
            use_space_char=False,
            use_gpu=gpu_available,
        )

    def _load_char_freq_db(self) -> bool:
        """
        Loads character frequency data from a JSON file and
        assigns it to the instance variable.

        :return: True if successfully loaded, False otherwise.
        """
        if FontOCRV2._global_char_freq_db is not None:
            return True

        try:
            char_freq_map_file = self._char_model_dir / "char_freq.json"
            with char_freq_map_file.open("r", encoding="utf-8") as f:
                FontOCRV2._global_char_freq_db = json.load(f)
            self._max_freq = max(FontOCRV2._global_char_freq_db.values())
            return True
        except Exception as e:
            logger.warning("[FontOCR] Failed to load char freq DB: %s", e)
            return False

    def _load_char_vec_db(self) -> None:
        """
        Initialize the shared Char Vector if not already loaded.
        """
        if FontOCRV2._global_vec_db is not None:
            return

        char_vec_dir = get_rec_char_vector_dir(self.ocr_version)
        char_vec_npy_file = char_vec_dir / "char_vectors.npy"
        char_vec_label_file = char_vec_dir / "char_vectors.txt"

        # Load and normalize vector database
        vec_db = array_backend.load(char_vec_npy_file)
        _, dim = vec_db.shape
        side = int(np.sqrt(dim))
        FontOCRV2._global_vec_shape = (side, side)

        norm = array_backend.linalg.norm(vec_db, axis=1, keepdims=True) + 1e-6
        FontOCRV2._global_vec_db = vec_db / norm

        # Load corresponding labels
        with open(char_vec_label_file, "r", encoding="utf-8") as f:
            FontOCRV2._global_vec_label = tuple(line.strip() for line in f)

    @staticmethod
    def _generate_char_image(
        char: str,
        render_font: ImageFont.FreeTypeFont,
        is_reflect: bool = False,
    ) -> Optional[Image.Image]:
        """
        Render a single character into a square image.
        If is_reflect is True, flip horizontally.
        """
        size = FontOCRV2.CHAR_IMAGE_SIZE
        img = Image.new("L", (size, size), color=255)
        draw = ImageDraw.Draw(img)
        bbox = draw.textbbox((0, 0), char, font=render_font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x = (size - w) // 2 - bbox[0]
        y = (size - h) // 2 - bbox[1]
        draw.text((x, y), char, fill=0, font=render_font)
        if is_reflect:
            img = img.transpose(Image.FLIP_LEFT_RIGHT)

        img_np = np.array(img)
        if np.unique(img_np).size == 1:
            return None

        return img

    def match_text_by_embedding(
        self,
        images: Union[Image.Image, List[Image.Image]],
        top_k: int = 1,
    ) -> Union[List[Tuple[str, float]], List[List[Tuple[str, float]]]]:
        """
        Match input image to precomputed character embeddings using cosine similarity.

        :param images: a PIL.Image or a list of PIL.Image to match
        :param top_k: int, how many top matches to return

        :return:
        - If a single Image was passed in,
                returns a list of (label, score) tuples sorted descending.

        - If a list of Images was passed in, returns a list of such lists.
        """
        if self._global_vec_db is None:
            return []
        try:
            imgs: List[Image.Image] = (
                [images] if isinstance(images, Image.Image) else images
            )

            # Convert images to normalized 1D vectors
            vecs = []
            for img in imgs:
                pil_gray = img.convert("L").resize(self._global_vec_shape)
                arr = np.asarray(pil_gray, dtype=np.float32) / 255.0
                v = array_backend.asarray(arr).ravel()
                v /= array_backend.linalg.norm(v) + 1e-6
                vecs.append(v)

            batch = array_backend.stack(vecs, axis=0)  # (N, D)
            # Compute all cosine similarities in one batch:
            sims_batch = batch.dot(self._global_vec_db.T)  # (N, num_chars)

            all_results: List[List[Tuple[str, float]]] = []
            for sims in sims_batch:
                k = min(top_k, sims.shape[0])
                top_unsorted = array_backend.argpartition(-sims, k - 1)[:k]
                top_idx = top_unsorted[array_backend.argsort(-sims[top_unsorted])]
                results = [
                    (self._global_vec_label[int(i)], float(sims[int(i)]))
                    for i in top_idx
                ]
                all_results.append(results)

            # Unwrap single-image case
            return all_results[0] if isinstance(images, Image.Image) else all_results
        except Exception as e:
            logger.warning("[FontOCR] Error: %s", e)
            default = [("", 0.0)]
            if isinstance(images, Image.Image):
                return default
            else:
                return [default for _ in range(len(images))]

    def run_ocr_on_images(
        self,
        images: Union[Image.Image, List[Image.Image]],
    ) -> Union[Tuple[str, float], List[Tuple[str, float]]]:
        """
        Run OCR on one or more PIL.Image(s) and return recognized text with confidence

        :param images: A single PIL.Image or list of PIL.Images to recognize.
        :return:
        - If a single image is passed, returns Tuple[str, float].

        - If a list is passed, returns List[Tuple[str, float]].
        """
        if self._global_ocr is None:
            return []
        try:
            # Normalize input to a list of numpy arrays (RGB)
            img_list = [images] if isinstance(images, Image.Image) else images
            np_imgs: List[np.ndarray] = [
                np.array(img.convert("RGB")) for img in img_list
            ]

            # Run OCR
            ocr_results = self._global_ocr(np_imgs)

            # Return result depending on input type
            return ocr_results if isinstance(images, list) else ocr_results[0]

        except Exception as e:
            logger.warning("[FontOCR] OCR failed: %s", e)
            fallback = ("", 0.0)
            return (
                fallback
                if isinstance(images, Image.Image)
                else [fallback for _ in images]
            )

    def query(
        self,
        images: Union[Image.Image, List[Image.Image]],
        top_k: int = 3,
    ) -> Union[List[Tuple[str, float]], List[List[Tuple[str, float]]]]:
        """
        For each input image, run OCR + embedding match, fuse scores,
        and return a sorted list of (char, score) above self.threshold.
        """
        # normalize to list
        single = isinstance(images, Image.Image)
        imgs: List[Image.Image] = [images] if single else images

        # try the hash store
        hash_batch = [img_hash_store.query(img, k=top_k) or [] for img in imgs]

        fallback_indices = [i for i, h in enumerate(hash_batch) if not h]
        fallback_imgs = [imgs[i] for i in fallback_indices]

        # OCR scores
        raw_ocr: Union[Tuple[str, float], List[Tuple[str, float]]] = (
            self.run_ocr_on_images(fallback_imgs)
            if (self.use_ocr and fallback_imgs)
            else []
        )
        if isinstance(raw_ocr, tuple):
            ocr_fallback: List[Tuple[str, float]] = [raw_ocr]
        else:
            ocr_fallback = raw_ocr

        # Vec‐embedding scores
        raw_vec: Union[List[Tuple[str, float]], List[List[Tuple[str, float]]]] = (
            self.match_text_by_embedding(fallback_imgs, top_k=top_k)
            if (self.use_vec and fallback_imgs)
            else []
        )
        if raw_vec and isinstance(raw_vec[0], tuple):
            vec_fallback: List[List[Tuple[str, float]]] = [raw_vec]  # type: ignore
        else:
            vec_fallback = raw_vec  # type: ignore

        # Fuse OCR+vector for the fallback set
        fused_fallback: List[List[Tuple[str, float]]] = []
        for ocr_preds, vec_preds in zip(ocr_fallback, vec_fallback):
            scores: Dict[str, float] = {}

            # OCR weight
            if ocr_preds:
                ch, s = ocr_preds
                scores[ch] = scores.get(ch, 0.0) + self.ocr_weight * s
                logger.debug(
                    "[FontOCR] OCR with weight: scores[%s] = %s", ch, scores[ch]
                )
            # Vec weight
            for ch, s in vec_preds:
                scores[ch] = scores.get(ch, 0.0) + self.vec_weight * s
                logger.debug(
                    "[FontOCR] Vec with weight: scores[%s] = %s", ch, scores[ch]
                )
            # Optional frequency
            if self.use_freq:
                for ch in list(scores):
                    level = self._global_char_freq_db.get(ch, self._max_freq)
                    freq_score = (self._max_freq - level) / max(1, self._max_freq)
                    scores[ch] += self._freq_weight * freq_score
                    logger.debug(
                        "[FontOCR] After Freq weight: scores[%s] = %s", ch, scores[ch]
                    )

            # Threshold + sort + top_k
            filtered = [(ch, sc) for ch, sc in scores.items() if sc >= self.threshold]
            filtered.sort(key=lambda x: -x[1])

            fused_fallback.append(filtered[:top_k])

        # Recombine hash hits + fallback in original order
        fused_batch: List[List[Tuple[str, float]]] = []
        fallback_iter = iter(fused_fallback)
        for h_preds in hash_batch:
            if h_preds:
                fused_batch.append(h_preds)
            else:
                fused_batch.append(next(fallback_iter))

        # Unwrap single‐image case
        return fused_batch[0] if single else fused_batch

    def _chunked(self, seq: List[T], size: int) -> Generator[List[T], None, None]:
        """Yield successive chunks of `seq` of length `size`."""
        for i in range(0, len(seq), size):
            yield seq[i : i + size]

    def generate_font_map(
        self,
        fixed_font_path: Union[str, Path],
        random_font_path: Union[str, Path],
        char_set: Set[str],
        refl_set: Set[str],
        chapter_id: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Generates a mapping from encrypted (randomized) font characters to
        their real recognized characters by rendering and OCR-based matching.

        :param fixed_font_path: Path to the reference (fixed) font.
        :param random_font_path: Path to the obfuscated (random) font.
        :param char_set: Characters to process normally.
        :param refl_set: Characters to process as horizontally flipped.
        :param chapter_id: Chapter ID

        :returns mapping_result: { obf_char: real_char, ... }
        """
        mapping_result: Dict[str, str] = {}
        fixed_map_file = self._fixed_map_dir / f"{Path(fixed_font_path).stem}.json"

        # load existing cache
        try:
            with open(fixed_map_file, "r", encoding="utf-8") as f:
                fixed_map = json.load(f)
        except Exception:
            fixed_map = {}

        # prepare font renderers and cmap sets
        try:
            fixed_ttf = TTFont(fixed_font_path)
            fixed_chars = set(chr(c) for c in fixed_ttf.getBestCmap().keys())
            fixed_font = ImageFont.truetype(str(fixed_font_path), self.CHAR_FONT_SIZE)

            random_ttf = TTFont(random_font_path)
            random_chars = set(chr(c) for c in random_ttf.getBestCmap().keys())
            random_font = ImageFont.truetype(str(random_font_path), self.CHAR_FONT_SIZE)
        except Exception as e:
            logger.error("[FontOCR] Failed to load TTF fonts: %s", e)
            return mapping_result

        def _render_batch(
            chars: List[Tuple[str, bool]]
        ) -> List[Tuple[str, Image.Image]]:
            out = []
            for ch, reflect in chars:
                if ch in fixed_chars:
                    font = fixed_font
                elif ch in random_chars:
                    font = random_font
                else:
                    continue
                img = self._generate_char_image(ch, font, reflect)
                if img is not None:
                    out.append((ch, img))
            return out

        # process normal and reflected sets together
        debug_idx = 1
        for chars, reflect in [(list(char_set), False), (list(refl_set), True)]:
            for batch_chars in self._chunked(chars, self.batch_size):
                # render all images in this batch
                to_render = [(ch, reflect) for ch in batch_chars]
                rendered = _render_batch(to_render)
                if not rendered:
                    continue

                # query OCR+vec simultaneously
                imgs_to_query = [img for (ch, img) in rendered]
                fused_raw = self.query(imgs_to_query, top_k=3)
                if isinstance(fused_raw[0], tuple):
                    fused: List[List[Tuple[str, float]]] = [fused_raw]  # type: ignore
                else:
                    fused = fused_raw  # type: ignore

                # pick best per char, apply threshold + cache
                for (ch, img), preds in zip(rendered, fused):
                    if ch in fixed_map:
                        mapping_result[ch] = fixed_map[ch]
                        logger.debug(
                            "[FontOCR] Using cached mapping: '%s' -> '%s'",
                            ch,
                            fixed_map[ch],
                        )
                        continue
                    if not preds:
                        if self.font_debug and chapter_id:
                            dbg_path = (
                                self._debug_dir / f"{chapter_id}_{debug_idx:04d}.png"
                            )
                            img.save(dbg_path)
                            logger.debug(
                                "[FontOCR] Saved debug image for '%s': %s", ch, dbg_path
                            )
                            debug_idx += 1
                        continue
                    real_char, _ = preds[0]
                    mapping_result[ch] = real_char
                    fixed_map[ch] = real_char
                    if self.font_debug:
                        logger.debug(
                            "[FontOCR] Prediction for char '%s': top_pred='%s'",
                            ch,
                            real_char,
                        )
                        logger.debug("[FontOCR] All predictions: %s", preds)

        # persist updated fixed_map
        try:
            with open(fixed_map_file, "w", encoding="utf-8") as f:
                json.dump(fixed_map, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error("[FontOCR] Failed to save fixed map: %s", e)

        return mapping_result
