## Factory 工厂函数

### 目录

- [Factory 工厂函数](#factory-工厂函数)
  - [目录](#目录)
  - [工厂函数列表](#工厂函数列表)
  - [注册机制说明](#注册机制说明)

---

### 工厂函数列表

```python
def get_downloader(
    fetcher: FetcherProtocol,
    parser: ParserProtocol,
    exporter: ExporterProtocol,
    site: str,
    config: DownloaderConfig,
) -> DownloaderProtocol:
```

描述: 根据站点名称和配置, 返回对应的 `DownloaderProtocol` 实例

示例:

```python
downloader = get_downloader(
    fetcher, parser, exporter,
    site="qidian",
    config=downloader_cfg,
)
```

---

```python
def get_exporter(
    site: str,
    config: ExporterConfig,
) -> ExporterProtocol:
```

描述: 根据站点名称和导出配置, 返回对应的 `ExporterProtocol` 实例

示例:

```python
exporter = get_exporter("qidian", exporter_cfg)
```

---

```python
def get_parser(
    site: str,
    config: ParserConfig,
) -> ParserProtocol:
```

描述: 根据站点名称和解析配置, 返回对应的 `ParserProtocol` 实例

示例:

```python
parser = get_parser("qidian", parser_cfg)
```

---

```python
def get_fetcher(
    site: str,
    config: FetcherConfig,
) -> FetcherProtocol:
```

描述: 根据站点名称和抓取配置, 返回对应的 `FetcherProtocol` 实例

示例:

```python
async with get_fetcher("qidian", fetcher_cfg) as fetcher:
    ...
```

---

### 注册机制说明

描述: 每个工厂函数内部维护一个预定义的注册表, 根据传入的 `site` 或 `name` 在注册表中查找对应的实现类, 并使用传入的 `config` 实例化后返回。

示例:

```python
# 工厂函数的内部示例 (伪代码)
_registry = {
    "qidian": QidianFetcher,
    ...
}

def get_fetcher(site, config):
    cls = _registry[site]
    return cls(config)
```
