# API 描述文档

---

## 1. 概览与分层

* **apps/**
  * **cli/**：命令行界面（`argparse` + `rich` 封装的 `ui`）
  * **web/**：NiceGUI Web 前端（页面、组件、下载任务调度与登录对话）
  * **constants.py**：站点显示名映射（`dict[str, str]`，如 `aaatxt -> "3A电子书"`）
* **infra/**：基础设施（配置加载与适配、网络下载、路径、日志、i18n、OCR/JSBridge、持久化）
* **libs/**：通用库（EPUB 构建、文件系统工具、加解密、文本清洗、URL 解析、时间工具）
* **plugins/**：站点插件（`fetcher / parser / downloader / exporter / searcher`；注册器与公共实现）
* **schemas/**：配置与数据的类型定义（`TypedDict` / `dataclass`）
* **locales/**：多语言资源

---

## 2. 快速开始

### 2.1 按书籍 ID/URL 下载并导出 (与 CLI 同流程)

```python
from pathlib import Path
from novel_downloader.infra.config import ConfigAdapter, load_config
from novel_downloader.apps.cli.handlers.download import download_book
from novel_downloader.apps.cli.handlers.export import export_book
from novel_downloader.libs.book_url_resolver import resolve_book_url

config = load_config(Path("./settings.toml"))
resolved = resolve_book_url("https://example.com/book/123")  # -> {"site_key": "...", "book": {"book_id": "..."}}

site = resolved["site_key"]
adapter = ConfigAdapter(config=config, site=site)

# 下载
import asyncio
ok = asyncio.run(
    download_book(
        site,
        resolved["book"],
        adapter.get_downloader_config(),
        adapter.get_fetcher_config(),
        adapter.get_parser_config(),
        adapter.get_login_config(),
    )
)
if ok:
    export_book(site, resolved["book"], adapter.get_exporter_config())
```

### 2.2 直接通过插件注册器使用

```python
from novel_downloader.plugins import registrar  # 插件注册器单例
from novel_downloader.schemas.config import FetcherConfig, ParserConfig, DownloaderConfig

parser = registrar.get_parser("aaatxt", ParserConfig())
async def run():
    async with registrar.get_fetcher("aaatxt", FetcherConfig()) as fetcher:
        downloader = registrar.get_downloader(fetcher, parser, "aaatxt", DownloaderConfig())
        await downloader.download({"book_id": "123"})
```

---

## 3. CLI API（`apps/cli/commands`）

> 基类：

```python
class Command(ABC):
    name: str
    help: str

    @classmethod
    def register(cls, subparsers) -> None: ...

    @classmethod
    def add_arguments(cls, parser) -> None: ...

    @classmethod
    @abstractmethod
    def run(cls, args) -> None: ...
```

### 3.1 `clean`

清理日志、缓存、数据、配置。

* 选项：
  * `--logs` 清理日志目录
  * `--cache` 清理脚本与 Cookie 缓存（如 Node 脚本目录）
  * `--data` 清理数据文件
  * `--config` 清理配置文件
  * `--all` 全部清理（支持 `-y/--yes` 跳过确认）

### 3.2 `config`

配置管理（含子命令）：

* `init [--force]`：在当前目录生成默认 `settings.toml`
* `set-lang <lang>`：设置界面语言（如 `zh` / `zh_CN`）
* `set-config <path>`：保存自定义的 TOML 配置

### 3.3 `download`

按书籍 **ID 或 URL** 下载（可选导出）。

* 位置参数：`book_ids...`（与 `--site` 搭配为 ID 模式；不带 `--site` 时必须是单个 URL）
* 选项：
  * `--site <key>` 指定站点（省略且传 URL 时自动识别）
  * `--config <path>` 指定配置文件
  * `--start/--end <chapter_id>` 仅作用于第一本
  * `--no-export` 跳过导出
* 流程：加载配置 -> 解析 URL 或读取 ID -> 组装配置（`ConfigAdapter`）-> 下载（必要时登录）-> 可选导出

### 3.4 `export`

对**已下载**内容进行导出。

* 位置参数：`book_ids...`（若未指定 `--site`，进入交互式站点/书籍选择）
* 选项：
  * `--format txt|epub ...`（默认按配置）
  * `--site <key>` 指定站点
  * `--config <path>` 配置路径
  * `--start/--end <chapter_id>` 仅作用于第一本

### 3.5 `search`

跨站点搜索并**可选自动下载+导出**（交互选择结果）。

* 位置参数：`keyword`
* 选项：
  * `-s/--site <key>` 可多次指定以限制站点
  * `-l/--limit N` 总结果上限
  * `--site-limit M` 每站点返回上限（默认 10）
  * `--timeout SECS` 单站点请求超时（默认 5.0）

---

## 4. Web 端（`apps/web`）简要约定

* **pages/**：搜索、下载、进度、历史页面（NiceGUI）
* **services/**
  * `task_manager.py`：接收页面发起的下载任务（需要时触发登录）
  * `client_dialog.py`：注册登录输入弹窗；配合 `fetcher.login_fields` 动态渲染
  * `cred_broker.py / cred_models.py`：登录凭据管理与数据模型
* **components/**：UI 组件（如导航）
* **main.py**：应用入口

> 交互流程：`page -> task_manager -> (need login?) -> client_dialog.prompt(...) -> download_book(...) -> exporter`

---

## 5. 配置 API（`infra/config`）

### 5.1 `load_config(config_path: str|Path|None) -> dict[str, Any]`

从 TOML 读取并返回通用字典配置（找不到或解析失败抛异常）。

### 5.2 `ConfigAdapter`

将通用配置映射为结构化数据类，按字段优先级解析：

1. `config["sites"][<site>]`
2. `config["general"]`
3. 调用方提供的默认值

可用方法：

```python
get_fetcher_config() -> FetcherConfig
get_downloader_config() -> DownloaderConfig
get_parser_config() -> ParserConfig
get_exporter_config() -> ExporterConfig
get_login_config() -> dict[str, str]
```

---

## 6. 插件系统（`plugins`）

### 6.1 协议（`plugins/protocols/*.py`）

* `FetcherProtocol`
  * 关键方法：`init() / close()`、`login()`、`get_book_info()`、`get_book_chapter()`、`load_state()/save_state()`
  * 属性：`is_logged_in: bool`、`login_fields: list[LoginField]`
* `ParserProtocol`
  * `parse_book_info(html_list) -> BookInfoDict | None`
  * `parse_chapter(html_list, chapter_id) -> ChapterDict | None`
* `DownloaderProtocol`
  * `download(book, *, progress_hook=None, cancel_event=None)`（或 `download_many`）
* `ExporterProtocol`
  * `export(book) -> dict[str, Path]`
  * 可选 `export_as_txt / export_as_epub`

### 6.2 注册器（`plugins/registry.py`）

```python
from novel_downloader.plugins import registrar

# 装饰器注册 (site_key 缺省时取模块父目录名)
@registrar.register_fetcher("aaatxt")
class AAAFetcher(...): ...

@registrar.register_parser("aaatxt")
class AAAParser(...): ...
```

获取实例：

```python
registrar.get_fetcher(site, FetcherConfig) -> FetcherProtocol
registrar.get_parser(site, ParserConfig) -> ParserProtocol
registrar.get_downloader(fetcher, parser, site, DownloaderConfig) -> DownloaderProtocol  # 无站点实现时回退 CommonDownloader
registrar.get_exporter(site, ExporterConfig) -> ExporterProtocol  # 无站点实现时回退 CommonExporter
```

> 站点包命名要求：`plugins.sites.<site_key>.<kind>`；若首字符为数字，规范化为前缀 `n`（如 `3xx` -> `n3xx`）。

### 6.3 搜索注册（`plugins/searching.py`）

```python
@register_searcher("aaatxt")
class AAASearcher(...): ...
```

统一入口：

```python
async def search(keyword, sites=None, limit=None, per_site_limit=5, timeout=5.0) -> list[SearchResult]
async def search_stream(...) -> AsyncGenerator[list[SearchResult]]
```

---

## 7. 核心库 API

### 7.1 下载与导出

```python
# apps/cli/handlers/download.py
async def download_books(
    site: str,
    books: list[BookConfig],
    downloader_cfg: DownloaderConfig,
    fetcher_cfg: FetcherConfig,
    parser_cfg: ParserConfig,
    login_config: dict[str, str] | None = None,
) -> bool

# apps/cli/handlers/export.py
def export_books(
    site: str,
    books: list[BookConfig],
    exporter_cfg: ExporterConfig,
    formats: list[str] | None = None,
) -> None
```

### 7.2 EPUB 构建（`libs/epub/builder.py`）

```python
class EpubBuilder:
    def __init__(self, title, author="", description="", cover_path=None,
                 subject=None, serial_status="", word_count="0", uid="", language="zh-Hans")
    def add_image(self, image_path: Path) -> str
    def add_chapter(self, chap: models.Chapter) -> None
    def add_volume(self, volume: models.Volume) -> None
    def export(self, output_path: str|Path) -> Path
```

### 7.3 文本与时间

* 文本清理：`libs/textutils`（`Cleaner` 协议、`truncate_half_lines(text)`）
* 异步抖动睡眠：`libs/time_utils.async_jitter_sleep(base, add_spread=0.0, mul_spread=1.0, max_sleep=None)`

### 7.4 URL 解析（`libs/book_url_resolver.py`）

```python
def resolve_book_url(url: str) -> BookURLInfo | None
# -> {"site_key": str, "book": {"book_id": str, ...}}
```

### 7.5 OCR 与 JS 解密

* **FontOCR**（`infra/fontocr/core.py`）
  * `predict(images: list[np.ndarray], batch_size=1) -> list[tuple[str, float]]`
  * `render_char_image(char, render_font, is_reflect=False, size=64) -> PIL.Image`
* **NodeDecryptor**（`infra/jsbridge/decryptor.py`）
  * `decrypt_qd(ciphertext, chapter_id, fkp, fuid) -> str`（起点；Node 优先，带二进制回退）
  * `decrypt_qq(ciphertext, chapter_id, fkp, fuid) -> str`（QQ；仅 Node）

### 7.6 持久化（`infra/persistence`）

* `ChapterStorage`
  * `upsert_chapter(data: ChapterDict, source_id: int) -> None`
  * `upsert_chapters(data: list[ChapterDict], source_id: int) -> None`
  * `get_chapter(chap_id: str, source_id: int) -> ChapterDict | None`
  * `get_chapters(chap_ids: list[str], source_id: int) -> dict[str, ChapterDict | None]`
* `StateManager`
  * `get_language() -> str`
  * `set_language(lang: str) -> None`

### 7.7 其它

* `infra/cookies.parse_cookies(cookies: str | Mapping[str, str]) -> dict[str, str]`
* `infra/logger.setup_logging(...)`
* `infra/paths`：应用目录与资源定位（如 `DATA_DIR`, `JS_SCRIPT_DIR`, `DEFAULT_CONFIG_FILE`, `CSS_MAIN_PATH`）
* `infra/i18n.t`：`gettext` 封装（全局 `t()`）

---

## 8. 数据模型（`schemas/*.py`）

> 下述选摘用于理解 I/O 形状；以实际代码为准。

* **章节与书籍**

  ```python
  class ChapterDict(TypedDict):
      id: str
      title: str
      content: str
      extra: dict[str, Any]

  class ChapterInfoDict(TypedDict):
      title: str
      url: str
      chapterId: str
      accessible: NotRequired[bool]

  class VolumeInfoDict(TypedDict):
      volume_name: str
      volume_cover: NotRequired[str]
      update_time: NotRequired[str]
      word_count: NotRequired[str]
      volume_intro: NotRequired[str]
      chapters: list[ChapterInfoDict]

  class BookInfoDict(TypedDict):
      book_name: str
      author: str
      cover_url: str
      update_time: str
      summary: str
      extra: dict[str, Any]
      volumes: list[VolumeInfoDict]
      tags: NotRequired[list[str]]
      word_count: NotRequired[str]
      serial_status: NotRequired[str]
      summary_brief: NotRequired[str]
      last_checked: NotRequired[float]  # Unix timestamp
  ```

* **配置数据类**

  ```python
  @dataclass
  class FetcherConfig:
      request_interval: float = 2.0
      retry_times: int = 3
      backoff_factor: float = 2.0
      timeout: float = 30.0
      max_connections: int = 10
      max_rps: float = 1000.0
      user_agent: str | None = None
      headers: dict[str, str] | None = None
      verify_ssl: bool = True
      locale_style: str = "simplified"

  @dataclass
  class DownloaderConfig:
      request_interval: float = 2.0
      retry_times: int = 3
      backoff_factor: float = 2.0
      raw_data_dir: str = "./raw_data"
      cache_dir: str = "./novel_cache"
      workers: int = 4
      skip_existing: bool = True
      login_required: bool = False
      save_html: bool = False
      storage_batch_size: int = 1

  @dataclass
  class FontOCRConfig: ...
  @dataclass
  class ParserConfig:
      cache_dir: str = "./novel_cache"
      use_truncation: bool = True
      decode_font: bool = False
      batch_size: int = 32
      save_font_debug: bool = False
      fontocr_cfg: FontOCRConfig = field(default_factory=FontOCRConfig)

  @dataclass
  class TextCleanerConfig: ...
  @dataclass
  class ExporterConfig:
      cache_dir: str = "./novel_cache"
      raw_data_dir: str = "./raw_data"
      output_dir: str = "./downloads"
      check_missing: bool = True
      clean_text: bool = True
      make_txt: bool = True
      make_epub: bool = False
      make_md: bool = False
      make_pdf: bool = False
      append_timestamp: bool = True
      filename_template: str = "{title}_{author}"
      include_cover: bool = True
      include_picture: bool = True
      split_mode: str = "book"
      cleaner_cfg: TextCleanerConfig = field(default_factory=TextCleanerConfig)

  class BookConfig(TypedDict):
      book_id: str
      start_id: NotRequired[str]
      end_id: NotRequired[str]
      ignore_ids: NotRequired[list[str]]
  ```

* **登录与搜索**

  ```python
  @dataclass
  class LoginField:
      name: str
      label: str
      type: Literal["text", "password", "cookie"]
      required: bool
      default: str = ""
      placeholder: str = ""
      description: str = ""

  class SearchResult(TypedDict):
      site: str
      book_id: str
      book_url: str
      cover_url: str
      title: str
      author: str
      latest_chapter: str
      update_date: str
      word_count: str
      priority: int
  ```

---

## 9. 站点扩展指引（最小实现）

1. 新建目录：`plugins/sites/<site_key>/`
2. 至少实现：
   * `fetcher.py`（网络请求、取书籍页与章节页）
   * `parser.py`（解析为 `BookInfoDict` 与 `ChapterDict`）
3. 可选：
   * `downloader.py` / `exporter.py`（否则回退 `common` 实现）
   * `searcher.py`（用于 CLI/Web 搜索）
4. 在类上使用对应注册器装饰器（见 6.2 / 6.3）
5. 若站点需要登录：
   * 在 `FetcherProtocol.login_fields` 暴露字段（`text/password/cookie`）
   * `login()` 成功后置 `is_logged_in=True`，并实现 `load_state()/save_state()` 以复用会话

---

## 10. 常见用法片段

**A. 仅导出为 EPUB**

```python
from novel_downloader.apps.cli.handlers.export import export_books
from novel_downloader.infra.config.file_io import load_config
from novel_downloader.infra.config.adapter import ConfigAdapter

cfg = load_config("./settings.toml")
adapter = ConfigAdapter(cfg, "aaatxt")
export_books(
    "aaatxt",
    [{"book_id": "123"}],
    adapter.get_exporter_config(),
    formats=["epub"],
)
```

**B. 通过搜索后立即下载+导出**

```python
import asyncio
from novel_downloader.plugins.searching import search
from novel_downloader.apps.cli.handlers.download import download_books
from novel_downloader.apps.cli.handlers.export import export_books
from novel_downloader.infra.config.file_io import load_config
from novel_downloader.infra.config.adapter import ConfigAdapter

async def main():
    results = await search("诡秘之主", sites=["aaatxt"], per_site_limit=3)
    pick = results[0]
    adapter = ConfigAdapter(load_config("./settings.toml"), pick["site"])
    books = [{"book_id": pick["book_id"]}]
    if await download_books(
        pick["site"], books,
        adapter.get_downloader_config(),
        adapter.get_fetcher_config(),
        adapter.get_parser_config(),
        adapter.get_login_config(),
    ):
        export_books(pick["site"], books, adapter.get_exporter_config())

asyncio.run(main())
```
