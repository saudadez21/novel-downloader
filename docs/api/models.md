## 数据模型

### 目录

- [数据模型](#数据模型)
  - [目录](#目录)
  - [基础类型](#基础类型)
  - [章节类型](#章节类型)
  - [配置模型](#配置模型)
  - [图书配置](#图书配置)
  - [登录字段](#登录字段)

---

### 基础类型

> `novel_downloader.utils.models`

```python
SplitMode = Literal["book", "volume"]
```

描述: 常用枚举类型别名，限定函数或配置中可接受的字符串值

---

### 章节类型

> `novel_downloader.utils.models`

```python
class ChapterDict(TypedDict, total=True):
    """
    TypedDict for a novel chapter.

    Fields:
        id      -- Unique chapter identifier
        title   -- Chapter title
        content -- Chapter text
        extra   -- Arbitrary metadata (e.g. author remarks, timestamps)
    """

    id: str
    title: str
    content: str
    extra: dict[str, Any]
```

描述: 章节数据的结构化类型定义

示例:

```python
chapter: ChapterDict = {
    "id": "1001",
    "title": "第一章",
    "content": "章节内容...",
    "extra": {"remark": "无需翻译"}
}
```

---

### 配置模型

> `novel_downloader.utils.models`

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
```

描述: 网页内容抓取相关参数配置

示例:

```python
fetcher_cfg = FetcherConfig(mode="browser", headless=True)
```

---

```python
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
    username: str = ""
    password: str = ""
    cookies: str = ""
```

描述: 下载流程相关参数配置

示例:

```python
down_cfg = DownloaderConfig(skip_existing=False, mode="browser")
```

---

```python
@dataclass
class ParserConfig:
    cache_dir: str = "./novel_cache"
    use_truncation: bool = True
    decode_font: bool = False
    batch_size: int = 32
    save_font_debug: bool = False
```

描述: 章节解析与 OCR/向量匹配相关配置

示例:

```python
parser_cfg = ParserConfig(use_freq=True, gpu_id=0)
```

---

```python
@dataclass
class ExporterConfig:
    cache_dir: str = "./novel_cache"
    raw_data_dir: str = "./raw_data"
    output_dir: str = "./downloads"
    clean_text: bool = True
    make_txt: bool = True
    make_epub: bool = False
    make_md: bool = False
    make_pdf: bool = False
    append_timestamp: bool = True
    filename_template: str = "{title}_{author}"
    include_cover: bool = True
    include_toc: bool = False
    include_picture: bool = False
    split_mode: SplitMode = "book"
```

描述: 导出文件格式和切分策略配置

示例:

```python
exp_cfg = ExporterConfig(make_epub=True)
```

---

### 图书配置

> `novel_downloader.utils.models`

```python
class BookConfig(TypedDict):
    book_id: str
    start_id: NotRequired[str]
    end_id: NotRequired[str]
    ignore_ids: NotRequired[list[str]]
```

描述: 单本书下载任务的 ID 范围与忽略列表

示例:

```python
book_cfg: BookConfig = {
    "book_id": "1030412702",
    "start_id": "100",
    "end_id": "200",
    "ignore_ids": ["150", "155"]
}
```

---

### 登录字段

> `novel_downloader.utils.models`

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
```

描述: 登录表单字段模型，用于动态生成或验证登录输入

示例:

```python
field = LoginField(
    name="username",
    label="用户名",
    type="text",
    required=True,
    placeholder="请输入用户名"
)
```
