#!/usr/bin/env python3
"""
validate_i18n.py

A script to scan Python source files for `t(...)` i18n usages and verify that:
  1. The translation key exists in the locale JSON files.
  2. All named parameters used in the call appear as `{param}` placeholders.

Usage:

python scripts/validate_i18n.py -s src/novel_downloader -l src/novel_downloader/locales
"""

import argparse
import ast
import json
import sys
from pathlib import Path
from typing import Any


def load_translations(locales_dir: Path) -> dict[str, dict[str, str]]:
    """
    Load all JSON translation files from the given directory.

    :param locales_dir: Path to the directory containing locale JSON files.
    :return: A dict mapping language code to its translations dict.
    """
    translations: dict[str, dict[str, str]] = {}
    for locale_path in locales_dir.glob("*.json"):
        lang = locale_path.stem
        try:
            with locale_path.open(encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    translations[lang] = data  # type: ignore
        except Exception as e:
            print(f"Warning: Failed to load {locale_path}: {e}", file=sys.stderr)
    return translations


def find_i18n_usages(source_path: Path) -> list[tuple[str, dict[str, str]]]:
    """
    Parse the file with AST, find all calls to t("key", foo="bar", ...)
    and return a list of (key, {foo: "bar", ...}).
    """
    text = source_path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(source_path))
    usages: list[tuple[str, dict[str, str]]] = []

    class Visitor(ast.NodeVisitor):
        def visit_Call(self, node: ast.Call) -> Any:
            if (
                isinstance(node.func, ast.Name)
                and node.func.id == "t"
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
            ):
                key = node.args[0].value
                params: dict[str, str] = {}
                for kw in node.keywords:
                    if (
                        kw.arg is not None
                        and isinstance(kw.value, ast.Constant)
                        and isinstance(kw.value.value, str)
                    ):
                        params[kw.arg] = kw.value.value
                usages.append((key, params))

            self.generic_visit(node)

    Visitor().visit(tree)
    return usages


def validate_usage(
    lang: str,
    key: str,
    params: dict[str, str],
    translations: dict[str, str],
    source_path: Path,
) -> bool:
    """
    Verify that the key exists and that all params appear as placeholders.

    :param lang: The locale code being validated (e.g. "en", "zh").
    :param key: The translation key.
    :param params: Dict of named parameters used in the call.
    :param translations: The dict of translations for this language.
    :param source_path: The file where this usage was found (for error reporting).
    :return: True if valid, False otherwise.
    """
    ok = True
    if key not in translations:
        print(f"[MISSING KEY] {source_path} ({lang}): key '{key}' not found")
        ok = False
    else:
        template = translations[key]
        for name in params:
            placeholder = "{" + name + "}"
            if placeholder not in template:
                print(
                    f"[MISSING PLACEHOLDER] {source_path} ({lang}): "
                    f"key '{key}' missing placeholder {placeholder}"
                )
                ok = False
    return ok


def process_file(
    source_path: Path,
    all_translations: dict[str, dict[str, str]],
) -> bool:
    """
    Process a single Python source file:
      - Skip if it does not import the t() function.
      - Find all t(...) usages via AST.
      - Validate each usage against every loaded locale.

    :param source_path: Path to the .py file.
    :param all_translations: Mapping of lang -> translations dict.
    :return: True if all usages are valid in all locales, False otherwise.
    """
    content = source_path.read_text(encoding="utf-8")
    # Quick check: skip files that don't import t
    if "import t" not in content:
        return True

    usages = find_i18n_usages(source_path)
    file_ok = True
    for lang, translations in all_translations.items():
        for key, params in usages:
            if not validate_usage(lang, key, params, translations, source_path):
                file_ok = False
    return file_ok


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate i18n translation keys and placeholders."
    )
    parser.add_argument(
        "--src",
        "-s",
        type=Path,
        default=Path("."),
        help="Path to the root of the Python source tree to scan.",
    )
    parser.add_argument(
        "--locales",
        "-l",
        dest="locales_dir",
        type=Path,
        default=Path("locales"),
        help="Path to the directory containing locale JSON files.",
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

    translations = load_translations(args.locales_dir)
    if not translations:
        print(
            f"Error: No translation files found in {args.locales_dir}", file=sys.stderr
        )
        return 1

    all_ok = True
    for py_file in args.src.rglob("*.py"):
        if not process_file(py_file, translations):
            all_ok = False

    if all_ok:
        print("All i18n checks passed.")
        return 0
    else:
        print("i18n checks failed. See messages above.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
