#!/usr/bin/env python3
import subprocess
from pathlib import Path


def main() -> int:
    package_dir = Path("src/novel_downloader")
    scripts_dir = Path("scripts")
    outdir = package_dir / "locales"
    outdir.mkdir(parents=True, exist_ok=True)
    outfile = outdir / "messages.pot"

    files = [str(p) for p in package_dir.rglob("*.py")]
    files.append(str(scripts_dir / "i18n_strings.py"))

    result = subprocess.run(
        [
            "xgettext",
            "--language=Python",
            "--keyword=t",
            "--output",
            str(outfile),
            *files,
        ],
        text=True,
        capture_output=True,
    )

    if result.returncode == 0:
        print(f"Updated template: {outfile}")
        return 0
    else:
        print("xgettext failed")
        print(result.stderr)
        return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
