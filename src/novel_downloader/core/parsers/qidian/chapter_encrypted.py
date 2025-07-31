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
from typing import TYPE_CHECKING, Any

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

if TYPE_CHECKING:
    from .main_parser import QidianParser

logger = logging.getLogger(__name__)
IGNORED_CLASS_LISTS = {"title", "review"}


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
        if not (parser._decode_font and parser._font_ocr):
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
        main_paragraphs = extract_paragraphs_recursively(raw_html)

        if parser.save_font_debug:
            main_paragraphs_path = debug_dir / "main_paragraphs_debug.json"
            main_paragraphs_path.write_text(
                json.dumps(main_paragraphs, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        paragraphs_rules = parse_rule(css_str)
        if parser.save_font_debug:
            paragraphs_rules_path = debug_dir / "paragraphs_rules_debug.json"
            paragraphs_rules_path.write_text(
                json.dumps(paragraphs_rules, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        paragraphs_str, refl_list = render_paragraphs(
            main_paragraphs,
            paragraphs_rules,
        )
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

        mapping_result = parser._font_ocr.generate_font_map(
            fixed_font_path=fixed_path,
            random_font_path=rand_path,
            char_set=char_set,
            refl_set=refl_set,
            chapter_id=chapter_id,
        )
        if parser.save_font_debug:
            mapping_json_path = debug_dir / "font_mapping.json"
            mapping_json_path.write_text(
                json.dumps(mapping_result, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        # Reconstruct final readable text
        original_text = parser._font_ocr.apply_font_mapping(
            text=paragraphs_str,
            font_map=mapping_result,
        )

        final_paragraphs_str = "\n\n".join(
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


def extract_paragraphs_recursively(html_str: str) -> list[dict[str, Any]]:
    def parse_element(elem: html.HtmlElement) -> dict[str, Any]:
        class_attr = elem.attrib.get("class", "")
        class_list = class_attr.split() if isinstance(class_attr, str) else class_attr
        if "review" in class_list:
            return {}

        # Build attrs with class as list
        attrs = {k: v.split() if k == "class" else v for k, v in elem.attrib.items()}

        node: dict[str, Any] = {
            "tag": elem.tag,
            "attrs": attrs,
            "data": [],
        }

        # Append entire elem.text if present (no splitting)
        if elem.text:
            node["data"].append(elem.text)

        # Recurse into children
        for child in elem.iterchildren(tag=None):
            child_dict = parse_element(child)
            if child_dict:
                node["data"].append(child_dict)

            # Append entire tail string (no split)
            if child.tail:
                node["data"].append(child.tail)

        return node

    tree = html.fromstring(html_str)
    return [parse_element(p) for p in tree.findall(".//p")]


def parse_rule(css_str: str) -> dict[str, Any]:
    """
    Parse a CSS string and extract style rules for rendering.

    Handles:
    - font-size:0 (mark for deletion)
    - scaleX(-1) (mark as mirrored)
    - ::before / ::after with content or attr()
    - class + tag selector mapping
    - custom rendering order via 'order'

    :param css_str: Raw CSS stylesheet string.
    :return: Dict with "rules" and "orders" for rendering.
    """

    rules: dict[str, Any] = {}
    orders = []

    stylesheet = tinycss2.parse_stylesheet(
        css_str, skip_comments=True, skip_whitespace=True
    )

    for rule in stylesheet:
        if rule.type != "qualified-rule":
            continue

        selector = tinycss2.serialize(rule.prelude).strip()
        declarations = tinycss2.parse_declaration_list(rule.content)

        parsed = {}
        order_val = None

        for decl in declarations:
            if decl.type != "declaration":
                continue
            name = decl.lower_name
            value = tinycss2.serialize(decl.value).strip()

            if name == "font-size" and value == "0":
                if "::first-letter" in selector:
                    parsed["delete-first"] = True
                else:
                    parsed["delete-all"] = True
            elif name == "transform" and value.lower() == "scalex(-1)":
                parsed["transform-x_-1"] = True
            elif name == "order":
                order_val = value
            elif name == "content":
                if "::after" in selector:
                    if "attr(" in value:
                        parsed["append-end-attr"] = value.split("attr(")[1].split(")")[
                            0
                        ]
                    else:
                        parsed["append-end-char"] = value.strip("\"'")
                elif "::before" in selector:
                    if "attr(" in value:
                        parsed["append-start-attr"] = value.split("attr(")[1].split(
                            ")"
                        )[0]
                    else:
                        parsed["append-start-char"] = value.strip("\"'")

        # Store in structure
        if selector.startswith(".sy-"):
            rules.setdefault("sy", {})[selector[1:]] = parsed
        elif selector.startswith(".p") and " " in selector:
            class_str, tag_part = selector.split(" ", 1)
            class_str = class_str.lstrip(".")
            tag_part = tag_part.split("::")[0]
            rules.setdefault(class_str, {}).setdefault(tag_part, {}).update(parsed)

        if order_val:
            orders.append((selector, order_val))

    orders.sort(key=lambda x: int(x[1]))
    return {"rules": rules, "orders": orders}


def render_paragraphs(
    main_paragraphs: list[dict[str, Any]],
    rules: dict[str, Any],
) -> tuple[str, list[str]]:
    """
    Applies the parsed CSS rules to the paragraph structure and
    reconstructs the visible text.

    Handles special class styles like .sy-*, text order control,
    mirrored characters, etc.

    :param main_paragraphs: A list of paragraph dictionaries, each with 'attrs'
                            and 'data' fields representing structured content.
    :param rules: A dictionary with keys 'orders' and 'rules', parsed from CSS.
                  - rules['orders']: List of (selector, id) tuples.
                  - rules['rules']: Nested dict containing transformation rules.

    :return:
        - A reconstructed paragraph string with line breaks.
        - A list of mirrored (reflected) characters for later OCR processing.
    """
    orders: list[tuple[str, str]] = rules.get("orders", [])
    rules = rules.get("rules", {})
    refl_list: list[str] = []

    def apply_rule(data: dict[str, Any], rule: dict[str, Any]) -> str:
        if rule.get("delete-all", False):
            return ""

        curr_str = ""
        if isinstance(data.get("data"), list) and data["data"]:
            first_data = data["data"][0]
            if isinstance(first_data, str):
                curr_str += first_data

        if rule.get("delete-first", False):
            curr_str = "" if len(curr_str) <= 1 else curr_str[1:]

        curr_str += rule.get("append-end-char", "")

        attr_name = rule.get("append-end-attr", "")
        if attr_name:
            curr_str += data.get("attrs", {}).get(attr_name, "")

        curr_str = rule.get("append-start-char", "") + curr_str

        attr_name = rule.get("append-start-attr", "")
        if attr_name:
            curr_str = data.get("attrs", {}).get(attr_name, "") + curr_str

        if rule.get("transform-x_-1", False):
            refl_list.append(curr_str)
        return curr_str

    paragraphs_str = ""
    for paragraph in main_paragraphs:
        class_list = paragraph.get("attrs", {}).get("class", [])
        p_class_str = next((c for c in class_list if c.startswith("p")), None)
        curr_datas = paragraph.get("data", [])

        ordered_cache = {}
        for data in curr_datas:
            # 文本节点直接加
            if isinstance(data, str):
                paragraphs_str += data
                continue

            if isinstance(data, dict):
                tag = data.get("tag", "")
                attrs = data.get("attrs", {})

                # 跳过 span.review
                if tag == "span" and "class" in attrs and "review" in attrs["class"]:
                    continue

                # sy 类型标签处理
                if tag == "y":
                    tag_class_list = attrs.get("class", [])
                    tag_class = next(
                        (c for c in tag_class_list if c.startswith("sy-")), None
                    )

                    if tag_class in rules.get("sy", {}):
                        curr_rule = rules["sy"][tag_class]
                        paragraphs_str += apply_rule(data, curr_rule)
                    continue

                if not p_class_str:
                    if any(cls in IGNORED_CLASS_LISTS for cls in class_list):
                        continue
                    logger.debug(f"[parser] not find p_class_str: {class_list}")
                    continue
                # 普通标签处理，根据 orders 顺序匹配
                for ord_selector, _ in orders:
                    if data.get("tag") != ord_selector:
                        continue
                    curr_rule = rules.get(p_class_str, {}).get(ord_selector)
                    curr_rule = curr_rule if curr_rule else {}
                    ordered_cache[ord_selector] = apply_rule(data, curr_rule)
                    break
        # 最后按 orders 顺序拼接
        for ord_selector, _ in orders:
            if ord_selector in ordered_cache:
                paragraphs_str += ordered_cache[ord_selector]

        paragraphs_str += "\n\n"

    return paragraphs_str, refl_list
