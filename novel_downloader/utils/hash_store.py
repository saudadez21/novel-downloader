#!/usr/bin/env python3
"""
novel_downloader.utils.hash_store
---------------------------------

Manage a small collection of image perceptual hashes and their labels.
Supports loading/saving to .json or .npy, and basic CRUD + search.
"""

import heapq
import json
import logging
from collections.abc import Callable
from pathlib import Path

from PIL import Image

from .constants import HASH_STORE_FILE
from .hash_utils import HASH_DISTANCE_THRESHOLD, fast_hamming_distance, phash

logger = logging.getLogger(__name__)


class _BKNode:
    """
    A node in a Burkhard-Keller tree (BK-Tree) for distance search.
    Stores one value and a dict of children keyed by distance.
    """

    __slots__ = ("value", "children")

    def __init__(self, value: int):
        self.value = value
        self.children: dict[int, _BKNode] = {}

    def add(self, h: int, dist_fn: Callable[[int, int], int]) -> None:
        d = dist_fn(h, self.value)
        child = self.children.get(d)
        if child is not None:
            child.add(h, dist_fn)
        else:
            self.children[d] = _BKNode(h)

    def query(
        self,
        target: int,
        threshold: int,
        dist_fn: Callable[[int, int], int],
    ) -> list[tuple[int, int]]:
        """
        Recursively collect (value, dist) pairs within threshold.
        """
        d0 = dist_fn(target, self.value)
        matches: list[tuple[int, int]] = []
        if d0 <= threshold:
            matches.append((self.value, d0))
        # Only children whose edge-dist \in [d0-threshold, d0+threshold]
        lower, upper = d0 - threshold, d0 + threshold
        for edge, child in self.children.items():
            if lower <= edge <= upper:
                matches.extend(child.query(target, threshold, dist_fn))
        return matches


