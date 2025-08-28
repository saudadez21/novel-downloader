## `settings.toml` 配置说明

> **提示**: 可根据实际需求在 `settings.toml` 中增删字段, 未列出的配置项可参考源码注释或自行扩展。

### general 配置

全局通用行为设置, 包括下载控制 / 目录结构 / 存储方式与调试选项等

#### 主配置项

| 参数名                | 类型    | 默认值             | 说明                                 |
| -------------------- | ------- | ----------------- | ------------------------------------ |
| `retry_times`        | int     | 3                 | 请求失败重试次数                         |
| `backoff_factor`     | float   | 2.0               | 重试的退避因子 (每次重试等待时间将按倍数增加, 如 `2s`, `4s`, `8s`) |
| `timeout`            | float   | 30.0              | 页面加载超时时间 (秒)                    |
| `max_connections`    | int     | 10                | 最大并发连接数                           |
| `max_rps`            | float   | 1000.0            | 最大请求速率 (requests per second)  |
| `request_interval`   | float   | 2.0               | 同一本书各章节请求间隔 (秒)                   |
| `raw_data_dir`       | string  | `"./raw_data"`    | 原始章节 JSON / DB 存放目录             |
| `output_dir`         | string  | `"./downloads"`   | 最终输出文件存放目录                   |
| `cache_dir`          | string  | `"./novel_cache"` | 本地缓存目录 (字体 / 图片等)       |
| `workers`            | int     | 2                 | 下载任务的协程数量                         |
| `skip_existing`      | bool    | true              | 下载时是否跳过本地已存在的章节文件            |
| `storage_backend`    | string  | `"sqlite"`        | 章节存储方式, 可选值：`json`、`sqlite`   |
| `storage_batch_size` | int     | 30                | 使用 SQLite 时每批次提交的章节数 (提高写入性能) |

> 注意: 部分站点在面对高频的访问频率时 (例如每秒 5 次), 可能因负载压力而返回 `503 Service Temporarily Unavailable` 错误。
>
> 建议根据具体站点的响应情况, 适当调低请求速率参数 (`max_rps`), 或稍后重新运行程序继续执行 (工具支持断点续爬, 已完成的数据不会被重复抓取)。

#### 示例配置

```toml
[requests]
retry_times = 3
backoff_factor = 2.0
timeout = 30.0
max_connections = 10
max_rps = 1.0                  # 每秒最多 1 次请求, 可用于限制站点压力
```

### 调试选项 `[general.debug]`

| 参数名                | 类型   | 默认值             | 说明                                 |
| -------------------- | ------ | ----------------- | ------------------------------------ |
| `debug.save_html`    | bool   | false             | 是否保存抓取到的原始 HTML 到磁盘        |
| `debug.log_level`    | string | `"INFO"`          | 日志级别: DEBUG, INFO, WARNING, ERROR |

### 字体/OCR 设置 `[general.font_ocr]`

用于支持混淆字体破解与文本识别的高级配置

| 参数名             | 类型         | 默认值      | 说明                                                   |
| ----------------- | ------------ | ---------- | ------------------------------------------------------ |
| `decode_font`     | bool         | false      | 是否尝试本地解码混淆字体                                 |
| `batch_size`      | int          | 32         | OCR 模型推理时的批处理大小                               |
| `save_font_debug` | bool         | false      | 是否保存字体调试数据                                     |

#### 示例配置

```toml
[general]
request_interval = 2.0
raw_data_dir = "./raw_data"
output_dir = "./downloads"
cache_dir = "./novel_cache"
download_workers = 2
parser_workers = 2
skip_existing = true
storage_backend = "sqlite"
storage_batch_size = 30

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

针对不同网站的专属配置, 通过站点名称区分 (如 `<site>` 可以是 `qidian`、`xxxxx` 等)

每个站点配置位于 `[sites.<site>]` 下:

| 参数名             | 类型                                  | 默认值 | 说明                                   |
| ----------------- | ------------------------------------- | ------ | ------------------------------------- |
| `book_ids`        | array\<string\> 或 array\<table\>     | -      | 小说 ID 列表 (如 `1010868264`)         |
| `login_required`  | bool                                  | false  | 是否需要登录才能访问                    |
| `use_truncation`  | bool                                  | true   | 是否启用基于章节长度的截断以避免重复内容  |

当需避免重复内容保存时, 请在 `settings.toml` 中将该站点 (例如 `[sites.qidian]`) 的 `use_truncation` 设置为 `true`。

#### `book_ids` 字段说明

`book_ids` 字段支持以下两种格式:

1. 简单 ID 列表

```toml
[sites.<site>]
book_ids = [
  "1010868264",
  "1020304050"
]
```

2. 结构化配置 (支持章节范围与忽略列表)

```toml
[sites.<site>]
login_required = true

