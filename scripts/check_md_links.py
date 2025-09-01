#!/usr/bin/env python3

import argparse
import re
from pathlib import Path

# Match Markdown links and images with local paths.
# Pattern breakdown:
# - !?               : optional '!' for image links
# - \[[^\]]+\]       : match [alt] or [text]
# - \(               : opening parenthesis
#   (?!http|mailto|#): skip absolute URLs and anchors
#   ([^)#][^)]*?)    : capture relative path (excluding pure anchors)
# - \)               : closing parenthesis
LINK_PATTERN = re.compile(r"!?\[[^\]]+\]\((?!http|https|mailto|#)([^)#][^)]*?)\)")


def find_invalid_links(base_dir: Path):
    """
    Scan all .md files under base_dir for local Markdown and image links,
    and check if their targets exist.

    Skips any text inside ``` ... ``` code fences.

    :param base_dir: Root directory to search recursively.

    :return: List of errors. Each error is a dict with:

      * 'file': Path to the .md file
      * 'line': Line number
      * 'raw_link': Original link text (may include anchor/query)
      * 'target': Resolved path that was not found
    """
    errors = []

    for md_file in base_dir.rglob("*.md"):
        rel_base = md_file.parent
        in_code_block = False

        try:
            with md_file.open(encoding="utf-8") as f:
                for lineno, line in enumerate(f, start=1):
                    if line.lstrip().startswith("```"):
                        in_code_block = not in_code_block
                        continue

                    if in_code_block:
                        continue

                    for match in LINK_PATTERN.finditer(line):
                        raw_path = match.group(1).strip()

                        # Remove any fragment (after '#') or query (after '?')
                        link_no_anchor = re.split(r"[#?]", raw_path, maxsplit=1)[0]

                        # Determine the target path:
                        # - starts with '/' -> relative to the project root
                        # - Otherwise -> relative to the directory of the .md file
                        if link_no_anchor.startswith("/"):
                            candidate = base_dir / link_no_anchor.lstrip("/")
                        else:
                            candidate = rel_base / link_no_anchor

                        try:
                            link_target = candidate.resolve()
                        except Exception:
                            # If resolution fails (e.g., broken symlink) -> non-existent
                            link_target = candidate

                        if not link_target.exists():
                            errors.append(
                                {
                                    "file": md_file,
                                    "line": lineno,
                                    "raw_link": raw_path,
                                    "target": link_target,
                                }
                            )
        except Exception as e:
            print(f"Warning: Could not read file {md_file}. Skipping. (Error: {e})")

    return errors


def main():
    parser = argparse.ArgumentParser(
        description="Check local Markdown links and image links for existence."
    )
    parser.add_argument(
        "-d",
        "--dir",
        type=Path,
        default=Path("."),
        help="Root directory to scan (default: current directory)",
    )
    args = parser.parse_args()

    base_dir = args.dir.resolve()
    print(f"Scanning Markdown files under: {base_dir}\n")

    broken_links = find_invalid_links(base_dir)

    if not broken_links:
        print("All local Markdown links and image links are valid.")
    else:
        print(f"Found {len(broken_links)} broken link(s):\n")
        for err in broken_links:
            rel_file = err["file"].relative_to(base_dir)
            line = err["line"]
            raw = err["raw_link"]
            target = err["target"]
            print(
                f"- File: {rel_file}, Line: {line},\n"
                f"  Link: '{raw}' -> Path: '{target}' (not found)"
            )
        print("\nPlease fix or remove the invalid references above.")


if __name__ == "__main__":
    main()
