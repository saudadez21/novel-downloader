#!/usr/bin/env python3
"""
novel_downloader.core.parsers.qidian.chapter_encrypted
------------------------------------------------------

Support for parsing encrypted chapters from Qidian using font OCR mapping,
CSS rules, and custom rendering logic.
"""

from __future__ import annotations

import json
import logging
import re
from contextlib import suppress
from typing import TYPE_CHECKING, TypedDict

from lxml import html

from novel_downloader.models import ChapterDict
from novel_downloader.utils import (
    download,
    truncate_half_lines,
)

from .utils import (
    extract_chapter_info,
    find_ssr_page_context,
    get_decryptor,
    is_duplicated,
    vip_status,
)
from .utils.fontmap_recover import (
    apply_font_mapping,
    generate_font_map,
)

if TYPE_CHECKING:
    from .main_parser import QidianParser

logger = logging.getLogger(__name__)
_RE_ATTR = re.compile(r"attr\(\s*([^)]+?)\s*\)", re.I)
_RE_SCALEX = re.compile(r"scalex\(\s*-?1\s*\)", re.I)


class Rule(TypedDict, total=False):
    delete_all: bool
    delete_first: bool
    transform_flip_x: bool
    append_start_char: str
    append_end_char: str
    append_start_attr: str
    append_end_attr: str


class Rules(TypedDict):
    # e.g., orders = ["i", "em", "span"]
    orders: list[str]
    # e.g., sy["sy-3"] -> Rule
    sy: dict[str, Rule]
    # e.g., p_rules["p3"]["i"] -> Rule
    p_rules: dict[str, dict[str, Rule]]


