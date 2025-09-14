## `settings.toml` 配置说明

* 配置分为三层：`[general]` (全局)、`[sites.<site>]` (站点级)、`[output]`/`[cleaner]` (产物与清洗)
* **优先级**：同名/相关行为**站点级覆盖全局** (`sites.<site> > general`)

### 目录

- [`settings.toml` 配置说明](#settingstoml-配置说明)
  - [目录](#目录)
  - [general 配置](#general-配置)
    - [主配置项](#主配置项)
    - [调试子节 `[general.debug]`](#调试子节-generaldebug)
    - [字体/OCR 子节 `[general.font_ocr]`](#字体ocr-子节-generalfont_ocr)
    - [示例配置](#示例配置)
  - [sites 配置](#sites-配置)
    - [通用键](#通用键)
    - [`book_ids` 字段说明](#book_ids-字段说明)
    - [示例: 起点 (`qidian`)](#示例-起点-qidian)
  - [output 配置](#output-配置)
    - [输出格式 `[output.formats]`](#输出格式-outputformats)
    - [命名规则 `[output.naming]`](#命名规则-outputnaming)
    - [EPUB 选项 `[output.epub]`](#epub-选项-outputepub)
    - [示例配置](#示例配置-1)
  - [cleaner 配置](#cleaner-配置)
    - [主配置项](#主配置项-1)
    - [标题清理 `[cleaner.title]`](#标题清理-cleanertitle)
    - [示例配置](#示例配置-2)

### general 配置

全局运行时设置, 面向下载 / 并发 / 速率限制 / 目录与存储的通用开关

#### 主配置项

| 参数名                | 类型    | 默认值             | 说明                                       |
| -------------------- | ------- | ----------------- | ------------------------------------------ |
| `retry_times`        | int     | 3                 | 请求失败重试次数                             |
| `backoff_factor`     | float   | 2.0               | 重试的退避因子 (每次重试等待时间将按倍数增加, 如 `2s`, `4s`, `8s`) |
| `timeout`            | float   | 30.0              | 单次请求超时 (秒)                            |
| `max_connections`    | int     | 10                | 最大并发连接数                               |
| `max_rps`            | float   | 1000.0            | 全局 RPS 上限 (requests per second)         |
| `request_interval`   | float   | 2.0               | **同一本书**章节请求的间隔 (秒)               |
| `raw_data_dir`       | string  | `"./raw_data"`    | 书籍数据存放目录                             |
| `output_dir`         | string  | `"./downloads"`   | 最终导出文件目录                             |
| `cache_dir`          | string  | `"./novel_cache"` | 本地缓存目录 (字体 / 图片等)                  |
| `workers`            | int     | 2                 | 下载任务协程数量                             |
| `skip_existing`      | bool    | true              | 下载时跳过本地已存在的章节文件                 |
| `storage_batch_size` | int     | 1                 | `sqlite` 每批提交的章节数 (提高写入性能)       |

> **站点压力与 503**
>
> 部分站点对高频访问敏感 (例如 >= 5 RPS), 可能返回 `503 Service Temporarily Unavailable`。
>
> 建议适当**降低** `max_rps` 或**增大** `request_interval`; 工具支持断点续爬, 已完成的数据不会重复抓取。

#### 调试子节 `[general.debug]`

| 参数名                | 类型   | 默认值             | 说明                                 |
| -------------------- | ------ | ----------------- | ------------------------------------ |
| `debug.save_html`    | bool   | false             | 是否保存抓取到的原始 HTML 到磁盘        |
| `debug.log_level`    | string | `"INFO"`          | 日志级别: DEBUG, INFO, WARNING, ERROR |

#### 字体/OCR 子节 `[general.font_ocr]`

用于支持混淆字体破解与文本识别

| 参数名             | 类型         | 默认值      | 说明                                                        |
| ----------------- | ------------ | ---------- | ----------------------------------------------------------- |
| `decode_font`     | bool         | false      | 是否尝试本地解码混淆字体                                      |
| `batch_size`      | int          | 32         | OCR 模型推理时的批处理大小                                    |
| `save_font_debug` | bool         | false      | 是否保存字体调试数据                                          |
| `model_name`      | str/None     | None       | 模型名称, 如果设置为None, 则使用 `PP-OCRv5_server_rec`         |
| `model_dir`       | str/None     | None       | 模型存储路径                                                  |
| `input_shape`     | tuple/None   | None       | 模型输入图像尺寸, 格式为 (C, H, W)                             |
| `device`          | str/None     | None       | 用于推理的设备, 例如："cpu"、"gpu"、"npu"、"gpu:0"、"gpu:0,1"  |
| `cpu_threads`     | int          | 10         | 在 CPU 上推理时使用的线程数量                                  |
| `enable_hpi`      | bool         | false      | 是否启用高性能推理                                             |

> **PaddleOCR** 相关配置可见官网 [文档](https://www.paddleocr.ai/main/version3.x/module_usage/text_recognition.html#_4)

#### 示例配置

```toml
[general]
retry_times = 3
backoff_factor = 2.0
timeout = 30.0
max_connections = 10
max_rps = 1.0
request_interval = 1.0
raw_data_dir = "./raw_data"
output_dir = "./downloads"
cache_dir = "./novel_cache"
workers = 2
skip_existing = true
storage_batch_size = 4

[general.debug]
save_html = false
log_level = "INFO"

[general.font_ocr]
decode_font = false
save_font_debug = false
batch_size = 32
```

---

### sites 配置

站点级设置 (如 `qidian`, `b520`, ...), **站点级会覆盖全局行为**; 每个站点配置位于 `[sites.<site>]` 下

#### 通用键

| 参数名             | 类型                                  | 默认值 | 说明                                   |
| ----------------- | ------------------------------------- | ------ | ------------------------------------- |
| `book_ids`        | array\<string\> 或 array\<table\>     | -      | 小说 ID 列表                           |
| `login_required`  | bool                                  | false  | 是否需要登录才能访问                    |
| `use_truncation`  | bool                                  | true   | 是否启用基于章节长度的截断以避免重复内容  |

> `use_truncation` 为 起点 设置, 详细可见 [站点支持文档](./4-supported-sites.md#book-id-说明)

#### `book_ids` 字段说明

`book_ids` 字段支持以下两种格式:

1) 简单列表

```toml
[sites.<site>]
book_ids = [
  "1010868264",
  "1020304050"
]
```

2) 结构化 (支持范围与忽略列表)

```toml
[sites.<site>]
login_required = true

[[sites.<site>.book_ids]]
book_id = "1030412702"
start_id = "833888839"
end_id = "921312343"
ignore_ids = ["1234563", "43212314"]

[[sites.<site>.book_ids]]
book_id = "1111111111"   # 其他字段可省略
```

**结构化字段说明**

| 字段名        | 类型           | 必需 | 说明                        |
| ------------ | -------------- | --- | --------------------------- |
| `book_id`    | string         | 是  | 小说的唯一标识 ID             |
| `start_id`   | string         | 否  | 起始章节 ID (含起)            |
| `end_id`     | string         | 否  | 结束章节 ID (含止)            |
| `ignore_ids` | `list[string]` | 否  | 需要跳过的章节 ID             |

#### 示例: 起点 (`qidian`)

**简单格式**

```toml
[sites.qidian]
book_ids = [
  "1010868264",
  "1012584111"
]
login_required = true
use_truncation = true
```

**结构化格式**

```toml
[sites.qidian]
login_required = true
use_truncation = true

[[sites.qidian.book_ids]]
book_id = "1010868264"
start_id = "434742822"
end_id = "528536599"
ignore_ids = ["507161874", "516065132"]

[[sites.qidian.book_ids]]
book_id = "1012584111"
```

---

### output 配置

控制导出格式, 文件命名与 EPUB 细节

#### 输出格式 `[output.formats]`

| 参数名          | 类型  | 默认值     | 说明                                       |
| -------------- | ----- | --------- | ------------------------------------------ |
| `make_txt`     | bool  | true      | 是否生成完整 TXT 文件                       |
| `make_epub`    | bool  | false     | 是否生成 EPUB 文件                          |
| `make_md`      | bool  | false     | 是否生成 Markdown 文件 (未实现)             |
| `make_pdf`     | bool  | false     | 是否生成 PDF 文件 (未实现)                  |

#### 命名规则 `[output.naming]`

| 参数名                         | 类型    | 默认值                         | 说明                                       |
| ----------------------------- | ------- | ----------------------------- | ------------------------------------------ |
| `append_timestamp`            | bool    | true                          | 输出文件名是否追加时间戳                     |
| `filename_template`           | string  | `"{title}_{author}"`          | 文件名模板                                  |

#### EPUB 选项 `[output.epub]`

| 参数名                         | 类型    | 默认值                         | 说明                                       |
| ----------------------------- | ------- | ----------------------------- | ------------------------------------------ |
| `include_cover`               | bool    | true                          | 是否包含封面                               |
| `include_picture`             | bool    | true                          | 是否下载并嵌入章节中的图片 (可能增加文件体积) |

#### 示例配置

```toml
[output.formats]
make_txt = true
make_epub = true
make_md = false
make_pdf = false

[output.naming]
append_timestamp = false
filename_template = "{title}_{author}"

[output.epub]
include_cover = true
include_picture = true
```

---

### cleaner 配置

控制标题/正文的正则移除与字面替换, 以及从外部文件加载规则

#### 主配置项

| 参数名              | 类型 | 默认值 | 说明                                       |
| ------------------ | ---- | ----- | ------------------------------------------ |
| `clean_text`       | bool | true  | 是否对章节文本做清理                         |
| `remove_invisible` | bool | true  | 是否移除 BOM 与零宽/不可见字符               |

#### 标题清理 `[cleaner.title]`

| 参数名              | 类型        | 默认值 | 说明                                  |
| ------------------ | ----------- | ------ | ------------------------------------ |
| `remove_patterns`  | string 数组 | `[]`   | 通过正则匹配, 移除标题中不需要的内容    |
| `replace`          | 键值对      | `{}`   | 每一项把 "源字符串" 替换成 "目标字符串" |

**外部加载** `[cleaner.title.external]`

  | 字段               | 类型   | 说明                                    |
  | ----------------- | ------ | --------------------------------------- |
  | `enabled`         | bool   | 是否启用外部文件                         |
  | `remove_patterns` | string | 指向 JSON 文件 (数组), 加载标题的正则删除模式列表 |
  | `replace`         | string | 指向 JSON 文件 (对象), 加载标题的字面替换映射     |

> 正文清理的结构与标题相同, 路径为 `[cleaner.content]` 与 `[cleaner.content.external]`

#### 示例配置

```toml
[cleaner]
clean_text = true
remove_invisible = true

[cleaner.title]
remove_patterns = [
  '【[^】]*?】',
  '[(（][^()（）]*?求票[^()（）]*?[)）]',
]

[cleaner.title.replace]
'：' = ':'

[cleaner.title.external]
enabled = true
remove_patterns = "path/to/title-remove.json"
replace         = "path/to/title-replace.json"

[cleaner.content]
remove_patterns = []

[cleaner.content.replace]
'li子' = '例子'
'pinbi词' = '屏蔽词'

[cleaner.content.external]
enabled = true
remove_patterns = "path/to/content-remove.json"
replace         = "path/to/content-replace.json"
```

> **规则合并说明**
>
> * `remove_patterns`: 按数组顺序应用正则删除。
> * `replace`: 对出现的键进行字面替换。
> * 若同时配置了本地与外部规则, 程序会加载并合并; **发生键冲突时外部文件优先**。
