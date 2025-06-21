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

* [**factory**](factory.md)
  提供 `get_fetcher`、`get_parser`、`get_exporter`、`get_downloader` 四个工厂函数

* [**fetchers**](fetchers.md)
  针对各站点的抓取器实现, 符合 `FetcherProtocol`

* [**parsers**](parsers.md)
  针对各站点的解析器实现, 符合 `ParserProtocol`

* [**exporters**](exporters.md)
  针对各站点的导出器实现, 符合 `ExporterProtocol`

* [**downloaders**](downloaders.md)
  将抓取、解析、导出整合, 符合 `DownloaderProtocol`

---

## 快速使用示例

```python
from novel_downloader.core import (
    get_fetcher, get_parser, get_exporter, get_downloader
)

# 准备配置对象
fetcher_cfg = FetcherConfig(...)
parser_cfg  = ParserConfig(...)
exporter_cfg = ExporterConfig(...)
downloader_cfg = DownloaderConfig(...)
book_config = {
    "book_id": 12345,
}

# 创建 Parser/Exporter
parser   = get_parser("qidian", parser_cfg)
exporter = get_exporter("qidian", exporter_cfg)

# 异步上下文中创建并登录 Fetcher
async with get_fetcher("qidian", fetcher_cfg) as fetcher:
    await fetcher.login(username, password)

    # 下载整本书
    downloader = get_downloader(
        fetcher,
        parser,
        site="qidian",
        config=downloader_cfg,
    )
    await downloader.download(book_config, progress_hook=progress_hook)

# 导出整本书
exporter.export(book["book_id"])
```
