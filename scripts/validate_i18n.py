#!/usr/bin/env python3
"""
validate_i18n.py

Scans Python sources for `t(...)` usages and validates against locale JSON files.

Checks performed:
  1) Missing translation keys.
  2) Two-way placeholder validation:
    * Params used in the call but not present as `{name}` in the template.
    * Placeholders present in the template but not provided as params in the call.
  3) Unused translation keys (present in locale files but never referenced).

Usage:

python scripts/validate_i18n.py -s src/novel_downloader -l src/novel_downloader/locales
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from collections.abc import Iterable, Mapping
from pathlib import Path
from string import Formatter
from typing import Any


def load_translations(
    locales_dir: Path,
) -> tuple[dict[str, dict[str, str]], dict[str, Path]]:
    """
    Load all JSON translation files from the given directory.

    :param locales_dir: Directory with locale JSON files (e.g., en.json, zh.json).
    :return: (translations, files)
             translations: lang -> { key -> template }
             files: lang -> path to the locale file
    """
    translations: dict[str, dict[str, str]] = {}
    files: dict[str, Path] = {}

    for locale_path in locales_dir.glob("*.json"):
        lang = locale_path.stem
        try:
            with locale_path.open(encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                # ensure all leaf values are strings
                translations[lang] = {str(k): str(v) for k, v in data.items()}
                files[lang] = locale_path
            else:
                print(
                    f"Warning: {locale_path} is not a JSON object; skipped.",
                    file=sys.stderr,
                )
        except Exception as e:
            print(f"Warning: failed to load {locale_path}: {e}", file=sys.stderr)

    return translations, files


def find_i18n_usages(source_path: Path) -> list[tuple[str, set[str]]]:
    """
    Parse a Python file with AST and collect all calls to t("key", ...).

    Returns a list of (key, params_used), where params_used is the set of
    keyword-argument names provided in the call (values can be dynamic).
    """
    text = source_path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text, filename=str(source_path))
    except SyntaxError as e:
        print(f"Warning: failed to parse {source_path}: {e}", file=sys.stderr)
        return []

    usages: list[tuple[str, set[str]]] = []

    class Visitor(ast.NodeVisitor):
        def visit_Call(self, node: ast.Call) -> Any:
            # Match t("key", ...)
            func = node.func
            if (
                isinstance(func, ast.Name)
                and func.id == "t"
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
            ):
                key = node.args[0].value
                params_used: set[str] = set()
                for kw in node.keywords:
                    # We only care about the param name, not its value.
                    if kw.arg is not None:
                        params_used.add(kw.arg)
                usages.append((key, params_used))
            self.generic_visit(node)

    Visitor().visit(tree)
    return usages


def extract_placeholders(template: str) -> set[str]:
    """
    Extract `{name}`-style placeholders using the standard Formatter parser.
    Properly ignores escaped braces `{{` and `}}`.

    :param template: The translation template string.
    :return: A set of placeholder names found in the template.
    """
    names: set[str] = set()
    for _, field_name, _, _ in Formatter().parse(template):
        if field_name:  # None for plain text segments
            # handle attribute/index access like {user.name} or {items[0]}
            base = str(field_name).split(".", 1)[0].split("[", 1)[0]
            if base:
                names.add(base)
    return names


def validate_usage(
    lang: str,
    key: str,
    params_used: set[str],
    translations: Mapping[str, str],
    source_path: Path,
) -> bool:
    """
    Validate a single (key, params) usage against a given language.

      * Report missing key.
      * Compare call params vs. template placeholders and report both sides:
        * [MISSING PLACEHOLDER] when call uses a param not present in template.
        * [MISSING PARAM] when template expects a placeholder not supplied by the call.

    :return: True if valid, False otherwise.
    """
    ok = True
    if key not in translations:
        print(f"[MISSING KEY] {source_path} ({lang}): key '{key}' not found")
        return False

    template = translations[key]
    placeholders = extract_placeholders(template)

    # params used in source but not present in template
    missing_in_template = sorted(params_used - placeholders)
    for name in missing_in_template:
        print(
            f"[MISSING PLACEHOLDER] {source_path} ({lang}): "
            f"key '{key}' missing placeholder '{{{name}}}' (param provided in call)"
        )
        ok = False

    # placeholders present in template but not provided in the call
    missing_in_call = sorted(placeholders - params_used)
    for name in missing_in_call:
        print(
            f"[MISSING PARAM] {source_path} ({lang}): "
            f"key '{key}' expects '{{{name}}}' but call did not supply it"
        )
        ok = False

    return ok


def process_file(
    source_path: Path,
    all_translations: Mapping[str, Mapping[str, str]],
    used_keys_out: set[str],
) -> bool:
    """
    Process a single Python source file:
      * Find all t(...) usages via AST.
      * Validate each usage against every loaded locale.
      * Record used keys into `used_keys_out`.

    :return: True if all usages in this file are valid in all locales, False otherwise.
    """
    usages = find_i18n_usages(source_path)
    for key, _ in usages:
        used_keys_out.add(key)

    file_ok = True
    for lang, translations in all_translations.items():
        for key, params_used in usages:
            if not validate_usage(lang, key, params_used, translations, source_path):
                file_ok = False
    return file_ok


def report_unused_keys(
    translations: Mapping[str, Mapping[str, str]],
    locale_files: Mapping[str, Path],
    used_keys: Iterable[str],
) -> bool:
    """
    Print translation keys that are present in locales but never referenced in source.

    :return: True if no unused keys are found; False otherwise.
    """
    ok = True
    used = set(used_keys)
    for lang, mapping in translations.items():
        unused = sorted(set(mapping.keys()) - used)
        if unused:
            ok = False
            locpath = locale_files.get(lang, Path(f"{lang}.json"))
            for k in unused:
                print(f"[UNUSED KEY] {locpath} ({lang}): key '{k}' is not referenced")
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate i18n translation keys, placeholders, and report unused."
    )
    parser.add_argument(
        "--src",
        "-s",
        type=Path,
        default=Path("."),
        help="Root of the Python source tree to scan.",
    )
    parser.add_argument(
        "--locales",
        "-l",
        dest="locales_dir",
        type=Path,
        default=Path("locales"),
        help="Directory containing locale JSON files.",
    )
    args = parser.parse_args()

    if not args.src.is_dir():
        print(f"Error: --src '{args.src}' is not a directory.", file=sys.stderr)
        return 1
    if not args.locales_dir.is_dir():
        print(
            f"Error: --locales '{args.locales_dir}' is not a directory.",
            file=sys.stderr,
        )
        return 1

    translations, locale_files = load_translations(args.locales_dir)
    if not translations:
        print(
            f"Error: no translation files found in {args.locales_dir}", file=sys.stderr
        )
        return 1

    all_ok = True
    used_keys: set[str] = set()

    # Scan all Python files
    for py_file in args.src.rglob("*.py"):
        if not process_file(py_file, translations, used_keys):
            all_ok = False

    # Report unused keys per locale
    if not report_unused_keys(translations, locale_files, used_keys):
        all_ok = False

    if all_ok:
        print("All i18n checks passed.")
        return 0
    else:
        print("i18n checks failed. See messages above.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