class ImageHashStore:
    """
    Store and manage image hashes grouped by label, with a BK-Tree index.

    :param path: file path for persistence (".json" or ".npy")
    :param auto_save: if True, every modification automatically calls save()
    :param hash_func: function to compute hash from PIL.Image
    :param ham_dist: function to compute Hamming distance between two hashes
    """

    def __init__(
        self,
        path: str | Path = HASH_STORE_FILE,
        auto_save: bool = False,
        hash_func: Callable[[Image.Image], int] = phash,
        ham_dist: Callable[[int, int], int] = fast_hamming_distance,
        threshold: int = HASH_DISTANCE_THRESHOLD,
    ) -> None:
        self._path = Path(path)
        self._auto = auto_save
        self._hf = hash_func
        self._hd = ham_dist
        self._th = threshold

        # label -> set of hashes
        self._hash: dict[str, set[int]] = {}
        # hash -> list of labels (for reverse lookup)
        self._hash_to_labels: dict[int, list[str]] = {}
        # root of BK-Tree (or None if empty)
        self._bk_root: _BKNode | None = None

        self.load()

    def load(self) -> None:
        """Load store from disk and rebuild BK-Tree index."""
        if not self._path.exists():
            self._hash.clear()
            logger.debug(
                "[ImageHashStore] No file found at %s, starting empty.", self._path
            )
            return

        txt = self._path.read_text(encoding="utf-8")
        obj = json.loads(txt) or {}
        self._hash = {lbl: set(obj.get(lbl, [])) for lbl in obj}

        # rebuild reverse map and BK-Tree
        self._hash_to_labels.clear()
        for lbl, hs in self._hash.items():
            for h in hs:
                self._hash_to_labels.setdefault(h, []).append(lbl)
        logger.debug(
            "[ImageHashStore] Loaded hash store from %s with %d hashes",
            self._path,
            sum(len(v) for v in self._hash.values()),
        )

        self._build_index()

    def _build_index(self) -> None:
        """Construct a BK-Tree over all stored hashes."""
        self._bk_root = None
        for h in self._hash_to_labels:
            if self._bk_root is None:
                self._bk_root = _BKNode(h)
            else:
                self._bk_root.add(h, self._hd)
        logger.debug(
            "[ImageHashStore] BK-tree index built with %d unique hashes",
            len(self._hash_to_labels),
        )

    def save(self) -> None:
        """Persist current store to disk."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = {lbl: list(s) for lbl, s in self._hash.items()}
        txt = json.dumps(data, ensure_ascii=False, indent=2)
        self._path.write_text(txt, encoding="utf-8")
        logger.debug("[ImageHashStore] Saved hash store to %s", self._path)

    def _maybe_save(self) -> None:
        if self._auto:
            self.save()

    def add_image(self, img_path: str | Path, label: str) -> int:
        """
        Compute hash for the given image and add it under `label`.
        Updates BK-Tree index incrementally.
        """
        img = Image.open(img_path).convert("L")
        h = self._hf(img)
        self._hash.setdefault(label, set()).add(h)
        self._hash_to_labels.setdefault(h, []).append(label)
        # insert into BK-Tree
        if self._bk_root is None:
            self._bk_root = _BKNode(h)
        else:
            self._bk_root.add(h, self._hd)
        logger.debug("[ImageHashStore] Added hash %d under label '%s'", h, label)
        self._maybe_save()
        return h

    def add_from_map(self, map_path: str | Path) -> None:
        """
        Load a JSON file of the form { "image_path": "label", ... }
        and add each entry.
        """
        map_path = Path(map_path)
        text = map_path.read_text(encoding="utf-8")
        mapping = json.loads(text)
        for rel_img_path, lbl in mapping.items():
            img_path = (map_path.parent / rel_img_path).resolve()
            try:
                self.add_image(img_path, lbl)
            except Exception as e:
                logger.warning(
                    "[ImageHashStore] Failed to add image '%s': %s", img_path, str(e)
                )
                continue

    def labels(self) -> list[str]:
        """Return a sorted list of all labels in the store."""
        return sorted(self._hash.keys())

    def hashes(self, label: str) -> set[int]:
        """Return the set of hashes for a given `label` (empty set if none)."""
        return set(self._hash.get(label, ()))

    def remove_label(self, label: str) -> None:
        """Remove all hashes associated with `label`."""
        if label in self._hash:
            del self._hash[label]
            logger.debug("[ImageHashStore] Removed label '%s'", label)
            self._maybe_save()

    def remove_hash(self, label: str, this: int | str | Path) -> bool:
        """
        Remove a specific hash under `label`.
        `this` can be:
         - an integer hash
         - a Path (image file) -> will compute its hash then remove
        Returns True if something was removed.
        """
        if label not in self._hash:
            return False

        h = None
        if isinstance(this, (str | Path)):
            try:
                img = Image.open(this).convert("L")
                h = self._hf(img)
            except Exception as e:
                logger.warning(
                    "[ImageHashStore] Could not open image '%s': %s", this, str(e)
                )
                return False
        else:
            h = int(this)

        if h in self._hash[label]:
            self._hash[label].remove(h)
            logger.debug("[ImageHashStore] Removed hash %d from label '%s'", h, label)
            self._maybe_save()
            return True
        return False

    def query(
        self,
        target: int | str | Path | Image.Image,
        k: int = 1,
        threshold: int | None = None,
    ) -> list[tuple[str, float]]:
        """
        Find up to `k` distinct labels whose stored hashes are most similar
        to `target` within `threshold`. Returns a list of (label, score),
        sorted by descending score. Each label appears at most once.

        :param target: Image path / int hash / PIL.Image
        :param k: number of labels to return (default=1)
        :param threshold: Hamming distance cutoff (default=self._th)
        """
        if threshold is None:
            threshold = self._th

        # compute target hash
        if isinstance(target, Image.Image):
            img = target.convert("L")
            thash = self._hf(img)
        elif isinstance(target, (str | Path)):
            img = Image.open(target).convert("L")
            thash = self._hf(img)
        else:
            thash = int(target)

        if self._bk_root is None:
            return []

        # find all (hash,dist) within threshold
        matches = self._bk_root.query(thash, threshold, self._hd)

        # collapse to one best dist per label
        best_per_label: dict[str, float] = {}
        h2l = self._hash_to_labels
        for h, dist in matches:
            for lbl in h2l.get(h, ()):
                score = 1.0 - dist / threshold
                prev = best_per_label.get(lbl)
                if prev is None or score > prev:
                    best_per_label[lbl] = score

        top_k = heapq.nsmallest(k, best_per_label.items(), key=lambda x: x[1])
        return top_k


img_hash_store = ImageHashStore()
