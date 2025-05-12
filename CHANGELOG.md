## v1.1.1 (2025-05-12)

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
