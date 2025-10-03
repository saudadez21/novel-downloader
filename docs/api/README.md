# API 描述文档

---

## 1. 概览与分层

整个项目采用分层架构，主要目录与职责如下:

* **apps/** (应用层): 具体入口与界面
  * **cli/**：命令行界面
    使用 `argparse` 解析参数，结合 `rich` 输出，`ui_adapters` 实现 `usecases/protocols.py` 定义的 UI 协议。
  * **web/**：Web 前端 (基于 NiceGUI)
    提供页面与组件，管理下载任务、登录对话；同样通过 `ui_adapters` 实现 UI 协议。
  * **constants.py**：站点显示名映射
    保存 `dict[str, str]`，例如 `aaatxt -> "3A电子书"`，供界面展示。

* **usecases/** (应用用例层):  封装完整的业务流程，对外暴露可直接调用的函数
  * `download.py`：下载流程（依赖 `LoginUI`、`DownloadUI` 协议）
  * `export.py`：导出流程（依赖 `ExportUI` 协议）
  * `login.py`：登录辅助（依赖 `LoginUI` 协议）
  * `config.py`：配置加载与初始化（依赖 `ConfigUI` 协议）
  * `search.py`：多站点搜索（聚合/流式 API）
  * `protocols.py`：UI 协议定义（`LoginUI` / `DownloadUI` / `ExportUI` / `ConfigUI`）

* **infra/** (基础设施层): 提供与外部环境交互的能力，例如:
  * 配置加载与适配
  * 网络下载（`aiohttp` 默认参数等）
  * 路径与文件管理
  * 日志
  * 国际化（i18n）
  * OCR/JSBridge
  * 持久化（状态存储）

* **libs/** (通用库), 与业务无关的工具集合：
  * EPUB 构建
  * 文件系统工具
  * 加解密
  * 文本清洗
  * URL 解析
  * 时间工具

* **plugins/** (站点插件层): 实现具体站点的抓取/解析/导出逻辑，统一通过注册器 (`registry`) 管理。
  * **fetcher**：负责获取页面（含登录、状态保存）
  * **parser**：负责解析 HTML，提取书籍与章节
  * **downloader**：协调 fetcher 与 parser 完成下载
  * **exporter**：负责导出到本地格式（txt、epub 等）
  * **searcher**：站点搜索入口
  * **registry**：统一注册与获取插件的接口

* **schemas/** (数据模型层): 定义统一的数据结构，方便在各层传递，主要采用 `TypedDict` 与 `dataclass`。

* **locales/** (多语言资源): 存放界面与提示语的本地化文本。

---

## 2. 快速开始

### 2.1 按书籍 ID/URL 下载并导出 (与 CLI 同流程)

```python
import asyncio
from pathlib import Path

from novel_downloader.infra.config import load_config, ConfigAdapter
from novel_downloader.libs.book_url_resolver import resolve_book_url

from novel_downloader.usecases.download import download_books
from novel_downloader.usecases.export import export_books

# CLI 侧 UI 适配器
from novel_downloader.apps.cli.ui_adapters import CLILoginUI, CLIDownloadUI, CLIExportUI

async def main():
    config = load_config(Path("./settings.toml"))

    resolved = resolve_book_url("https://example.com/book/123")
    if resolved is None:
        return

    site = resolved["site_key"]
    book = resolved["book"]
    adapter = ConfigAdapter(config=config)

    await download_books(
        site=site,
        books=[book],
        downloader_cfg=adapter.get_downloader_config(site),
        fetcher_cfg=adapter.get_fetcher_config(site),
        parser_cfg=adapter.get_parser_config(site),
        login_ui=CLILoginUI(),
        download_ui=CLIDownloadUI(),
        login_config=adapter.get_login_config(site),
    )

    export_books(
        site=site,
        books=[book],
        exporter_cfg=adapter.get_exporter_config(site),
        export_ui=CLIExportUI(),
    )

asyncio.run(main())
```

### 2.2 直接通过插件注册器使用

```python
from novel_downloader.plugins import registrar  # 插件注册器单例
from novel_downloader.schemas import BookConfig, FetcherConfig, ParserConfig, DownloaderConfig

parser = registrar.get_parser("aaatxt", ParserConfig())
async def run():
    async with registrar.get_fetcher("aaatxt", FetcherConfig()) as fetcher:
        downloader = registrar.get_downloader(fetcher, parser, "aaatxt", DownloaderConfig())
        await downloader.download(BookConfig(book_id="123"))
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

* 位置参数：`book_ids...`（与 `--site` 搭配为 ID 模式; 不带 `--site` 时必须是单个 URL）
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
  * `client_dialog.py`：注册登录输入弹窗; 配合 `fetcher.login_fields` 动态渲染
  * `cred_broker.py`：登录凭据请求/回传
* **ui_adapters.py**：实现 `LoginUI` / `DownloadUI` / `ExportUI`（写入/更新 `DownloadTask` 状态）
* **components/**：UI 组件（如导航）
* **main.py**：应用入口

> 交互: `page -> task_manager -> (need login?) -> WebLoginUI.prompt(...) -> download_books(...) -> export_books(...)`

---

## 5. 配置 API（`infra/config`）

### 5.1 `load_config(config_path: str|Path|None) -> dict[str, Any]`

从 TOML 读取并返回通用字典配置（找不到或解析失败抛异常）。

### 5.2 `ConfigAdapter`

将通用配置映射为结构化数据类，按字段优先级解析：

1. `config["sites"][<site>]`
2. `config["sites"]["common"]`
3. `config["general"]`
3. 默认值

**构造:**

```python
adapter = ConfigAdapter(config)
```

**方法:**

```python
get_fetcher_config(site: str)   -> FetcherConfig
get_downloader_config(site: str)-> DownloaderConfig
get_parser_config(site: str)    -> ParserConfig
get_exporter_config(site: str)  -> ExporterConfig
get_login_config(site: str)     -> dict[str, str]
get_book_ids(site: str)         -> list[BookConfig]

get_plugins_config() -> dict[str, Any]
get_log_level()      -> str
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

> 站点包命名要求：`plugins.sites.<site_key>.<kind>`; 若首字符为数字，规范化为前缀 `n`（如 `3xx` -> `n3xx`）。

---

## 7. 用例层（`usecases`）

位于框架最上层，提供可直接调用的高阶业务流程：登录、下载、导出、配置管理、搜索等。

### 7.1 协议（`usecases/protocols.py`）

以下协议定义与界面交互的回调事件。实现这些协议即可接收进度、错误等通知。

* **LoginUI**：登录交互
  * `prompt`：提示用户输入账号/密码或其他登录字段
  * `on_login_failed`：登录失败时回调
  * `on_login_success`：登录成功时回调

* **DownloadUI**：下载过程交互
  * `on_start`：开始下载一本书时
  * `on_progress`：下载进度更新
  * `on_complete`：一本书下载完成
  * `on_book_error`：某本书下载失败
  * `on_site_error`：站点不可用或不支持

* **ExportUI**：导出过程交互
  * `on_start`：开始导出一本书时
  * `on_success`：导出成功
  * `on_error`：导出失败
  * `on_unsupported`：格式不受支持

* **ConfigUI**：配置文件交互
  * `on_missing`：配置文件不存在
  * `on_created`：配置文件已新建
  * `on_invalid`：配置文件损坏或无效
  * `on_abort`：用户放弃加载/创建配置
  * `confirm_create`：确认是否新建配置

```python
class LoginUI(Protocol):
    async def prompt(self, fields: list[LoginField], prefill: dict[str, Any] | None = None) -> dict[str, Any]: ...
    def on_login_failed(self) -> None: ...
    def on_login_success(self) -> None: ...

class DownloadUI(Protocol):
    async def on_start(self, book: BookConfig) -> None: ...
    async def on_progress(self, done: int, total: int) -> None: ...
    async def on_complete(self, book: BookConfig) -> None: ...
    async def on_book_error(self, book: BookConfig, error: Exception) -> None: ...
    async def on_site_error(self, site: str, error: Exception) -> None: ...

class ExportUI(Protocol):
    def on_start(self, book: BookConfig, fmt: str | None = None) -> None: ...
    def on_success(self, book: BookConfig, fmt: str, path: Path) -> None: ...
    def on_error(self, book: BookConfig, fmt: str | None, error: Exception) -> None: ...
    def on_unsupported(self, book: BookConfig, fmt: str) -> None: ...

class ConfigUI(Protocol):
    def on_missing(self, path: Path) -> None: ...
    def on_created(self, path: Path) -> None: ...
    def on_invalid(self, error: Exception) -> None: ...
    def on_abort(self) -> None: ...
    def confirm_create(self) -> bool: ...
```

### 7.2 流程函数

以下函数封装了对插件注册表 (`registrar`) 的调用，直接调用即可完成对应任务:

```python
# 登录辅助
async def ensure_login(
    fetcher: FetcherProtocol,
    login_ui: LoginUI,
    login_config: dict[str, str] | None = None,
) -> bool: ...

# 下载
async def download_books(
    site: str,
    books: list[BookConfig],
    downloader_cfg: DownloaderConfig,
    fetcher_cfg: FetcherConfig,
    parser_cfg: ParserConfig,
    login_ui: LoginUI,
    download_ui: DownloadUI,
    login_config: dict[str, str] | None = None,
) -> None: ...

# 导出
def export_books(
    site: str,
    books: list[BookConfig],
    exporter_cfg: ExporterConfig,
    export_ui: ExportUI,
    formats: list[str] | None = None,
) -> None: ...

# 配置加载/初始化
def load_or_init_config(
    config_path: Path | None,
    config_ui: ConfigUI,
) -> dict[str, Any] | None: ...
```

---

### 7.3 搜索（`usecases/search.py`）

支持在多个站点并行搜索，返回聚合结果，或以流式方式按站点依次返回。

```python
# 聚合搜索
async def search(
    keyword: str,
    sites: Sequence[str] | None = None,
    limit: int | None = None,
    per_site_limit: int = 5,
    timeout: float = 5.0,
) -> list[SearchResult]: ...
```

* `keyword`: 搜索关键词
* `sites`: 限定搜索的站点 key，默认搜索所有已注册站点
* `limit`: 总结果数量上限
* `per_site_limit`: 每个站点的结果数量上限
* `timeout`: 每个请求的超时时间 (秒)
* 返回：按优先级排序的搜索结果列表

```python
# 流式搜索
async def search_stream(
    keyword: str,
    sites: Sequence[str] | None = None,
    per_site_limit: int = 5,
    timeout: float = 5.0,
) -> AsyncGenerator[list[SearchResult], None]: ...
```

* 与 `search` 相同，但以异步生成器形式逐站点返回结果，适合需要实时展示的场景。

---

## 8. 数据模型（`schemas/*.py`）

> 下述选摘用于理解 I/O 形状; 以实际代码为准。

### 章节与书籍

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

### 配置数据类

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

### 登录与搜索

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

### A. 仅导出为 EPUB

```python
from pathlib import Path
from novel_downloader.infra.config import load_config, ConfigAdapter
from novel_downloader.usecases.export import export_books
from novel_downloader.apps.cli.ui_adapters import CLIExportUI
from novel_downloader.schemas import BookConfig

cfg = load_config(Path("./settings.toml"))
adapter = ConfigAdapter(cfg)

export_books(
    site="aaatxt",
    books=[BookConfig(book_id="123")],
    exporter_cfg=adapter.get_exporter_config("aaatxt"),
    export_ui=CLIExportUI(),
    formats=["epub"],
)
```

### B. 通过搜索后立即下载+导出

```python
import asyncio
from novel_downloader.usecases.download import download_books
from novel_downloader.usecases.export import export_books
from novel_downloader.usecases.search import search
from novel_downloader.infra.config import load_config, ConfigAdapter
from novel_downloader.apps.cli.ui_adapters import CLILoginUI, CLIDownloadUI, CLIExportUI
from novel_downloader.schemas import BookConfig

async def main():
    results = await search("诡秘之主", sites=["hetushu"], per_site_limit=3)
    pick = results[0]
    site = pick["site"]
    book = BookConfig(book_id=pick["book_id"])

    adapter = ConfigAdapter(load_config("./settings.toml"))

    await download_books(
        site=site,
        books=[book],
        downloader_cfg=adapter.get_downloader_config(site),
        fetcher_cfg=adapter.get_fetcher_config(site),
        parser_cfg=adapter.get_parser_config(site),
        login_ui=CLILoginUI(),
        download_ui=CLIDownloadUI(),
        login_config=adapter.get_login_config(site),
    )

    export_books(
        site=site,
        books=[book],
        exporter_cfg=adapter.get_exporter_config(site),
        export_ui=CLIExportUI(),
    )

asyncio.run(main())
```
