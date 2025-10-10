import json
import re
from pathlib import Path
from typing import Any


def load_html_parts(html_dir: Path, filename_prefix: str) -> list[str]:
    """Load HTML parts like {prefix}_1.html, {prefix}_2.html, ..."""
    pattern = f"{filename_prefix}_*.html"
    candidates = list(html_dir.glob(pattern))
    regex = re.compile(rf"^{re.escape(filename_prefix)}_(\d+)\.html$")
    indexed = []
    for path in candidates:
        m = regex.match(path.name)
        if m:
            indexed.append((int(m.group(1)), path))
    if not indexed:
        return []
    indexed.sort()
    return [p.read_text(encoding="utf-8") for _, p in indexed]


def load_json(path: Path) -> Any:
    with open(path, encoding="utf-8") as f:
        return json.load(f)
