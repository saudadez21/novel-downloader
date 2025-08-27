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
from contextlib import suppress
from typing import TYPE_CHECKING, TypedDict

import tinycss2
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
IGNORED_CLASS_LISTS = {"title", "review"}


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


def parse_css_rules(css_str: str) -> Rules:
    """
    Smaller, stricter CSS parsing tuned to the selectors you actually consume.
    Produces normalized Rules with:
      - orders: list[str] of tag names sorted by numeric 'order'
      - sy:     '.sy-*' class rules
      - p_rules: '.p* <tag>' rules, indexed by p-class then tag
    """
    rules: Rules = {"orders": [], "sy": {}, "p_rules": {}}
    stylesheet = tinycss2.parse_stylesheet(
        css_str, skip_comments=True, skip_whitespace=True
    )

    # Gather (tag, order_value) then sort once
    order_pairs: list[tuple[str, int]] = []

    for rule in stylesheet:
        if getattr(rule, "type", None) != "qualified-rule":
            continue

        selector_raw = tinycss2.serialize(rule.prelude).strip()
        decls = tinycss2.parse_declaration_list(rule.content)

        new_rule: Rule = {}
        order_val: int | None = None

        for decl in decls:
            if decl.type != "declaration":
                continue
            name = (decl.lower_name or "").strip()
            value = tinycss2.serialize(decl.value).strip()

            if name == "font-size" and value == "0":
                if "::first-letter" in selector_raw:
                    new_rule["delete_first"] = True
                else:
                    new_rule["delete_all"] = True
            elif name == "transform" and value.lower().replace(" ", "") == "scalex(-1)":
                new_rule["transform_flip_x"] = True
            elif name == "order":
                with suppress(ValueError, TypeError):
                    order_val = int(value)
            elif name == "content":
                if "::after" in selector_raw:
                    if "attr(" in value:
                        attr = value.split("attr(", 1)[1].split(")", 1)[0]
                        new_rule["append_end_attr"] = attr
                    else:
                        new_rule["append_end_char"] = value.strip("\"'")
                elif "::before" in selector_raw:
                    if "attr(" in value:
                        attr = value.split("attr(", 1)[1].split(")", 1)[0]
                        new_rule["append_start_attr"] = attr
                    else:
                        new_rule["append_start_char"] = value.strip("\"'")

        # classify selector
        if selector_raw.startswith(".sy-"):
            # e.g. ".sy-3"
            key = selector_raw.lstrip(".")
            old = rules["sy"].get(key)
            rules["sy"][key] = {**(old or {}), **(new_rule or {})}

        elif selector_raw.startswith(".p") and " " in selector_raw:
            # e.g. ".p3 i", ".p2 span::before"
            p_cls, right = selector_raw.split(" ", 1)
            p_cls = p_cls.lstrip(".")
            tag = _only_tag(right)
            if tag:
                prev = rules["p_rules"].setdefault(p_cls, {}).get(tag)
                rules["p_rules"][p_cls][tag] = {**(prev or {}), **(new_rule or {})}

        # orders (bare tag name with order)
        if order_val is not None:
            tag_for_order = _only_tag(selector_raw)
            if tag_for_order:
                order_pairs.append((tag_for_order, order_val))

    # normalize orders
    order_pairs.sort(key=lambda t: t[1])
    seen: set[str] = set()
    for tag, _n in order_pairs:
        if tag not in seen:
            seen.add(tag)
            rules["orders"].append(tag)
    return rules


def render_visible_text(html_str: str, rules: Rules) -> tuple[str, list[str]]:
    """
    Single-pass renderer over the HTML using pre-parsed Rules.
    Mirrors original semantics:
      - text nodes appended as-is
      - skip .review
      - special <y class="sy-*"> handled via sy rules
      - per-<p class="p*> piece ordering using rules.orders
      - capture reflected chars for OCR mapping
    """
    tree = html.fromstring(html_str)
    paragraphs_out: list[str] = []
    refl_list: list[str] = []

    def _class_list(el: html.HtmlElement) -> list[str]:
        cls = el.attrib.get("class", "")
        return cls.split() if isinstance(cls, str) else (cls or [])

    def _tag_name(el: html.HtmlElement) -> str:
        t = el.tag
        if isinstance(t, str):
            return t.split("}", 1)[-1]
        ln = getattr(t, "localname", None)
        return ln if isinstance(ln, str) else str(t).split("}", 1)[-1]

    def _apply_rule(el: html.HtmlElement, rule: Rule) -> str:
        if rule.get("delete_all", False):
            return ""

        # Text payload behavior: take element.text only
        s = el.text or ""

        if rule.get("delete_first", False):
            s = "" if len(s) <= 1 else s[1:]

        # end char / attr
        end_char = rule.get("append_end_char")
        if end_char:
            s += end_char
        end_attr = rule.get("append_end_attr")
        if end_attr:
            s += el.attrib.get(end_attr, "")

        # start char / attr
        start_char = rule.get("append_start_char")
        if start_char:
            s = start_char + s
        start_attr = rule.get("append_start_attr")
        if start_attr:
            s = el.attrib.get(start_attr, "") + s

        if rule.get("transform_flip_x", False) and s:
            refl_list.append(s)
        return s

    for p in tree.findall(".//p"):
        p_classes = _class_list(p)
        if any(c in IGNORED_CLASS_LISTS for c in p_classes):
            continue

        # identify the 'p*' class expected by rule tables
        p_key = next((c for c in p_classes if c.startswith("p")), None)

        buf_parts: list[str] = []
        ordered_cache: dict[str, str] = {}

        # leading text node on <p>
        if p.text:
            buf_parts.append(p.text)

        for child in p:
            child_tag = _tag_name(child)
            # skip span.review entirely (but keep its tail)
            if child_tag == "span":
                child_cls = _class_list(child)
                if "review" in child_cls:
                    if child.tail:
                        buf_parts.append(child.tail)
                    continue

            if child_tag == "y":
                # <y class="sy-*">
                y_cls = next(
                    (c for c in _class_list(child) if c.startswith("sy-")), None
                )
                rule = rules["sy"].get(y_cls) if y_cls else None
                if rule:
                    buf_parts.append(_apply_rule(child, rule))
                if child.tail:
                    buf_parts.append(child.tail)
                continue

            # Per-tag ordered pieces for this paragraph class
            if p_key is not None and child_tag in rules["orders"]:
                rule = rules["p_rules"].get(p_key, {}).get(child_tag) or {}
                ordered_cache[child_tag] = _apply_rule(child, rule)

            if child.tail:
                buf_parts.append(child.tail)

        # append ordered pieces by tag order
        for tag in rules["orders"]:
            if tag in ordered_cache:
                buf_parts.append(ordered_cache[tag])

        para = "".join(buf_parts).strip()
        if para:
            paragraphs_out.append(para)

    return "\n\n".join(paragraphs_out), refl_list