def parse_encrypted_chapter(
    parser: QidianParser,
    html_str: str,
    chapter_id: str,
) -> ChapterDict | None:
    """
    Extract and return the formatted textual content of an encrypted chapter.

    Steps:
    1. Load SSR JSON context for CSS, fonts, and metadata.
    3. Decode and save randomFont bytes; download fixedFont via download_font().
    4. Extract paragraph structures and save debug JSON.
    5. Parse CSS rules and save debug JSON.
    6. Render encrypted paragraphs, then run OCR font-mapping.
    7. Extracts paragraph texts and formats them.

    :param html_str: Raw HTML content of the chapter page.
    :return: Formatted chapter text or empty string if not parsable.
    """
    try:
        if not parser._decode_font:
            return None
        ssr_data = find_ssr_page_context(html_str)
        chapter_info = extract_chapter_info(ssr_data)
        if not chapter_info:
            logger.warning(
                "[Parser] ssr_chapterInfo not found for chapter '%s'", chapter_id
            )
            return None

        debug_dir = parser._debug_dir / "font_debug" / "qidian" / chapter_id
        if parser.save_font_debug:
            debug_dir.mkdir(parents=True, exist_ok=True)

        css_str = chapter_info["css"]
        randomFont_str = chapter_info["randomFont"]
        fixedFontWoff2_url = chapter_info["fixedFontWoff2"]

        title = chapter_info.get("chapterName", "Untitled")
        duplicated = is_duplicated(ssr_data)
        raw_html = chapter_info.get("content", "")
        chapter_id = chapter_info.get("chapterId", chapter_id)
        fkp = chapter_info.get("fkp", "")
        author_say = chapter_info.get("authorSay", "")
        update_time = chapter_info.get("updateTime", "")
        update_timestamp = chapter_info.get("updateTimestamp", 0)
        modify_time = chapter_info.get("modifyTime", 0)
        word_count = chapter_info.get("actualWords", 0)
        seq = chapter_info.get("seq", None)
        volume = chapter_info.get("extra", {}).get("volumeName", "")

        # extract + save font
        rf = json.loads(randomFont_str)
        rand_path = parser._base_cache_dir / "randomFont.ttf"
        rand_path.parent.mkdir(parents=True, exist_ok=True)
        rand_path.write_bytes(bytes(rf["data"]))

        fixed_path = download(
            url=fixedFontWoff2_url,
            target_dir=parser._fixed_font_dir,
            stream=True,
        )
        if fixed_path is None:
            raise ValueError("fixed_path is None: failed to download font")

        # Extract and render paragraphs from HTML with CSS rules
        if vip_status(ssr_data):
            try:
                decryptor = get_decryptor()
                raw_html = decryptor.decrypt(
                    raw_html,
                    chapter_id,
                    fkp,
                    parser._fuid,
                )
            except Exception as e:
                logger.error("[Parser] decryption failed for '%s': %s", chapter_id, e)
                return None

        css_rules = parse_css_rules(css_str)
        paragraphs_str, refl_list = render_visible_text(raw_html, css_rules)
        if parser.save_font_debug:
            paragraphs_str_path = debug_dir / f"{chapter_id}_debug.txt"
            paragraphs_str_path.write_text(paragraphs_str, encoding="utf-8")

        # Run OCR + fallback mapping
        char_set = {c for c in paragraphs_str if c not in {" ", "\n", "\u3000"}}
        refl_set = set(refl_list)
        char_set = char_set - refl_set
        if parser.save_font_debug:
            char_sets_path = debug_dir / "char_set_debug.txt"
            temp = f"char_set:\n{char_set}\n\nrefl_set:\n{refl_set}"
            char_sets_path.write_text(
                temp,
                encoding="utf-8",
            )

        mapping_result = generate_font_map(
            fixed_font_path=fixed_path,
            random_font_path=rand_path,
            char_set=char_set,
            refl_set=refl_set,
            cache_dir=parser._base_cache_dir,
            batch_size=parser._config.batch_size,
        )
        if not mapping_result:
            return None

        if parser.save_font_debug:
            mapping_json_path = debug_dir / "font_mapping.json"
            mapping_json_path.write_text(
                json.dumps(mapping_result, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        # Reconstruct final readable text
        original_text = apply_font_mapping(
            text=paragraphs_str,
            font_map=mapping_result,
        )

        final_paragraphs_str = "\n".join(
            line.strip() for line in original_text.splitlines() if line.strip()
        )
        if parser._use_truncation and duplicated:
            final_paragraphs_str = truncate_half_lines(final_paragraphs_str)

        return {
            "id": str(chapter_id),
            "title": str(title),
            "content": final_paragraphs_str,
            "extra": {
                "author_say": author_say.strip() if author_say else "",
                "updated_at": update_time,
                "update_timestamp": update_timestamp,
                "modify_time": modify_time,
                "word_count": word_count,
                "duplicated": duplicated,
                "seq": seq,
                "volume": volume,
                "encrypted": True,
            },
        }

    except Exception as e:
        logger.warning(
            "[Parser] parse error for encrypted chapter '%s': %s", chapter_id, e
        )
    return None


def _only_tag(selector: str) -> str | None:
    """
    Normalize a selector into just its tag name for ordering.

    Handles forms like 'i', 'em::before', '.p3 i', '.p2 span::after'.

    Returns None if can't extract a tag.
    """
    sel = selector.strip()
    # If it has spaces, take the rightmost simple selector
    last = sel.split()[-1]
    # Drop ::pseudo
    last = last.split("::", 1)[0]
    # If it's like 'span[attr=..]' keep 'span'
    last = last.split("[", 1)[0]
    # If it starts with '.', it's not a tag
    if not last or last.startswith("."):
        return None
    return last


def _parse_decls(block: str) -> list[tuple[str, str]]:
    """
    Parse 'name:value;...' inside a block. Tolerates quotes and attr().
    """
    decls: list[tuple[str, str]] = []
    i = 0
    n = len(block)
    name: list[str] = []
    val: list[str] = []
    in_name = True
    quote = None  # track ' or "
    while i < n:
        c = block[i]
        if quote:
            # inside quotes
            if c == "\\" and i + 1 < n:
                # keep escaped char
                (name if in_name else val).append(c)
                i += 1
                (name if in_name else val).append(block[i])
            elif c == quote:
                (name if in_name else val).append(c)
                quote = None
            else:
                (name if in_name else val).append(c)
        else:
            if c in ("'", '"'):
                (name if in_name else val).append(c)
                quote = c
            elif in_name and c == ":":
                in_name = False
            elif c == ";":
                nm = "".join(name).strip().lower()
                vl = "".join(val).strip()
                if nm:
                    decls.append((nm, vl))
                name.clear()
                val.clear()
                in_name = True
            else:
                (name if in_name else val).append(c)
        i += 1

    if name or val:
        nm = "".join(name).strip().lower()
        vl = "".join(val).strip()
        if nm:
            decls.append((nm, vl))
    return decls


def parse_css_rules(css_str: str) -> Rules:
    """
    Produces normalized Rules with:
      - orders: list[str] of tag names sorted by numeric 'order'
      - sy: '.sy-*' class rules
      - p_rules: '.p* <tag>' rules, indexed by p-class then tag
    """
    rules: Rules = {"orders": [], "sy": {}, "p_rules": {}}
    order_pairs: list[tuple[str, int]] = []

    i = 0
    while True:
        b1 = css_str.find("{", i)
        if b1 == -1:
            break
        selector = css_str[i:b1].strip().lower()
        b2 = css_str.find("}", b1 + 1)
        if b2 == -1:
            break
        block = css_str[b1 + 1 : b2]
        i = b2 + 1

        decls = _parse_decls(block)

        new_rule: Rule = {}
        order_val: int | None = None

        for name, value in decls:
            v = value.strip()
            if name == "font-size" and v == "0":
                if "::first-letter" in selector:
                    new_rule["delete_first"] = True
                else:
                    new_rule["delete_all"] = True
            elif name == "transform":
                if _RE_SCALEX.search(v.replace(" ", "")):
                    new_rule["transform_flip_x"] = True
            elif name == "order":
                with suppress(ValueError, TypeError):
                    order_val = int(v)
            elif name == "content":
                # normalize: remove outer quotes
                if "::after" in selector:
                    m = _RE_ATTR.search(v)
                    if m:
                        new_rule["append_end_attr"] = m.group(1)
                    else:
                        s = v.strip().strip("\"'")
                        new_rule["append_end_char"] = s
                elif "::before" in selector:
                    m = _RE_ATTR.search(v)
                    if m:
                        new_rule["append_start_attr"] = m.group(1)
                    else:
                        s = v.strip().strip("\"'")
                        new_rule["append_start_char"] = s

        # classification
        if selector.startswith(".sy-"):
            key = selector.lstrip(".")
            old = rules["sy"].get(key)
            rules["sy"][key] = {**old, **new_rule} if old else (new_rule or {})

        elif selector.startswith(".p") and " " in selector:
            p_cls, right = selector.split(" ", 1)
            p_cls = p_cls.lstrip(".")
            tag = _only_tag(right)
            if tag:
                prev = rules["p_rules"].setdefault(p_cls, {}).get(tag)
                rules["p_rules"][p_cls][tag] = (
                    {**prev, **new_rule} if prev else (new_rule or {})
                )

        if order_val is not None:
            tag_for_order = _only_tag(selector)
            if tag_for_order:
                order_pairs.append((tag_for_order, order_val))

    # normalize orders
    order_pairs.sort(key=lambda t: t[1])
    seen = set()
    orders: list[str] = []
    for tag, _num in order_pairs:
        if tag not in seen:
            seen.add(tag)
            orders.append(tag)
    rules["orders"] = orders
    return rules


def render_visible_text(html_str: str, rules: Rules) -> tuple[str, list[str]]:
    """
    Renderer the HTML using pre-parsed Rules.
    """
    tree = html.fromstring(html_str)
    paragraphs_out: list[str] = []
    refl_list: list[str] = []
    orders = rules.get("orders") or []
    p_rules = rules.get("p_rules") or {}
    sy_rules = rules.get("sy") or {}

    def _class_list(el: html.HtmlElement) -> list[str]:
        cls = el.get("class")
        return cls.split() if cls else []

    def _apply_rule(el: html.HtmlElement, rule: Rule) -> str:
        if rule.get("delete_all"):
            return ""

        parts: list[str] = []
        if "append_start_char" in rule:
            parts.append(rule["append_start_char"])
        if "append_start_attr" in rule:
            parts.append(el.get(rule["append_start_attr"], ""))

        text = el.text or ""
        if rule.get("delete_first") and text:
            text = text[1:]
        parts.append(text)

        if "append_end_char" in rule:
            parts.append(rule["append_end_char"])
        if "append_end_attr" in rule:
            parts.append(el.get(rule["append_end_attr"], ""))

        s = "".join(parts)

        if rule.get("transform_flip_x") and s:
            refl_list.append(s)

        return s

    for p in tree.findall(".//p"):
        p_classes = _class_list(p)
        p_key = next((c for c in p_classes if c.startswith("p")), None)
        has_ordered_rules = p_key in p_rules

        buf_parts: list[str] = []

        if p.text and not has_ordered_rules:
            buf_parts.append(p.text)

        ordered_cache: dict[str, list[str]] = {}

        for child in p:
            tag = str(child.tag)

            # Handle inline <y class="sy-*"> spans
            if tag == "y" and not has_ordered_rules:
                y_cls = next(
                    (c for c in _class_list(child) if c.startswith("sy-")), None
                )
                if y_cls and y_cls in sy_rules:
                    buf_parts.append(_apply_rule(child, sy_rules[y_cls]))
                else:
                    buf_parts.append(child.text or "")
                if child.tail:
                    buf_parts.append(child.tail)
                continue

            # Handle ordered paragraphs: only cache tags that appear in `orders`
            if p_key and has_ordered_rules and tag in orders:
                rule = p_rules[p_key].get(tag, {})
                ordered_cache.setdefault(tag, []).append(_apply_rule(child, rule))
                continue

            # Non-ordered, non-<y> nodes: include text + tails as-is
            if not has_ordered_rules:
                buf_parts.append(child.text or "")
                if child.tail:
                    buf_parts.append(child.tail)

        # If ordered, flush in global orders with all duplicates preserved
        if has_ordered_rules:
            for tag in orders:
                if tag in ordered_cache:
                    buf_parts.extend(ordered_cache[tag])

        para = "".join(buf_parts)
        if para:
            paragraphs_out.append(para)

    return "\n".join(paragraphs_out), refl_list
