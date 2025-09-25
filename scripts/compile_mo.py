#!/usr/bin/env python3
import subprocess
from pathlib import Path


def main() -> int:
    locales_dir = Path("src/novel_downloader/locales")
    po_files = list(locales_dir.rglob("LC_MESSAGES/*.po"))
    if not po_files:
        print("No .po files found.")
        return 0

    for po_file in po_files:
        mo_file = po_file.with_suffix(".mo")
        result = subprocess.run(
            ["msgfmt", str(po_file), "-o", str(mo_file)],
            text=True,
            capture_output=True,
        )
        if result.returncode == 0:
            print(f"Compiled {po_file} -> {mo_file}")
        else:
            print(f"msgfmt failed for {po_file}")
            print(result.stderr)
            return result.returncode

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
