# API 描述文档

- [API 描述文档](#api-描述文档)
  - [1. 概览与分层](#1-概览与分层)
  - [2. 快速开始](#2-快速开始)
  - [3. 配置 API (`infra/config`)](#3-配置-api-infraconfig)
  - [4. 插件系统 (`plugins`)](#4-插件系统-plugins)
  - [5. 数据模型 (`schemas/*.py`)](#5-数据模型-schemaspy)
    - [章节与书籍](#章节与书籍)
    - [配置数据类](#配置数据类)
    - [登录与搜索](#登录与搜索)
  - [6. 站点扩展指引 (最小实现)](#6-站点扩展指引-最小实现)
  - [7. 常见用法片段](#7-常见用法片段)
    - [A. 仅导出为 EPUB](#a-仅导出为-epub)
    - [B. 通过搜索后立即下载+导出](#b-通过搜索后立即下载导出)
    - [C. 需登录的站点](#c-需登录的站点)
    - [D. 下载进度接口](#d-下载进度接口)

---

## 1. 概览与分层

* **apps/**：应用入口与界面
  * **cli/**：命令行 (`argparse`、`rich`), `ui_adapters` 实现 UI 协议
  * **web/**：NiceGUI 前端 (页面、组件、任务管理、登录对话)
* **infra/**：基础设施 (配置、网络、路径/文件、日志、i18n、OCR/JSBridge、持久化)
* **libs/**：通用库 (EPUB、文件工具、加解密、URL/时间工具)
* **plugins/**：站点插件层 (统一由 `registry` 管理)
  * **fetcher**：网络会话与登录、状态保存
  * **parser**：HTML 解析为结构化数据
  * **client**：站点客户端 (统一下载/处理/导出/资源管理)
  * **searcher**：站点搜索
  * **registry**：注册与获取
* **schemas/**：数据模型与配置数据类
* **locales/**：多语言资源

---

## 2. 快速开始

```python
import asyncio
from novel_downloader.plugins import registrar
from novel_downloader.schemas import BookConfig, ClientConfig

async def main() -> None:
    # 指定站点标识
    site = "n23qb"

    # 指定书籍 ID
    book = BookConfig(book_id="12282")

    # 创建客户端配置
    cfg = ClientConfig(request_interval=0.5)

    # 获取站点客户端实例
    client = registrar.get_client(site, cfg)

    # 在异步上下文中执行下载
    async with client:
        await client.download_book(book)

    # 下载完成后执行导出操作
    client.export_book(book, formats=["txt", "epub"])

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 3. 配置 API (`infra/config`)

**3.1 `load_config(config_path: str|Path|None) -> dict[str, Any]`**

从 TOML 读取并返回通用字典配置 (找不到或解析失败抛异常)。

**3.2 `ConfigAdapter`**

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

## 4. 插件系统 (`plugins`)

**4.1 协议 (`plugins/protocols/*.py`)**

`ClientProtocol`

```python
class ClientProtocol(Protocol):
    """
    Core interface for downloading, processing, exporting,
    and managing book-related resources of a site.
    """

    async def init(self, fetcher_cfg: FetcherConfig, parser_cfg: ParserConfig) -> None: ...
    async def close(self) -> None: ...

    async def login(
        self, *, ui: LoginUI, login_cfg: dict[str, str] | None = None, **kwargs: Any
    ) -> bool: ...

    async def download_book(
        self, book: BookConfig, *, ui: DownloadUI | None = None, **kwargs: Any
    ) -> None: ...

    def process_book(
        self, book: BookConfig, processors: list[ProcessorConfig], *,
        ui: ProcessUI | None = None, **kwargs: Any
    ) -> None: ...

    async def cache_media(
        self, book: BookConfig, *, force_update: bool = False, concurrent: int = 10,
        **kwargs: Any
    ) -> None: ...

    def export_book(
        self,
        book: BookConfig,
        cfg: ExporterConfig | None = None,
        *,
        formats: list[str] | None = None,
        stage: str | None = None,
        ui: ExportUI | None = None,
        **kwargs: Any,
    ) -> dict[str, list[Path]]: ...

    async def __aenter__(self) -> Self: ...
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        tb: types.TracebackType | None,
    ) -> None: ...
```

**4.2 注册器 (`plugins/registry.py`)**

```python
from novel_downloader.plugins import registrar

# 装饰器注册 (site_key 缺省时取模块父目录名)
@registrar.register_fetcher("aaatxt")
class AAAFetcher(...): ...

@registrar.register_parser("aaatxt")
class AAAParser(...): ...

@registrar.register_client("aaatxt")
class AAAClient(...):
    ...
```

获取实例：

```python
client = registrar.get_client("aaatxt")  # -> ClientProtocol

fetcher = registrar.get_fetcher(site, FetcherConfig)  # -> FetcherProtocol
parser = registrar.get_parser(site, ParserConfig)  # -> ParserProtocol
```

> 站点包命名要求：`plugins.sites.<site_key>.<kind>`; 若首字符为数字，规范化为前缀 `n` (如 `3xx` -> `n3xx`)。

---

## 5. 数据模型 (`schemas/*.py`)

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
    timeout: float = 10.0
    max_connections: int = 10
    max_rps: float = 1000.0
    user_agent: str | None = None
    headers: dict[str, str] | None = None
    verify_ssl: bool = True
    locale_style: str = "simplified"

@dataclass
class OCRConfig: ...
@dataclass
class ParserConfig:
    cache_dir: str = "./novel_cache"
    use_truncation: bool = True
    enable_ocr: bool = False
    batch_size: int = 32
    remove_watermark: bool = False
    cut_mode: str = "none"
    ocr_cfg: OCRConfig = field(default_factory=OCRConfig)

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

## 6. 站点扩展指引 (最小实现)

1. 新建目录：`plugins/sites/<site_key>/`
2. 至少实现：
   * `fetcher.py` (网络请求、取书籍页与章节页)
   * `parser.py` (解析为 `BookInfoDict` 与 `ChapterDict`)
3. 可选：
   * `client.py` (否则回退 `common` 实现)
   * `searcher.py` (用于 CLI/Web 搜索)
4. 在类上使用对应注册器装饰器
5. 若站点需要登录：
   * 在 `FetcherProtocol.login_fields` 暴露字段 (`text/password/cookie`)
   * `login()` 成功后置 `is_logged_in=True`，并实现 `load_state()/save_state()` 以复用会话

---

## 7. 常见用法片段

### A. 仅导出为 EPUB

```python
from novel_downloader.plugins import registrar
from novel_downloader.schemas import BookConfig

site = "n23qb"  # 站点标识
book = BookConfig(book_id="12282")
client = registrar.get_client(site)
client.export_book(book, formats=["epub"])
```

### B. 通过搜索后立即下载+导出

```python
import asyncio
from novel_downloader.plugins import registrar
from novel_downloader.plugins.search import search
from novel_downloader.schemas import ClientConfig, BookConfig


async def main() -> None:
    cfg = ClientConfig(request_interval=0.5)

    keyword = "三体"
    results = await search(keyword, sites=["n23qb"])
    if not results:
        print(f"未找到与 '{keyword}' 匹配的结果")
        return

    print(f"共找到 {len(results)} 个结果:")
    for idx, item in enumerate(results[:5], start=1):
        print(f"[{idx}] {item['title']} - {item['author']} ({item['site']})")

    # 选择第一个结果进行下载
    first = results[0]
    site = first["site"]
    book = BookConfig(book_id=first["book_id"])

    print(f"\n开始下载: {first['title']} - {first['author']} (站点: {site})")
    client = registrar.get_client(site, cfg)

    async with client:
        await client.download_book(book)

    # 导出为 txt 与 epub
    export_result = client.export_book(book, formats=["txt", "epub"])

    print("\n导出完成:")
    for fmt, paths in export_result.items():
        for path in paths:
            print(f" - {fmt}: {path}")

if __name__ == "__main__":
    asyncio.run(main())
```

### C. 需登录的站点

```python
import asyncio
from typing import Any
from getpass import getpass

from novel_downloader.plugins import registrar
from novel_downloader.schemas import BookConfig, ClientConfig, LoginField
from novel_downloader.infra.cookies import parse_cookies

class SimpleLoginUI:
    async def prompt(
        self,
        fields: list[LoginField],
        prefill: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        prefill = prefill or {}
        result: dict[str, Any] = {}

        for field in fields:
            print(f"\n[{field.label}] ({field.name})")
            if field.description:
                print(f"说明: {field.description}")
            if field.placeholder:
                print(f"提示: {field.placeholder}")

            existing_value = prefill.get(field.name, "").strip()
            if existing_value:
                print("使用配置中的值。")
                result[field.name] = existing_value
                continue

            value: str | dict[str, str] = ""
            for _ in range(5):
                if field.type == "password":
                    value = getpass("请输入密码: ")
                elif field.type == "cookie":
                    raw = input("请输入 Cookies: ").strip()
                    value = parse_cookies(raw)
                else:
                    value = input("请输入值: ").strip()

                if not value and field.default:
                    value = field.default

                if not value and field.required:
                    print("此字段为必填项，请输入有效值。")
                else:
                    break

            result[field.name] = value

        return result

    def on_login_failed(self) -> None:
        print("登录失败：请检查账号、密码或 Cookies。")

    def on_login_success(self) -> None:
        print("登录成功。")

async def main() -> None:
    cfg = ClientConfig(request_interval=0.5)

    site = "qidian"
    book = BookConfig(book_id="1001535146")

    client = registrar.get_client(site, cfg)

    async with client:
        # 登录 (若站点要求)
        await client.login(ui=SimpleLoginUI())
        # 下载
        await client.download_book(book)

    # 导出为 txt 与 epub
    export_result = client.export_book(book, formats=["txt", "epub"])

    print("\n导出完成:")
    for fmt, paths in export_result.items():
        for path in paths:
            print(f" - {fmt}: {path}")

if __name__ == "__main__":
    asyncio.run(main())
```

### D. 下载进度接口

```python
import asyncio

from novel_downloader.plugins import registrar
from novel_downloader.schemas import BookConfig, ClientConfig

class SimpleDownloadUI:
    async def on_start(self, book: BookConfig) -> None:
        print(f"\n开始下载: {book.book_id}")

    async def on_progress(self, done: int, total: int) -> None:
        percent = (done / total * 100) if total else 0.0
        print(f"\r进度: {done}/{total} ({percent:.1f}%)", end="", flush=True)

    async def on_complete(self, book: BookConfig) -> None:
        print(f"\n下载完成: {book.book_id}")

async def main() -> None:
    cfg = ClientConfig(request_interval=0.5)

    site = "n23qb"
    book = BookConfig(book_id="12282")

    client = registrar.get_client(site, cfg)

    async with client:
        await client.download_book(book, ui=SimpleDownloadUI())

    # 导出为 txt 与 epub
    export_result = client.export_book(book, formats=["txt", "epub"])

    print("\n导出完成:")
    for fmt, paths in export_result.items():
        for path in paths:
            print(f" - {fmt}: {path}")

if __name__ == "__main__":
    asyncio.run(main())
```
