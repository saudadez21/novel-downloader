## `settings.toml` 配置说明

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
  - [plugins 配置](#plugins-配置)
    - [主配置项](#主配置项-1)
    - [示例配置](#示例配置-2)
  - [processors 配置](#processors-配置)
    - [内置处理器概览 (简要)](#内置处理器概览-简要)
      - [`cleaner`](#cleaner)
      - [`zh_convert`](#zh_convert)
      - [`corrector`](#corrector)
    - [各引擎支持与参数](#各引擎支持与参数)

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
| `request_interval`   | float   | 0.5               | **同一本书**章节请求的间隔 (秒)               |
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
| `device`          | str/None     | None       | 用于推理的设备, 例如: "cpu"、"gpu"、"npu"、"gpu:0"、"gpu:0,1"  |
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

### plugins 配置

插件系统相关设置; 用于开启/覆盖内置实现, 以及声明文本处理流水线 (`processors`)。

#### 主配置项

| 参数名                  | 类型           | 默认值               | 说明                                          |
| ---------------------- | -------------- | ------------------- | --------------------------------------------- |
| `enable_local_plugins` | bool           | false               | 是否启用本地插件目录 (扫描并加载本地插件)                          |
| `override_builtins`    | bool           | false               | 是否允许本地插件**覆盖**同名的内置实现 (如同名站点/处理器/导出器)           |
| `local_plugins_path`   | string         | `"./novel_plugins"` | 本地插件目录路径; 仅在 `enable_local_plugins = true` 时生效 |
| `processors`           | `array<table>` | `[]`                | 文本处理流水线的阶段列表 (**可选**; 留空或缺省则不执行任何文本处理)           |

> 说明: `processors` 为 **有序列表**, 按声明顺序执行。

> 更多插件编写说明 (自定义站点、处理器、导出器), 见: [插件系统文档](./plugins.md)

#### 示例配置

```toml
[plugins]
# 是否启用本地插件目录
enable_local_plugins = false
# 是否允许本地插件覆盖内置实现
override_builtins = false
# 本地插件路径 (可选)
local_plugins_path = "./novel_plugins"

[[plugins.processors]]
name = "cleaner"
overwrite = false
remove_invisible = true

title_removes = "path/to/title-remove.json"
title_replace = "path/to/title-replace.json"

content_removes = "path/to/content-remove.json"
content_replace = "path/to/content-replace.json"

[[plugins.processors]]
name = "zh_convert"
direction = "s2t"
```

---

### processors 配置

在导出前按顺序执行的文本处理阶段列表。

典型用途: **正则清理**、**繁简转换 (OpenCC)**、**文本纠错 (pycorrector)** 等。

> **所有处理器均为可选**; 未配置或列表为空时, 不执行文本处理。

#### 内置处理器概览 (简要)

##### `cleaner`

用于移除不可见字符、删除不需要的文本片段、进行字面替换 (可作用于标题与正文)。

| 参数名                | 类型   | 默认值   | 说明                                               |
| ------------------ | ---- | ----- | ------------------------------------------------ |
| `remove_invisible` | bool | true  | 移除常见不可见字符 (如零宽字符等)                       |
| `title_removes`    | str  | -     | **可选**; JSON 文件路径, 内容为**字符串数组** (正则), 逐条删除           |
| `title_replace`    | str  | -     | **可选**; JSON 文件路径, 内容为**字典** (`{"old": "new"}`) 逐条替换 |
| `content_removes`  | str  | -     | 同上, 作用于正文                                         |
| `content_replace`  | str  | -     | 同上, 作用于正文                                         |
| `overwrite`        | bool | false | 若同名阶段已存在, 是否强制重建                                  |

> `*_removes`: JSON 数组; `*_replace`: JSON 对象。

**示例**

假设配置中写入:

```toml
[[plugins.processors]]
name = "cleaner"
remove_invisible = true
title_removes = "title-remove.json"
content_replace = "content-replace.json"
```

则需要在相同目录下创建对应 JSON 文件:

**title-remove.json**

```json
[
  "\\[广告\\]",
  "\\(无弹窗小说网\\)",
  "PS：.*$"
]
```

**content-replace.json**

```json
{
  "请记住本书首发网址": "",
  "（本章完）": "",
  "li子": "例子",
  "pinbi词": "屏蔽词"
}
```

##### `zh_convert`

进行简繁体转换, 基于 **OpenCC**。

| 参数名           | 类型   | 默认值   | 说明            |
| --------------- | ------ | ------- | --------------- |
| `direction`     | str    | `t2s`   | 转换方向 (见下)  |
| `apply_title`   | bool   | true    | 是否作用于标题   |
| `apply_content` | bool   | true    | 是否作用于正文   |
| `apply_author`  | bool   | false   | 是否作用于作者名 |
| `apply_tags`    | bool   | false   | 是否作用于标签   |
| `overwrite`     | bool   | false   | 是否强制重建     |

**可选转换方向** (`direction`):

| 简写      | 含义                   |
| ------- | -------------------- |
| `hk2s`  | 繁体 (香港标准)  -> 简体        |
| `s2hk`  | 简体 -> 繁体 (香港标准)         |
| `s2t`   | 简体 -> 繁体              |
| `s2tw`  | 简体 -> 繁体 (台湾标准)         |
| `s2twp` | 简体 -> 繁体 (台湾标准，带词汇转换)   |
| `t2hk`  | 繁体 -> 繁体 (香港标准)         |
| `t2s`   | 繁体 -> 简体              |
| `t2tw`  | 繁体 -> 繁体 (台湾标准)         |
| `tw2s`  | 繁体 (台湾标准)  -> 简体        |
| `tw2sp` | 繁体 (台湾标准)  -> 简体 (带词汇转换)  |

> 更多方向及说明见:
> [OpenCC 官方文档](https://github.com/yichen0831/opencc-python?tab=readme-ov-file#conversions-%E8%BD%89%E6%8F%9B)
>
> 依赖: `opencc-python-reimplemented`。

##### `corrector`

中文文本纠错, 基于 [**pycorrector**](https://github.com/shibing624/pycorrector)。

可选择多种纠错引擎, 如 `kenlm`、`macbert`、`t5`、`ernie_csc`、`gpt`、`mucgec_bart` 等。

> 注意: 小说文本上纠错效果受模型影响较大, 通常不佳。

| 参数名            | 类型     | 默认值     | 说明              |
| ---------------- | -------- | --------- | --------------- |
| `engine`         | str      | `"kenlm"` | 纠错引擎类型          |
| `apply_title`    | bool     | true      | 是否作用于标题         |
| `apply_content`  | bool     | true      | 是否作用于正文         |
| `apply_author`   | bool     | false     | 是否作用于作者名        |
| `apply_tags`     | bool     | false     | 是否作用于标签         |
| `skip_if_len_le` | int|None | None      | 文本长度小于等于该值时跳过处理 |
| `overwrite`      | bool     | false     | 是否强制重建          |

> 依赖: `pycorrector` 及对应模型; 首次加载可能较慢。
>
> 各引擎的参数说明与官方文档参见下表。


#### 各引擎支持与参数

| 引擎 Key          | 说明                        | 文档链接                                                                                                                                       | 额外参数                                                                                                                                   |
| --------------- | ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------- |
| **kenlm**       | 基于统计语言模型的中文纠错             | [kenlm 模型（统计模型）](https://github.com/shibing624/pycorrector?tab=readme-ov-file#kenlm%E6%A8%A1%E5%9E%8B%E7%BB%9F%E8%AE%A1%E6%A8%A1%E5%9E%8B) | `language_model_path`, `custom_confusion_path_or_dict`, `proper_name_path`, `common_char_path`, `same_pinyin_path`, `same_stroke_path` |
| **macbert**     | 基于 Transformer 的拼写纠错模型    | [MacBERT 模型](https://github.com/shibing624/pycorrector?tab=readme-ov-file#macbert4csc%E6%A8%A1%E5%9E%8B)                                   | `model_name_or_path`                                                                                                                   |
| **t5**          | T5 架构的中文纠错模型              | [T5 模型](https://github.com/shibing624/pycorrector?tab=readme-ov-file#t5%E6%A8%A1%E5%9E%8B)                                                 | `model_name_or_path`                                                                                                                   |
| **ernie_csc**   | 基于 ERNIE 的中文纠错模型          | [ErnieCSC 模型](https://github.com/shibing624/pycorrector?tab=readme-ov-file#erniecsc%E6%A8%A1%E5%9E%8B)                                     | `model_name_or_path`                                                                                                                   |
| **gpt**         | 基于 ChatGLM / Qwen 等大模型的纠错 | [GPT 模型](https://github.com/shibing624/pycorrector?tab=readme-ov-file#gpt%E6%A8%A1%E5%9E%8B)                                               | `model_name_or_path`, `model_type`, `peft_name`                                                                                        |
| **mucgec_bart** | Bart 架构的中文纠错模型            | [Bart / MuCGEC Bart 模型](https://github.com/shibing624/pycorrector?tab=readme-ov-file#bart%E6%A8%A1%E5%9E%8B)                               | `model_name_or_path`                                                                                                                   |
