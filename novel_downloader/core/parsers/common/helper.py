#!/usr/bin/env python3
"""
novel_downloader.core.parsers.common.helper
-------------------------------------------

Shared utility functions for parsing Common pages.
"""

import logging
import re
from collections.abc import Iterable, Iterator
from typing import Any, cast

from bs4 import BeautifulSoup, Tag

from novel_downloader.models import (
    BookInfoRules,
    FieldRules,
    RuleStep,
    VolumesRules,
)

logger = logging.getLogger(__name__)


def html_to_soup(html_str: str) -> BeautifulSoup:
    """
    Convert an HTML string to a BeautifulSoup object with fallback.

    :param html_str: Raw HTML string.
    :return: Parsed BeautifulSoup object.
    """
    try:
        return BeautifulSoup(html_str, "lxml")
    except Exception as e:
        logger.warning("[Parser] lxml parse failed, falling back: %s", e)
        return BeautifulSoup(html_str, "html.parser")


class HTMLExtractor:
    """
    HTML extraction engine that applies a sequence of RuleSteps to
    pull data out of a page.
    """

    def __init__(self, html: str):
        self._html = html
        self._soup = html_to_soup(html)

    def extract_book_info(self, rules: BookInfoRules) -> dict[str, Any]:
        """
        Extract structured book information from HTML according to the given rules.

        Only non-empty fields in the rules are processed.

        :param rules: Extraction configuration specifying how to extract.
        :return: A dictionary containing extracted book information.
        """
        book_info: dict[str, Any] = {}

        for field_name, field_rules in rules.items():
            if field_rules is None:
                continue

            if field_name == "volumes":
                book_info[field_name] = self.extract_volumes_structure(
                    cast(VolumesRules, field_rules)
                )
            else:
                steps = cast(FieldRules, field_rules)["steps"]
                book_info[field_name] = self.extract_field(steps)

        return book_info

    def extract_field(self, steps: list[RuleStep]) -> str:
        """
        Execute a list of extraction steps on the given HTML.

        - If any step yields None, stops processing further steps.
        - At the end, always returns a str:
        * If current is a list, converts items to text and joins with '\n'.
        * If current is a Tag, extracts its .get_text().
        * Else, uses str().
        """

        def flatten_list(items: Iterable[Any]) -> Iterator[Any]:
            for item in items:
                if isinstance(item, list):
                    yield from flatten_list(item)
                else:
                    yield item

        def to_text(item: Any) -> str:
            if isinstance(item, Tag):
                return str(item.get_text().strip())
            return str(item).strip()

        current: Any = self._soup

        for step in steps:
            t = step.get("type")
            if t == "select_one":
                sel = step.get("selector")
                current = current.select_one(sel) if sel else None

            elif t == "select":
                sel = step.get("selector")
                lst = current.select(sel) if sel else []
                idx = step.get("index")
                current = lst[idx] if idx is not None and idx < len(lst) else lst

            elif t == "exclude":
                sel = step.get("selector")
                for elem in current.select(sel or ""):
                    elem.decompose()

            elif t == "find":
                nm = step.get("name")
                attrs = step.get("attrs") or {}
                current = current.find(nm, attrs=attrs)

            elif t == "find_all":
                nm = step.get("name")
                attrs = step.get("attrs") or {}
                lst = current.find_all(nm, attrs=attrs, limit=step.get("limit"))
                idx = step.get("index")
                current = lst[idx] if idx is not None and idx < len(lst) else lst

            elif t == "text":
                if isinstance(current, list):
                    current = [elem.get_text() for elem in current]
                elif isinstance(current, Tag):
                    current = current.get_text()

            elif t == "strip":
                chars = step.get("chars")
                if isinstance(current, list):
                    current = [c.strip(chars) for c in current]
                elif isinstance(current, str):
                    current = current.strip(chars)

            elif t == "regex":
                txt = str(current or "")
                pat = step.get("pattern") or ""
                flags = step.get("flags")
                flags = flags if flags is not None else 0
                match = re.compile(pat, flags).search(txt)
                if match:
                    template = step.get("template")
                    if template:
                        s = template
                        for i in range(1, len(match.groups()) + 1):
                            s = s.replace(f"${i}", match.group(i) or "")
                        current = s
                    else:
                        grp = step.get("group")
                        grp = grp if grp is not None else 0
                        current = match.group(grp)
                else:
                    current = ""

            elif t == "replace":
                old = step.get("old")
                old = old if old is not None else ""

                new = step.get("new")
                new = new if new is not None else ""

                cnt = step.get("count")
                cnt = cnt if cnt is not None else -1

                if isinstance(current, list):
                    current = [c.replace(old, new, cnt) for c in current]
                elif isinstance(current, str):
                    current = current.replace(old, new, cnt)

            elif t == "split":
                sep = step.get("sep", "")
                idx = step.get("index")
                idx = idx if idx is not None else 0
                parts = (current or "").split(sep)
                current = parts[idx] if idx < len(parts) else ""

            elif t == "join":
                sep = step.get("sep")
                sep = sep if sep is not None else ""
                if isinstance(current, list):
                    current = sep.join(current)

            elif t == "attr":
                name = step.get("attr") or ""
                if isinstance(current, list):
                    current = [elem.get(name, "") for elem in current]
                elif isinstance(current, Tag):
                    current = current.get(name, "")

            else:
                raise ValueError(f"Unsupported step type: {t}")

            if current is None:
                break

        # Final normalization
        if isinstance(current, list):
            flat = list(flatten_list(current))
            texts = [to_text(x) for x in flat if x is not None]
            return "\n".join(texts)
        if isinstance(current, Tag):
            return str(current.get_text().strip())
        return str(current or "").strip()

    def extract_mixed_volumes(self, volume_rule: VolumesRules) -> list[dict[str, Any]]:
        """
        Special mode: mixed <volume> and <chapter> under same parent.
        (e.g., dt / dd pattern in BiQuGe)
        """
        list_selector = volume_rule.get("list_selector")
        volume_selector = volume_rule.get("volume_selector")
        volume_name_steps = volume_rule.get("volume_name_steps")
        chapter_selector = volume_rule["chapter_selector"]
        chapter_steps_list = volume_rule["chapter_steps"]

        if not (
            list_selector and volume_selector and chapter_selector and volume_name_steps
        ):
            raise ValueError(
                "volume_mode='mixed' 时, 必须提供 list_selector, volume_selector, "
                "chapter_selector 和 volume_name_steps"
            )

        volumes: list[dict[str, Any]] = []
        current_volume: dict[str, Any] | None = None
        if not chapter_steps_list:
            chapter_steps_list = []
        chapter_info_steps = {item["key"]: item["steps"] for item in chapter_steps_list}

        list_area = self._soup.select_one(list_selector)
        if not list_area:
            raise ValueError(f"找不到 list_selector: {list_selector}")

        for elem in list_area.find_all(
            [volume_selector, chapter_selector], recursive=True
        ):
            if not isinstance(elem, Tag):
                continue
            if elem.name == volume_selector:
                extractor = HTMLExtractor(str(elem))
                volume_name = extractor.extract_field(volume_name_steps)
                current_volume = {"volume_name": volume_name, "chapters": []}
                volumes.append(current_volume)

            elif elem.name == chapter_selector and current_volume is not None:
                chap_extractor = HTMLExtractor(str(elem))
                chapter_data = {}
                for field, steps in chapter_info_steps.items():
                    chapter_data[field] = chap_extractor.extract_field(steps)
                current_volume["chapters"].append(chapter_data)

        return volumes

    def extract_volume_blocks(self, volume_rule: VolumesRules) -> list[dict[str, Any]]:
        volume_selector = volume_rule.get("volume_selector")
        volume_name_steps = volume_rule.get("volume_name_steps")
        chapter_selector = volume_rule["chapter_selector"]
        chapter_steps_list = volume_rule["chapter_steps"]
        if not (volume_selector and volume_name_steps):
            raise ValueError(
                "has_volume=True 时, 必须提供 volume_selector 和 volume_name_steps"
            )
        volumes = []
        chapter_info_steps = {item["key"]: item["steps"] for item in chapter_steps_list}
        for vol in self._soup.select(volume_selector):
            extractor = HTMLExtractor(str(vol))
            volume_name = extractor.extract_field(volume_name_steps)

            chapters = []
            for chap in vol.select(chapter_selector):
                chap_extractor = HTMLExtractor(str(chap))
                chapter_data = {}
                for field, steps in chapter_info_steps.items():
                    chapter_data[field] = chap_extractor.extract_field(steps)
                chapters.append(chapter_data)

            volumes.append({"volume_name": volume_name, "chapters": chapters})

        return volumes

    def extract_flat_chapters(self, volume_rule: VolumesRules) -> list[dict[str, Any]]:
        chapter_selector = volume_rule["chapter_selector"]
        chapter_steps_list = volume_rule["chapter_steps"]
        volume_selector = volume_rule.get("volume_selector")
        volumes = []
        chapter_info_steps = {item["key"]: item["steps"] for item in chapter_steps_list}

        if volume_selector:
            candidates = self._soup.select(volume_selector)
        else:
            candidates = [self._soup]

        all_chapters = []
        for area in candidates:
            for chap in area.select(chapter_selector):
                chap_extractor = HTMLExtractor(str(chap))
                chapter_data = {}
                for field, steps in chapter_info_steps.items():
                    chapter_data[field] = chap_extractor.extract_field(steps)
                all_chapters.append(chapter_data)

        volumes.append({"volume_name": "未分卷", "chapters": all_chapters})

        return volumes

    def extract_volumes_structure(
        self, volume_rule: VolumesRules
    ) -> list[dict[str, Any]]:
        volume_mode = volume_rule.get("volume_mode", "normal")
        if volume_mode == "mixed":
            return self.extract_mixed_volumes(volume_rule)

        if volume_rule.get("has_volume", True):
            return self.extract_volume_blocks(volume_rule)
        else:
            return self.extract_flat_chapters(volume_rule)
