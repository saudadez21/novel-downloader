## v2.0.0 (2025-08-30)

### Feat

- **web**: implement basic GUI interface (#65)
- **core**: async search; add 9 sites; add AES notes/helpers; archive deqixs.com (#64)

### Refactor

- **core**: optimize structure; simplify config; maintainable parsers; refresh web UI (#68)
- **ocr**: generalize FontOCR class, add lazy-loading, simplify Qidian parser (#66)
- remove TUI and browser mode; unify downloader/exporter; add support for 10+ sites (#63)

## v1.5.0 (2025-07-21)

### Feat

- **search**: add BaseSearcher, site-specific searchers, CLI subcommand (#61)

### Refactor

- **core**: migrate ChapterStorage to SQLite and optimize download/export pipelines (#59)
- **code**: cleanup resources, decorator-based module registration, and streamline exporter (#58)

### Perf

- **utils**: single-pass TextCleaner and template-based chapter rendering (#60)

## v1.4.5 (2025-07-12)

## v1.4.4 (2025-07-12)

### Fix

- **qidian**: rewrite book info parser for new page structure (#54)

### Refactor

- **project**: migrate project to src layout (#49)

## v1.4.3 (2025-06-21)

### Fix

- **qidian**: add use_truncation flag to prevent duplicate chapter content (#45)
- **fetcher**: close pages in finally block to prevent leak on failures (#41)

### Refactor

- **downloader**: separate exporter from download flow (#47)

## v1.4.2 (2025-06-14)

### Feat

- **download**: support partial chapter download with start_id and end_id (#37)

### Fix

- **debug**: restore save_html behavior for encrypted content (#39)

### Refactor

- **exporter**: replace ebooklib with custom EPUB generator (#35)

## v1.4.1 (2025-06-07)

### Fix

- **fetcher**: handle single-volume extraction for linovelib

## v1.4.0 (2025-06-07)

### Feat

- **tui**: implement basic download UI (#32)
- **site**: add support for linovelib (#28)

### Fix

- **tui**: include .tcss styles in package data for Textual UI
- **parser**: add missing Node.js check for qidian

### Refactor

- **core**: migrate to async, switch to lxml, and use argparse (#31)
- **login**: extract login from requester into downloader (#29)

## v1.3.3 (2025-05-26)

### Feat

- **epub**: add image support (#26)

### Refactor

- **esjzone**: simplify chapterList node selection in parser for volumes

## v1.3.2 (2025-05-25)

### Feat

- **site**: add support for yamibo (#24)
- **site**: add support for esjzone (#23)
- **site**: add support for sfacg (#22)
- **site**: add support for Qianbi (#21)
- **site**: implement async version for biquge support (#20)

## v1.3.1 (2025-05-23)

### Fix

- **site**: assign missing _logged_in flag for Qidian

## v1.3.0 (2025-05-23)

### Refactor

- **core**: restructure layout for better scalability and extensibility (#16)

## v1.2.2 (2025-05-16)

### Feat

- **i18n**: add bilingual manual login prompts and improve UX messaging

### Refactor

- **typing**: update type annotations and fix Pylance issues (#14)

## v1.2.1 (2025-05-13)

### Refactor

- **config**: unify time fields as float + centralize font OCR config (#11)

## v1.2.0 (2025-05-13)

### Feat

- **async**: full async download mode via aiohttp (#9)

### Fix

- **bump**: grant permissions to allow push
- **gitattributes**: mark non-code resources as linguist-vendored to improve language stats

### Refactor

- **config**: support loading and saving config as JSON (#3)

## v1.1.0 (2025-05-10)

### Feat

- **cli**: add 'init' subcommand to initialize default settings
- **fontocr**: add debug logs for predictions and fallback cases
- **saver**: defer common_epub import and raise NotImplementedError if missing
- **cli**: add optional auto-close prompt after parsing
- **fontocr**: add OCR v2 module with vector+OCR fusion and hash support
- **saver**: add support for exporting novel as EPUB file
- **qidian**: support parsing encrypted chapter content
- **ocr**: add FontOCRV1 for font-based character recognition
- **epub**: add utils for EPUB generation (init, styles, intro rendering)
- **interactive**: add download option with prompts for site and book IDs
- **cli**: add clean command to remove cache, logs, and config files
- **parser**: add QidianSessionParser to support session-based chapter parsing
- **requester**: add QidianSession
- **time_utils**: support flexible multi-format datetime parsing
- **biquge**: add parser and rules for book info, volumes, and chapters
- **factory**: add Common fallback support for requester, parser, saver, and downloader
- **requester**: add common session requester for novel sites
- **parser**: add CommonParser supporting site-specific novel extraction
- **downloader**: add CommonDownloader class for generic novel downloading
- **saver**: add unified save() method based on config
- **config**: add function to validate and save setting and site-rule file
- **downloader**: add QidianDownloader with full book/chapter workflow
- **savers**: implement QidianSaver with TXT export support
- **parser**: add mode-based parser factory supporting browser/session
- **config**: add mode field (browser/session) to control requester behavior
- **parser**: add QidianBrowserParser for browser-rendered pages
- **parser**: add BaseParser abstract class for site-specific parsers
- **interfaces**: add DownloaderProtocol to define downloader interface
- **core**: add Base Requesters and QidianRequester
- **utils**: add time_utils module to centralize time-related utilities
- **interfaces**: add core protocol definitions for parser, requester, and saver
- **text_utils**: add text_utils module to expose common text utilities
- **logger**: add configurable logger with daily rotation and console output
- **network**: add retryable HTTP client and resource download utilities
- **file_utils**: add filename sanitizer and file I/O helpers
- **cli**: add initial CLI structure (argument parsing, no core logic yet)
- **config**: add config loader and adapter
- **state**: add persistent state manager for language and login flags

### Fix

- **fontocr**: ensure debug path is created with parents=True
- **parser**: clean volume titles from HTML
- **qidian**: add missing chapter_id param in extract_paragraphs_recursively
- **io**: avoid newline in binary mode
- **qidian**: correct vip_status parsing logic
- **test**: add debug method to DummyLogger to fix pytest failure
- **main**: call setup_logging() to initialize logging system
- **io**: ensure JSON content is properly serialized in _write_file

### Refactor

- **types**: replace builtin generics with typing.* for py38
- **downloader**: improve login flow in QidianDownloader
- **fontocr**: change path for saving failed images
- **parser, utils**: clean structure, fix docstrings
- **qidian**: improve chapter parser with better error handling and optional import
- **output**: unify chapter saving format to JSON
- **cli**: migrate from argparse to click
- **logging**: use module-level name for logger naming
- **saver**: extract CommonSaver and make QidianSaver inherit it
- **log**: change default log path from ./logs to BASE_CONFIG_DIR/logs
- **config**: move save_html from ParserConfig to DownloaderConfig
- **core**: move interfaces module to correct package location
