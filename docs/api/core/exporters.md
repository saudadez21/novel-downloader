## Exporters

### 目录

- [Exporters](#exporters)
  - [目录](#目录)
  - [导入方式](#导入方式)
  - [使用示例](#使用示例)
  - [ExporterProtocol 接口](#exporterprotocol-接口)

---

### 导入方式

```python
from novel_downloader.core.exporters import QidianExporter
```

描述: 直接导入站点专用的 Exporter 类

示例:

```python
exporter = QidianExporter(exporter_cfg)
```

---

```python
from novel_downloader.core import get_exporter
```

描述: 根据站点名称和 `ExporterConfig` 获取对应 Exporter 实例

参数:

* `site`: 站点名称, 如 `"qidian"`
* `config`: `ExporterConfig` 配置对象

返回:

* `ExporterProtocol` 实例

示例:

```python
exporter = get_exporter("qidian", exporter_cfg)
```

---

### 使用示例

```python
exporter = get_exporter(site, exporter_cfg)

# 以文本格式导出全部章节
exporter.export_as_txt(book_id)

# 以 EPUB 格式导出
exporter.export_as_epub(book_id)
```

---

### ExporterProtocol 接口

> `novel_downloader.core.ExporterProtocol`

```python
def export(self, book_id: str) -> None:
```

描述: 按配置指定的格式导出整本书, 单方法调用所有子格式

参数:

* `book_id`: 图书标识

示例:

```python
exporter.export(book_id)
```

---

```python
def export_as_txt(self, book_id: str) -> None:
```

描述: 将整本书持久化为 `.txt` 文件

参数:

* `book_id`: 图书标识

示例:

```python
exporter.export_as_txt(book_id)
```

---

```python
def export_as_epub(self, book_id: str) -> None:
```

描述: 将整本书持久化为 `.epub` 文件

参数:

* `book_id`: 图书标识

示例:

```python
exporter.export_as_epub(book_id)
```
