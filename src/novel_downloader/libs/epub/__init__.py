#!/usr/bin/env python3
"""
novel_downloader.libs.epub
--------------------------

Top-level package for EPUB export utilities.

Key components:
  * EpubBuilder : orchestrates metadata, manifest, spine, navigation, and resources
  * Chapter, Volume : represent and render content sections and volume intros

Usage example:

```python
builder = EpubBuilder(title="My Novel", author="Author Name", uid="uuid-1234")
builder.chapters.append(Chapter(id="ch1", title="Chapter 1", content="<p>xxx</p>"))
builder.export("output/my_novel.epub")
```
"""

__all__ = [
    "EpubBuilder",
    "Chapter",
    "Volume",
    "StyleSheet",
]

from .builder import EpubBuilder
from .models import (
    Chapter,
    StyleSheet,
    Volume,
)