[[sites.<site>.book_ids]]
book_id = "1030412702"
start_id = "833888839"
end_id = "921312343"
ignore_ids = ["1234563", "43212314"]

[[sites.<site>.book_ids]]
book_id = "1111111111"
# 其他字段可省略
```

每个结构化的 `book_id` 支持以下字段：

| 字段名        | 类型           | 必需 | 说明                        |
| ------------ | -------------- | --- | --------------------------- |
| `book_id`    | string         | 是  | 小说的唯一标识 ID             |
| `start_id`   | string         | 否  | 起始章节 ID, 从该章节开始下载  |
| `end_id`     | string         | 否  | 结束章节 ID, 下载至该章节为止  |
| `ignore_ids` | `list[string]` | 否  | 要跳过的章节 ID 列表          |

#### 示例: 起点中文网配置

```toml
# 简单格式
[sites.qidian]
book_ids = [
  "1010868264",
  "1012584111"
]
login_required = true
```

```toml
# 结构化格式
[sites.qidian]
login_required = true

[[sites.qidian.book_ids]]
book_id = "1010868264"
start_id = "434742822"
end_id = "528536599"
ignore_ids = ["507161874", "516065132"]

[[sites.qidian.book_ids]]
book_id = "1012584111"
```

### output 配置

控制输出格式 / 文件命名规则以及生成文件的内容设置

#### 主配置项

| 参数名                         | 类型    | 默认值                         | 说明                                       |
| ----------------------------- | ------- | ----------------------------- | ------------------------------------------ |
| `clean_text`                  | bool    | true                          | 是否对章节文本做清理                         |

#### 输出格式 `[output.formats]`

| 参数名                         | 类型    | 默认值                         | 说明                                       |
| ----------------------------- | ------- | ----------------------------- | ------------------------------------------ |
| `make_txt`                    | bool    | true                          | 是否生成完整 TXT 文件                       |
| `make_epub`                   | bool    | false                         | 是否生成 EPUB 文件                          |
| `make_md`                     | bool    | false                         | 是否生成 Markdown 文件 (未实现)             |
| `make_pdf`                    | bool    | false                         | 是否生成 PDF 文件 (未实现)                  |

#### 文件命名规则 `[output.naming]`

| 参数名                         | 类型    | 默认值                         | 说明                                       |
| ----------------------------- | ------- | ----------------------------- | ------------------------------------------ |
| `append_timestamp`            | bool    | true                          | 在输出文件名中追加时间戳                     |
| `filename_template`           | string  | `"{title}_{author}"`          | 输出文件名模板                              |

#### EPUB 选项 `[output.epub]`

| 参数名                         | 类型    | 默认值                         | 说明                                       |
| ----------------------------- | ------- | ----------------------------- | ------------------------------------------ |
| `include_cover`               | bool    | true                          | 是否在 EPUB 文件中包含封                    |
| `include_picture`             | bool    | true                          | 是否下载并嵌入章节中的图片 (可能增加文件体积) |

#### 示例配置

```toml
[output]
clean_text = true

[output.formats]
make_txt = true
make_epub = false
make_md = false
make_pdf = false

[output.naming]
append_timestamp = false
filename_template = "{title}_{author}"

[output.epub]
include_cover = true
include_picture = true
```

### cleaner 配置

控制文本清理器的行为, 包括对章节标题与内容的正则移除与字符串替换规则。

#### 主配置项

| 参数名              | 类型 | 默认值 | 说明                                       |
| ------------------ | ---- | ----- | ------------------------------------------ |
| `remove_invisible` | bool | true  | 是否移除 BOM 与零宽/不可见字符               |

#### 标题清理 `[cleaner.title]`

| 参数名              | 类型        | 默认值 | 说明                                  |
| ------------------ | ----------- | ------ | ------------------------------------ |
| `remove_patterns`  | string 数组 | `[]`   | 通过正则匹配, 移除标题中不需要的内容    |
| `replace`          | 键值对      | `{}`   | 每一项把 "源字符串" 替换成 "目标字符串" |

#### 外部加载 `[cleaner.title.external]`

  | 字段               | 类型   | 说明                                    |
  | ----------------- | ------ | --------------------------------------- |
  | `enabled`         | bool   | 是否启用外部文件                         |
  | `remove_patterns` | string | 指向 JSON 文件, 加载标题的正则删除模式列表 |
  | `replace`         | string | 指向 JSON 文件, 加载标题的字面替换映射     |

> `content` 同理, 对应的是正文规则

---

### 示例配置

```toml
[cleaner]
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

> **说明**:
>
> * `remove_patterns` 配置的是一系列正则, 用于删除所有匹配到的内容
> * `replace` 配置的是字面量替换, 对文本中出现的 "源" 一律换成 "目标"。
> * `*.external.remove_patterns` / `*.external.replace`: 如果配置了外部文件, 脚本会从对应 JSON 路径加载并合并配置, 映射冲突时外部优先。
