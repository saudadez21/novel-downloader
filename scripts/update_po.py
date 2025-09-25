#!/usr/bin/env python3
import subprocess
from pathlib import Path

_LANGS = {
    "zh_CN",
}


def run_cmd(cmd: list[str]) -> bool:
    """Run a command and print output if it fails."""
    result = subprocess.run(cmd, text=True, capture_output=True)
    if result.returncode == 0:
        return True
    print(f"Command failed: {' '.join(cmd)}")
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    return False


def main() -> int:
    locales_dir = Path("src/novel_downloader/locales")
    pot_file = locales_dir / "messages.pot"

    # Ensure the template file exists
    if not pot_file.exists():
        print("No messages.pot found. Run update_pot.py first.")
        return 1

    for lang in _LANGS:
        po_file = locales_dir / lang / "LC_MESSAGES" / "messages.po"

        if po_file.exists():
            # Update existing .po file with new strings from .pot
            print(f"Updating {po_file} ...")
            ok = run_cmd(["msgmerge", "--update", str(po_file), str(pot_file)])
            if not ok:
                return 1
        else:
            print(f"{po_file} not found, creating with msginit ...")
            po_file.parent.mkdir(parents=True, exist_ok=True)
            ok = run_cmd(
                [
                    "msginit",
                    "--no-translator",
                    "-l",
                    lang,
                    "-i",
                    str(pot_file),
                    "-o",
                    str(po_file),
                ]
            )
            if not ok:
                return 1

    print("All locales updated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
