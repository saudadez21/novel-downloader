## Parsers

### 目录

- [Parsers](#parsers)
  - [目录](#目录)
  - [导入方式](#导入方式)
  - [使用示例](#使用示例)
  - [ParserProtocol 接口](#parserprotocol-接口)

---

### 导入方式

```python
from novel_downloader.core.parsers import QidianParser
```

描述: 直接导入站点专用的 Parser 类

示例:

```python
parser = QidianParser(parser_cfg)
```

---

```python
from novel_downloader.core import get_parser
```

描述: 根据站点名称和 `ParserConfig` 获取对应 Parser 实例

参数:

* `site`: 站点名称, 如 `"qidian"`
* `config`: `ParserConfig` 配置对象

返回:

* `ParserProtocol` 实例

示例:

```python
parser = get_parser("qidian", parser_cfg)
```

---

### 使用示例

```python
parser_cfg = ParserConfig(
    cache_dir="./novel_cache",
    decode_font=True,
    use_ocr=True,
    use_freq=False,
    use_vec=True,
    ocr_version="v2.0",
    ocr_weight=0.5,
    vec_weight=0.5,
)

qd_parser = QidianParser(parser_cfg)
html_str = Path(f"{chap_id}.html").read_text(encoding="utf-8")
parsed = qd_parser.parse_chapter([html_str], chap_id)
if parsed:
    with open(f"{chap_id}.json", "w", encoding="utf-8") as f:
        json.dump(parsed, f, ensure_ascii=False, indent=2)
```

---

### ParserProtocol 接口

> `novel_downloader.core.ParserProtocol`

```python
def parse_book_info(
    self,
    html_list: list[str],
    **kwargs: Any,
) -> dict[str, Any]:
```

描述: 解析图书信息页面内容, 返回元数据字典

参数:

* `html_list`: 图书信息页的 HTML 列表

返回:

* `dict[str, Any]`, 包含标题、作者、章节列表等信息

示例:

```python
info = parser.parse_book_info(pages)
```

---

```python
def parse_chapter(
    self,
    html_list: list[str],
    chapter_id: str,
    **kwargs: Any,
) -> ChapterDict | None:
```

描述: 解析单章内容, 返回结构化章节数据

参数:

* `html_list`: 章节页面的 HTML 列表
* `chapter_id`: 章节标识

返回:

* `ChapterDict` 或 `None`

示例:

```python
chapter = parser.parse_chapter(pages, "77882211")
```
