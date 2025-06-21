## Downloaders

### 目录

- [Downloaders](#downloaders)
  - [目录](#目录)
  - [导入方式](#导入方式)
  - [使用示例](#使用示例)
  - [DownloaderProtocol 接口](#downloaderprotocol-接口)

---

### 导入方式

```python
from novel_downloader.core.downloaders import QidianDownloader
```

描述: 直接导入站点专用的 Downloader 类, 初始化需传入 `fetcher`、`parser` 和 `config`

示例:

```python
downloader = QidianDownloader(fetcher, parser, downloader_cfg)
```

---

### 使用示例

```python
async def _print_progress(done: int, total: int) -> None:
    percent = done / total * 100
    print(f"下载进度: {done}/{total} 章 ({percent:.2f}%)")

parser = get_parser(site, parser_cfg)
exporter = get_exporter(site, exporter_cfg)

async with get_fetcher(site, fetcher_cfg) as fetcher:
    await fetcher.login(username, password)

    downloader = get_downloader(
        fetcher=fetcher,
        parser=parser,
        site=site,
        config=downloader_cfg,
    )

    # 下载单本书
    await downloader.download(
        book_config,
        progress_hook=_print_progress,
    )
    # 导出保存为 txt / epub
    exporter.export(book_id)

    # 批量下载多本书
    await downloader.download_many(
        [book1, book2],
        progress_hook=_print_progress,
    )
```

---

### DownloaderProtocol 接口

> `novel_downloader.core.DownloaderProtocol`

```python
async def download(
    self,
    book: BookConfig,
    *,
    progress_hook: Callable[[int, int], Awaitable[None]] | None = None,
    **kwargs: Any,
) -> None:
```

描述: 按照 `BookConfig` 下载单本书, 包括起始/结束/忽略章节, 抓取、解析并导出

参数:

* `book`: 包含 `book_id`、可选 `start_id`/`end_id`/`ignore_ids`
* `progress_hook`: 可选异步回调, 参数为已完成章节数和总章节数

示例:

```python
await downloader.download(book_config, progress_hook=_print_progress)
```

---

```python
async def download_many(
    self,
    books: list[BookConfig],
    *,
    progress_hook: Callable[[int, int], Awaitable[None]] | None = None,
    **kwargs: Any,
) -> None:
```

描述: 批量下载多本书, 行为与 `download` 相同, 按顺序执行

参数:

* `books`: `BookConfig` 列表
* `progress_hook`: 可选异步回调, 参数为已完成章节数和总章节数

示例:

```python
await downloader.download_many([book_config1, book_config2], progress_hook=_print_progress)
```
