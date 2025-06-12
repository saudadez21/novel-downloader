## `settings.toml` 配置说明

> **提示**: 可根据实际需求在 `settings.toml` 中增删字段, 未列出的配置项可参考源码注释或自行扩展。

### requests 配置

控制网络请求行为, 包括超时 / 重试 / 并发连接数等选项

| 参数名            | 类型    | 默认值          | 说明                                   |
|------------------|--------|---------------|--------------------------------------|
| `retry_times`      | int    | 3             | 请求失败重试次数                         |
| `backoff_factor`   | float  | 2.0           | 重试的退避因子 (每次重试等待时间将按倍数增加, 如 `2s`, `4s`, `8s`) |
| `timeout`          | float  | 30.0          | 页面加载超时时间 (秒)                    |
| `max_connections`  | int    | 10            | 最大并发连接数                           |
| `max_rps`           | int \| null | null    | 最大请求速率 (requests per second), 为空则不限制 |
| `headless`         | bool   | false         | 启动浏览器时是否使用无头模式 (不显示窗口)          |
| `disable_images`   | bool   | true          | 是否禁用图片加载 (可加速页面渲染)           |

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
verify_ssl = true
browser_type = "chromium"

# 可选项
headless = false               # 是否使用无头浏览器
disable_images = false         # 是否禁用图片加载
```

---

### general 配置

全局通用行为设置, 包括下载控制 / 目录结构 / 存储方式与调试选项等

#### 主配置项

| 参数名               | 类型    | 默认值              | 说明                                   |
|---------------------|--------|-------------------|--------------------------------------|
| `request_interval`   | float  | 2.0               | 同一本书各章节请求间隔 (秒)                   |
| `raw_data_dir`       | string | `"./raw_data"`    | 原始章节 JSON / DB 存放目录             |
| `output_dir`         | string | `"./downloads"`   | 最终输出文件存放目录                   |
| `cache_dir`          | string | `"./novel_cache"` | 本地缓存目录 (字体 / 图片等)       |
| `download_workers`   | int    | 2                 | 并发下载任务的协程数量                         |
| `parser_workers`     | int    | 2                 | 并发解析任务的协程数量                        |
| `skip_existing`      | bool   | true              | 下载时是否跳过本地已存在的章节文件            |
| `storage_backend`    | string | `"sqlite"`        | 章节存储方式, 可选值：`json`、`sqlite`   |
| `storage_batch_size` | int    | 30                | 使用 SQLite 时每批次提交的章节数 (提高写入性能) |

#### 调试选项 `[general.debug]`

| 参数名               | 类型    | 默认值              | 说明                                   |
|---------------------|--------|-------------------|--------------------------------------|
| `debug.save_html`    | bool   | false             | 是否保存抓取到的原始 HTML 到磁盘         |
| `debug.log_level`    | string | `"INFO"`          | 日志级别: DEBUG, INFO, WARNING, ERROR |

#### 字体/OCR 设置 `[general.font_ocr]`

用于支持混淆字体破解与文本识别的高级配置

| 参数名            | 类型         | 默认值     | 说明                                                   |
|------------------|--------------|------------|--------------------------------------------------------|
| `decode_font`     | bool         | false      | 是否尝试本地解码混淆字体                                |
| `use_freq`        | bool         | false      | 是否启用字符频率分析辅助识别                             |
| `ocr_version`     | string       | `"v2.0"`   | OCR 使用的模型版本: `v1.0` / `v2.0`                      |
| `use_ocr`         | bool         | true       | 是否使用 OCR 模型辅助识别字体加密                          |
| `use_vec`         | bool         | false      | 是否使用向量模型辅助识别文本                              |
| `save_font_debug` | bool         | false      | 是否保存字体调试数据                                     |
| `batch_size`      | int          | 32         | OCR 模型推理时的批处理大小                               |
| `gpu_mem`         | int          | 500        | CR 推理时可使用的 GPU 显存上限 (MB)                      |
| `gpu_id`          | int/null     | null       | 使用哪个 GPU, 若未指定则自动分配                         |
| `ocr_weight`      | float        | 0.5        | 最终结果中 OCR 部分的权重                                |
| `vec_weight`      | float        | 0.5        | 最终结果中向量识别部分的权重                             |

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
use_freq = false
ocr_version = "v2.0"
use_ocr = true
use_vec = false
save_font_debug = false
batch_size = 32
gpu_mem = 500
# gpu_id = 0
ocr_weight = 0.5
vec_weight = 0.5
```

---

### sites 配置

针对不同网站的专属配置, 通过站点名称区分 (如 `<site>` 可以是 `qidian`、`xxxxx` 等)

每个站点配置位于 `[sites.<site>]` 下:

| 参数名           | 类型             | 默认值        | 说明                                                           |
|------------------|------------------|---------------|----------------------------------------------------------------|
| `book_ids`        | array\<string\> 或 array\<table\>     | -             | 小说 ID 列表 (如 `1010868264`)                                 |
| `mode`            | string            | `"browser"`   | 请求方式: `browser` / `session` /                             |
| `login_required`  | bool              | false         | 是否需要登录才能访问                                           |

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
mode = "session"
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

| 字段名          | 类型            | 必需 | 说明               |
| ------------ | ------------- | -- | ---------------- |
| `book_id`    | string        | 是  | 小说的唯一标识 ID       |
| `start_id`   | string        | 否  | 起始章节 ID，从该章节开始下载 |
| `end_id`     | string        | 否  | 结束章节 ID，下载至该章节为止 |
| `ignore_ids` | `list[string]` | 否  | 要跳过的章节 ID 列表     |

#### 示例: 起点中文网配置

```toml
# 简单格式
[sites.qidian]
book_ids = [
  "1010868264",
  "1012584111"
]
mode = "session"
login_required = true
```

```toml
# 结构化格式
[sites.qidian]
mode = "session"
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

| 参数名                         | 类型     | 默认值                          | 说明                                       |
|-------------------------------|---------|-------------------------------|-------------------------------------------|
| `clean_text`                  | bool    | true                          | 是否对章节文本做清理                         |

#### 输出格式 `[output.formats]`

| 参数名                         | 类型     | 默认值                          | 说明                                       |
|-------------------------------|---------|-------------------------------|-------------------------------------------|
| `make_txt`                    | bool    | true                          | 是否生成完整 TXT 文件                       |
| `make_epub`                   | bool    | false                         | 是否生成 EPUB 文件                         |
| `make_md`                     | bool    | false                         | 是否生成 Markdown 文件 (未实现)             |
| `make_pdf`                    | bool    | false                         | 是否生成 PDF 文件 (未实现)                  |

#### 文件命名规则 `[output.naming]`

| 参数名                         | 类型     | 默认值                          | 说明                                       |
|-------------------------------|---------|-------------------------------|-------------------------------------------|
| `append_timestamp`            | bool    | true                          | 在输出文件名中追加时间戳                     |
| `filename_template`           | string  | `"{title}_{author}"`          | 输出文件名模板                              |

#### EPUB 选项 `[output.epub]`

| 参数名                         | 类型     | 默认值                          | 说明                                       |
|-------------------------------|---------|-------------------------------|-------------------------------------------|
| `include_cover`               | bool    | true                          | 是否在 EPUB 文件中包含封                    |
| `include_toc`                 | bool    | true                          | 是否自动生成章节目录                        |
| `include_picture`             | bool    | false                         | 是否下载并嵌入章节中的图片 (可能增加文件体积) |

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
include_toc = false
include_picture = false
```
