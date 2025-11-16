#!/usr/bin/env python3
"""
novel_downloader.plugins.utils.yuewen.qdcss
-------------------------------------------
"""

from __future__ import annotations

__all__ = ["apply_css_text_rules"]

from contextlib import suppress
from typing import TypedDict

from lxml import html


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


def apply_css_text_rules(html_str: str, css_str: str) -> tuple[str, list[str]]:
    """
    Render visible text from Yuewen/QD HTML + CSS.

    :param html_str: Raw HTML of the chapter/content.
    :param css_str:  Raw CSS string extracted from the page.

    :return: Visible text, with paragraphs joined by newlines.
    """
    rules = _parse_css_rules(css_str)
    return _render_with_rules(html_str, rules)


def _render_with_rules(html_str: str, rules: Rules) -> tuple[str, list[str]]:
    """Renderer the HTML using pre-parsed Rules."""
    tree = html.fromstring(html_str)
    paragraphs_out: list[str] = []
    refl_set: set[str] = set()
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
            refl_set.add(s)

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

    return "\n".join(paragraphs_out), sorted(refl_set)


def _parse_css_rules(css_str: str) -> Rules:
    """
    Produces normalized Rules with:
      * orders: list[str] of tag names sorted by numeric 'order'
      * sy: '.sy-*' class rules
      * p_rules: '.p* <tag>' rules, indexed by p-class then tag
    """
    rules: Rules = {"orders": [], "sy": {}, "p_rules": {}}
    order_pairs: list[tuple[str, int]] = []

    pos = 0
    while True:
        b1 = css_str.find("{", pos)
        if b1 == -1:
            break
        selector = css_str[pos:b1].strip().lower()
        b2 = css_str.find("}", b1 + 1)
        if b2 == -1:
            break
        block = css_str[b1 + 1 : b2]
        pos = b2 + 1

        decls = _parse_decls(block)
        new_rule: Rule = {}
        order_val: int | None = None

        for name, value in decls:
            v = value.strip()
            if name == "font-size" and v == "0":
                new_rule[
                    "delete_first" if "::first-letter" in selector else "delete_all"
                ] = True
            elif name == "transform" and "scalex(-1" in v.replace(" ", "").lower():
                new_rule["transform_flip_x"] = True
            elif name == "order":
                with suppress(ValueError):
                    order_val = int(v)
            elif name == "content":
                if "::after" in selector:
                    if v.lower().startswith("attr("):
                        new_rule["append_end_attr"] = v[5:-1].strip()
                    else:
                        new_rule["append_end_char"] = v.strip().strip("\"'")
                elif "::before" in selector:
                    if v.lower().startswith("attr("):
                        new_rule["append_start_attr"] = v[5:-1].strip()
                    else:
                        new_rule["append_start_char"] = v.strip().strip("\"'")

        if selector.startswith(".sy-"):
            key = selector.lstrip(".")
            rules["sy"][key] = {**rules["sy"].get(key, {}), **new_rule}
        elif selector.startswith(".p") and " " in selector:
            p_cls, right = selector.split(" ", 1)
            tag = _only_tag(right)
            if tag:
                p_cls = p_cls.lstrip(".")
                rules["p_rules"].setdefault(p_cls, {})
                rules["p_rules"][p_cls][tag] = {
                    **rules["p_rules"][p_cls].get(tag, {}),
                    **new_rule,
                }

        if order_val is not None:
            tag = _only_tag(selector)
            if tag:
                order_pairs.append((tag, order_val))

    rules["orders"] = [t for t, _ in sorted(order_pairs, key=lambda x: x[1])]
    return rules


def _only_tag(selector: str) -> str | None:
    """
    Normalize a selector into just its tag name for ordering.

    Handles forms like 'i', 'em::before', '.p3 i', '.p2 span::after'.

    Returns None if can't extract a tag.
    """
    # If it has spaces, take the rightmost simple selector
    last = selector.strip().split()[-1]
    # Drop ::pseudo
    last = last.split("::", 1)[0]
    # If it's like 'span[attr=..]' keep 'span'
    last = last.split("[", 1)[0]
    # If it starts with '.', it's not a tag
    if not last or last.startswith("."):
        return None
    return last


def _parse_decls(block: str) -> list[tuple[str, str]]:
    """Parse 'name:value;...' inside a block. Tolerates quotes and attr()."""
    parts = [d.strip() for d in block.split(";") if d.strip()]
    decls = []
    for p in parts:
        if ":" in p:
            name, val = p.split(":", 1)
            decls.append((name.strip().lower(), val.strip()))
    return decls
