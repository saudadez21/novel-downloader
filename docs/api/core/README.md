## Core 模块概览

`novel_downloader.core` 是项目的核心调度层, 负责:

* 定义并导出四个协议:

  * `FetcherProtocol` (抓取)
  * `ParserProtocol` (解析)
  * `ExporterProtocol` (导出)
  * `DownloaderProtocol` (下载)

* 通过工厂函数动态注册并实例化各站点实现, 提供统一、可扩展的调用入口

---

## 模块组成

* [**fetchers**](fetchers.md)
  针对各站点的抓取器实现, 符合 `FetcherProtocol`

* [**parsers**](parsers.md)
  针对各站点的解析器实现, 符合 `ParserProtocol`

* [**exporters**](exporters.md)
  针对各站点的导出器实现, 符合 `ExporterProtocol`

* [**downloaders**](downloaders.md)
  将抓取、解析、导出整合, 符合 `DownloaderProtocol`

* [**searchers**](searchers.md)
  根据关键词搜索并返回结果

---

## 快速使用示例

```python
from novel_downloader.core import (
    get_fetcher, get_parser, get_exporter, get_downloader, search
)

async def _print_progress(done: int, total: int) -> None:
    print(f"下载进度: {done}/{total} 章")

keyword = "关键词"
sites = ["b520"]

results = search(
    keyword=keyword,
    sites=sites,
    limit=10,
    per_site_limit=5,
)

chosen = results[0]  # 选择一个
book_id = chosen["book_id"]  # 或不使用 search 直接定义
site_key = chosen["site"]  # 了例如 "qidian"

# 准备配置对象
fetcher_cfg = FetcherConfig(...)
parser_cfg  = ParserConfig(...)
exporter_cfg = ExporterConfig(...)
downloader_cfg = DownloaderConfig(...)
book_config = {
    "book_id": book_id,
}

# 创建 Parser/Exporter
parser   = get_parser(site_key, parser_cfg)
exporter = get_exporter(site_key, exporter_cfg)

# 异步上下文中创建并登录 Fetcher
async with get_fetcher(site_key, fetcher_cfg) as fetcher:
    await fetcher.login(username, password)

    # 下载整本书
    downloader = get_downloader(
        fetcher,
        parser,
        site=site_key,
        config=downloader_cfg,
    )
    await downloader.download(book_config, progress_hook=_print_progress)

# 导出整本书
exporter.export(book_config["book_id"])
```
