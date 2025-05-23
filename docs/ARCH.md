# Architecture Overview

This document provides an overview of the internal architecture of `novel-downloader`.

---

## Modes

The system supports three pluggable modes for web content fetching:

| Mode      | Description                                                                 |
|-----------|-----------------------------------------------------------------------------|
| `browser` | Uses headless browsers (e.g., DrissionPage) for JavaScript-rendered content |
| `session` | Uses `requests.Session` for standard HTTP crawling                          |
| `async`   | Uses `aiohttp` + `asyncio` for high-performance concurrent downloading      |

All modes share the same pipeline logic (fetch -> parse -> save), with only the underlying fetcher differing.

---

## Standard Flow (`browser` / `session` Mode)

In both `browser` and `session` modes, the crawling process is executed **sequentially**, step by step:

### Phase 1: Book Metadata

1. Fetch book info page (e.g., title, author, tags, volumes, chapters list)
2. Parse HTML to extract structured book metadata
3. Save metadata as JSON (`book.json`)

### Phase 2-3: Volume and Chapter Iteration

1. Loop through the volume list from `book.json`
2. For each volume:
  - Loop through its chapters
    - Fetch the raw HTML of the chapter
    - Parse content (text, title, assets)
    - Save each chapter as individual JSON files (`{chapter_id}.json`)

### Phase 4: Merge Output

1. Use the parsed metadata and chapters
2. Reconstruct the full book
3. Export to desired formats (e.g., `.txt`, `.epub`, `.md`, `.json`)

```

[Book Info] -> [Volumes] -> [Chapters] -> [Parsed JSON/DB]
  ↓
[Merged Output]
(.txt / .epub / ...)

```

---

## Async Mode Architecture

The `async` mode is designed for **maximum performance** when downloading and parsing large amounts of chapter content. It uses a producer-consumer pattern with queues.

```
[URLs]
  ↓
[Downloader] (asyncio + aiohttp)
  ↓ (HTML content)
[Async Queue]
  ↓
[Parser Workers] (Thread/Process Pool + BeautifulSoup)
  ↓
[Output: JSON files / DB entries]
```

Compared to `session`, this model:
- Fetches hundreds of chapters concurrently
- Separates network I/O and parsing via queues
- Fully utilizes both CPU and bandwidth

---

### Future Improvements (Async Mode)

- Proxy pool integration
- Rate limiter / auto backoff support
- Better retry/failure logging
- Optional disk-based buffering (for large queues)
