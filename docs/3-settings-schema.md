## `settings.toml` 配置说明

### 目录

- [`settings.toml` 配置说明](#settingstoml-配置说明)
  - [目录](#目录)
  - [general 配置](#general-配置)
    - [主配置项](#主配置项)
    - [parser 子节 `[general.parser]`](#parser-子节-generalparser)
    - [output 子节 `[general.output]`](#output-子节-generaloutput)
    - [调试子节 `[general.debug]`](#调试子节-generaldebug)
    - [示例配置](#示例配置)
  - [sites 配置](#sites-配置)
    - [通用键](#通用键)
    - [`book_ids` 字段说明](#book_ids-字段说明)
    - [示例: 起点 (`qidian`)](#示例-起点-qidian)
  - [plugins 配置](#plugins-配置)
    - [主配置项](#主配置项-1)
    - [示例配置](#示例配置-1)
  - [processors 配置](#processors-配置)
    - [内置处理器概览 (简要)](#内置处理器概览-简要)
      - [`cleaner`](#cleaner)
      - [`zh_convert`](#zh_convert)
      - [`translator.google`](#translatorgoogle)
      - [`translator.edge`](#translatoredge)
      - [`translator.youdao`](#translatoryoudao)
      - [`corrector`](#corrector)

### general 配置

全局运行时设置, 面向下载 / 并发 / 速率限制 / 目录与存储的通用开关

#### 主配置项

| 参数名                | 类型    | 默认值             | 说明                                       |
| -------------------- | ------- | ----------------- | ------------------------------------------ |
| `backend`            | `str`   | `"aiohttp"`       | 全局 HTTP 请求后端, 可选 `"aiohttp"`, `"httpx"`, `"curl_cffi"` |
| `retry_times`        | int     | 3                 | 请求失败重试次数                             |
| `backoff_factor`     | float   | 2.0               | 重试的退避因子 (每次重试等待时间将按倍数增加, 如 `2s`, `4s`, `8s`) |
| `timeout`            | float   | 30.0              | 单次请求超时 (秒)                            |
| `max_connections`    | int     | 10                | 最大并发连接数                               |
| `max_rps`            | float   | 1000.0            | 全局 RPS 上限 (requests per second)         |
| `request_interval`   | float   | 0.5               | **同一本书**章节请求的间隔 (秒)               |
| `raw_data_dir`       | string  | `"./raw_data"`    | 书籍数据存放目录                             |
| `output_dir`         | string  | `"./downloads"`   | 最终导出文件目录                             |
| `cache_dir`          | string  | `"./novel_cache"` | 本地缓存目录 (字体 / 图片等)                  |
| `workers`            | int     | 4                 | 下载任务协程数量                             |
| `cache_book_info`    | bool    | `true`            | 是否启用 book_info 缓存                      |
| `cache_chapter`      | bool    | `true`            | 是否启用章节缓存                             |
| `fetch_inaccessible` | bool    | `false`           | 是否尝试获取未订阅章节                        |
| `http2`              | `bool`  | `true`            | 仅对 `httpx` 生效, 启用 HTTP/2 支持           |
| `impersonate`        | `str \| None` | `None`      | 仅对 `curl_cffi` 生效, 启用浏览器指纹仿真模式  |
| `storage_batch_size` | int     | 1                 | `sqlite` 每批提交的章节数 (提高写入性能)       |

**站点压力与 503**

部分站点对高频访问敏感 (例如 >= 5 RPS), 可能返回 `503 Service Temporarily Unavailable`。

建议适当**降低** `max_rps` 或**增大** `request_interval`; 工具支持断点续爬, 已完成的数据不会重复抓取。

**HTTP 请求后端**

程序支持可插拔式 HTTP 后端, 可在 `[general]` 中通过 `backend` 参数进行切换:

| 后端名称     | 说明                                                | 依赖安装                    |
| ----------- | --------------------------------------------------- | -------------------------- |
| `aiohttp`   | 默认后端, 基于 `aiohttp` 的异步 HTTP 客户端           | -                          |
| `httpx`     | 现代异步 HTTP 客户端, 支持 HTTP/1.1 与 HTTP/2         | `pip install httpx[http2]` |
| `curl_cffi` | 基于 `libcurl` 的实现, 支持浏览器仿真 (`impersonate`) | `pip install curl_cffi`    |

> **扩展参数**
>
> * `http2`: 仅对 `httpx` 生效, 启用 HTTP/2 支持 (默认 `true`)
> * `impersonate`: 仅对 `curl_cffi` 生效, 启用浏览器指纹仿真, 可设为 `"chrome136"`, `"chrome"` 等
>
> 更多信息请参考各项目文档:
>
> * [`httpx`](https://github.com/encode/httpx)
> * [`curl_cffi`](https://github.com/lexiforest/curl_cffi)

**兼容性与 Cloudflare 行为说明**

由于各 HTTP 客户端在协议实现与 TLS 指纹上的差异, 部分站点在使用默认的 `aiohttp` 后端时, 可能会触发 **Cloudflare 反爬虫或访问验证机制**, 从而导致连接被拦截或返回 `403`/`5xx` 状态码。

若遇到此类情况, 建议切换至以下后端之一:

* **`httpx` (启用 `http2 = true`)**: 通过 HTTP/2 可获得更接近现代浏览器的网络特征, 对部分启用 Cloudflare 的站点有更好的兼容性
* **`curl_cffi` (启用 `impersonate`)**: 通过模拟浏览器 TLS 指纹和请求头, 可显著提升被 Cloudflare 或其他 WAF 拦截的站点的访问成功率

需要注意的是, 不同站点的后端表现可能存在差异。例如:

* 某些站点仅在 `aiohttp` 或 `httpx` 的 HTTP/1.1 模式下可正常访问, 而在启用 `http2 = true` 时反而会触发 Cloudflare 或导致连接失败
* 另一些站点则恰好相反, 只有在启用 HTTP/2 或使用 `curl_cffi` 的浏览器仿真模式下才能成功建立连接

因此, 在遇到访问异常 (如 403、TLS 握手失败、Cloudflare 验证循环等) 时, 建议根据具体站点情况灵活调整后端和相关参数。

#### parser 子节 `[general.parser]`

该配置用于处理 **混淆字体解码** 与 **图片章节 OCR 识别**, 并控制图片章节的 **去水印** 与 **切割方式**。

| 参数名             | 类型          | 默认值      | 说明                                                        |
| ------------------ | ------------ | ---------- | ----------------------------------------------------------- |
| `enable_ocr`       | bool         | false      | 是否启用本地 OCR, 用于识别混淆字体或图片章节文本                |
| `batch_size`       | int          | 32         | OCR 模型推理时的批处理大小                                    |
| `remove_watermark` | bool         | false      | 是否尝试对图片章节进行去水印 (部分站点支持)                     |
| `cut_mode`         | string       | `"none"`   | 图片章节切割模式: `none` (整图) / `paragraph` (按段落) / `page` (按页) |
| `model_name`       | str/None     | None       | OCR 模型名称, 如果设置为 `None`, 则使用 `PP-OCRv5_server_rec`  |
| `model_dir`        | str/None     | None       | OCR 模型存储路径                                              |
| `input_shape`      | tuple/None   | None       | OCR 模型输入图像尺寸, 格式为 (C, H, W)                         |
| `device`           | str/None     | None       | 用于推理的设备, 例如: "cpu"、"gpu"、"npu"、"gpu:0"、"gpu:0,1"  |
| `cpu_threads`      | int          | 10         | 在 CPU 上推理时使用的线程数量                                  |
| `enable_hpi`       | bool         | false      | 是否启用高性能推理                                             |

功能说明:

* **混淆字体章节**
  * 若未开启解析或解析失败, 程序将在导出 EPUB/HTML 时自动嵌入对应字体文件, 确保显示正常

* **图片章节切割**
  * 当未开启 OCR 或识别失败时, 图片章节会根据 `cut_mode` 进行切割
  * 由于整图经常过长且不适合在 EPUB 阅读器中显示, 建议使用 `paragraph` / `page` 模式以获得更好的阅读体验。
  * 需要注意的是, `paragraph` 模式可能会因产生大量小图而显著增加文件体积, 例如约 1000 个章节可能膨胀至 1.5 GB

依赖说明:

若 `cut_mode` 为 `paragraph` / `page` 或启用了 `enable_ocr`, 需安装额外的图像处理依赖

```bash
pip install novel-downloader[image-utils]
```

OCR 功能依赖 `PaddleOCR` 及其模型, 请参考安装指南:

* [安装说明](./1-installation.md)

`PaddleOCR` 配置参考官方文档:

* [PaddleOCR 文档](https://www.paddleocr.ai/main/version3.x/module_usage/text_recognition.html#_4)

#### output 子节 `[general.output]`

控制导出格式, 文件命名与 EPUB 细节

| 参数名                        | 类型         | 默认值                | 说明                                       |
| ----------------------------- | ----------- | --------------------- | ------------------------------------------ |
| `formats`                     | `list[str]` | `[]`                  | 输出格式                                    |
| `append_timestamp`            | bool        | true                  | 输出文件名是否追加时间戳                     |
| `filename_template`           | string      | `"{title}_{author}"`  | 文件名模板                                  |
| `include_picture`             | bool        | true                  | 是否下载并嵌入章节中的图片 (可能增加文件体积) |

#### 调试子节 `[general.debug]`

| 参数名                | 类型   | 默认值             | 说明                                 |
| -------------------- | ------ | ----------------- | ------------------------------------ |
| `debug.save_html`    | bool   | false             | 是否保存抓取到的原始 HTML 到磁盘        |
| `debug.log_level`    | string | `"INFO"`          | 日志级别: DEBUG, INFO, WARNING, ERROR |

#### 示例配置

```toml
[general]
retry_times = 3
backoff_factor = 2.0
timeout = 30.0
max_connections = 10
max_rps = 1.0
request_interval = 0.5
raw_data_dir = "./raw_data"
output_dir = "./downloads"
cache_dir = "./novel_cache"
workers = 4
cache_book_info = true
cache_chapter = true
storage_batch_size = 4

[general.output]
formats = [
    "txt",
    "epub",
    "html",
]
include_picture = true

[general.parser]
enable_ocr = false
batch_size = 32

remove_watermark = true
cut_mode = "paragraph"

model_name = "PP-OCRv5_mobile_rec"
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
  "(本章完)": "",
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

##### `translator.google`

| 参数名           | 类型   | 默认值   |
| --------------- | ------ | ------- |
| `source`        | str    | `auto`  |
| `target`        | str    | `zh-CN` |
| `sleep`         | float  | 2.0     |

<details>
<summary>支持语言列表 (点击展开)</summary>

| 语言名称              | 代码         |
| ----------------- | ---------- |
| 阿布哈兹语             | `ab`       |
| 亚齐语               | `ace`      |
| 阿乔利语              | `ach`      |
| 阿法尔语              | `aa`       |
| 南非荷兰语             | `af`       |
| 阿尔巴尼亚语            | `sq`       |
| 阿卢尔语              | `alz`      |
| 阿姆哈拉语             | `am`       |
| 阿拉伯语              | `ar`       |
| 亚美尼亚语             | `hy`       |
| 阿萨姆语              | `as`       |
| 阿瓦尔语              | `av`       |
| 阿瓦德语              | `awa`      |
| 艾马拉语              | `ay`       |
| 阿塞拜疆语             | `az`       |
| 巴厘语               | `ban`      |
| 俾路支语              | `bal`      |
| 班巴拉语              | `bm`       |
| 巴乌莱语              | `bci`      |
| 巴什基尔语             | `ba`       |
| 巴斯克语              | `eu`       |
| 巴塔克卡罗语            | `btx`      |
| 巴塔克西马隆贡语          | `bts`      |
| 巴塔克托巴语            | `bbc`      |
| 白俄罗斯语             | `be`       |
| 本巴语               | `bem`      |
| 孟加拉语              | `bn`       |
| 雅加达方言(Betawi)     | `bew`      |
| 博杰普尔语             | `bho`      |
| 比科尔语              | `bik`      |
| 波斯尼亚语             | `bs`       |
| 布列塔尼语             | `br`       |
| 保加利亚语             | `bg`       |
| 布里亚特语             | `bua`      |
| 粤语                | `yue`      |
| 加泰罗尼亚语            | `ca`       |
| 宿务语               | `ceb`      |
| 查莫罗语              | `ch`       |
| 车臣语               | `ce`       |
| 齐切瓦语              | `ny`       |
| 中文(简体)            | `zh-CN`    |
| 中文(繁体)            | `zh-TW`    |
| 楚克语               | `chk`      |
| 楚瓦什语              | `cv`       |
| 科西嘉语              | `co`       |
| 克里米亚鞑靼语           | `crh`      |
| 克罗地亚语             | `hr`       |
| 捷克语               | `cs`       |
| 丹麦语               | `da`       |
| 达里语               | `fa-AF`    |
| 迪维希语              | `dv`       |
| 丁卡语               | `din`      |
| 多格拉语              | `doi`      |
| 冬贝语               | `dov`      |
| 荷兰语               | `nl`       |
| 朱拉语(Dyula)        | `dyu`      |
| 宗卡语               | `dz`       |
| 英语                | `en`       |
| 世界语               | `eo`       |
| 爱沙尼亚语             | `et`       |
| 埃维语               | `ee`       |
| 法罗语               | `fo`       |
| 斐济语               | `fj`       |
| 菲律宾语              | `tl`       |
| 芬兰语               | `fi`       |
| 丰语(Fon)           | `fon`      |
| 法语                | `fr`       |
| 弗里斯兰语             | `fy`       |
| 弗留利语              | `fur`      |
| 富拉语               | `ff`       |
| 加语(Ga)            | `gaa`      |
| 加利西亚语             | `gl`       |
| 格鲁吉亚语             | `ka`       |
| 德语                | `de`       |
| 希腊语               | `el`       |
| 瓜拉尼语              | `gn`       |
| 古吉拉特语             | `gu`       |
| 海地克里奥尔语           | `ht`       |
| 哈卡钦语              | `cnh`      |
| 豪萨语               | `ha`       |
| 夏威夷语              | `haw`      |
| 希伯来语              | `iw`       |
| 希利盖农语             | `hil`      |
| 印地语               | `hi`       |
| 苗族语               | `hmn`      |
| 匈牙利语              | `hu`       |
| 洪斯里克语             | `hrx`      |
| 伊班语               | `iba`      |
| 冰岛语               | `is`       |
| 伊博语               | `ig`       |
| 伊洛卡诺语             | `ilo`      |
| 印度尼西亚语            | `id`       |
| 爱尔兰语              | `ga`       |
| 意大利语              | `it`       |
| 牙买加土语             | `jam`      |
| 日语                | `ja`       |
| 爪哇语               | `jw`       |
| 景颇语               | `kac`      |
| 格陵兰语              | `kl`       |
| 卡纳达语              | `kn`       |
| 卡努里语              | `kr`       |
| 卡潘潘庞语             | `pam`      |
| 哈萨克语              | `kk`       |
| 卡西语               | `kha`      |
| 高棉语               | `km`       |
| 基加语               | `cgg`      |
| 基孔戈语              | `kg`       |
| 卢旺达语              | `rw`       |
| 基图巴语              | `ktu`      |
| 科克博罗克语            | `trp`      |
| 科米语               | `kv`       |
| 孔卡尼语              | `gom`      |
| 韩语                | `ko`       |
| 克里奥尔语(塞拉利昂)       | `kri`      |
| 库尔德语(库尔曼吉)        | `ku`       |
| 库尔德语(索拉尼)         | `ckb`      |
| 吉尔吉斯语             | `ky`       |
| 老挝语               | `lo`       |
| 拉脱维亚方言(Latgalian) | `ltg`      |
| 拉丁语               | `la`       |
| 拉脱维亚语             | `lv`       |
| 利古里亚语             | `lij`      |
| 林堡语               | `li`       |
| 林加拉语              | `ln`       |
| 立陶宛语              | `lt`       |
| 伦巴第语              | `lmo`      |
| 卢干达语              | `lg`       |
| 卢奥语               | `luo`      |
| 卢森堡语              | `lb`       |
| 马其顿语              | `mk`       |
| 马都拉语              | `mad`      |
| 迈蒂利语              | `mai`      |
| 望加锡语              | `mak`      |
| 马尔加什语             | `mg`       |
| 马来语               | `ms`       |
| 马来语(爪夷文)          | `ms-Arab`  |
| 马拉雅拉姆语            | `ml`       |
| 马耳他语              | `mt`       |
| 马姆语               | `mam`      |
| 曼岛语               | `gv`       |
| 毛利语               | `mi`       |
| 马拉地语              | `mr`       |
| 马绍尔语              | `mh`       |
| 马尔瓦里语             | `mwr`      |
| 毛里求斯克里奥尔语         | `mfe`      |
| 马里语(东部)           | `chm`      |
| 曼尼普尔语(梅泰文)        | `mni-Mtei` |
| 米南加保语             | `min`      |
| 米佐语               | `lus`      |
| 蒙古语               | `mn`       |
| 缅甸语               | `my`       |
| 纳瓦特尔语(东瓦斯特卡)      | `nhe`      |
| 恩道语               | `ndc-ZW`   |
| 南恩德贝莱语            | `nr`       |
| 尼瓦尔语              | `new`      |
| 尼泊尔语              | `ne`       |
| 恩科语               | `bm-Nkoo`  |
| 挪威语               | `no`       |
| 努埃尔语              | `nus`      |
| 奥克语               | `oc`       |
| 奥里亚语              | `or`       |
| 奥罗莫语              | `om`       |
| 奥塞梯语              | `os`       |
| 邦阿西楠语             | `pag`      |
| 帕皮阿门托语            | `pap`      |
| 普什图语              | `ps`       |
| 波斯语               | `fa`       |
| 波兰语               | `pl`       |
| 葡萄牙语(巴西)          | `pt`       |
| 葡萄牙语(葡萄牙)         | `pt-PT`    |
| 旁遮普语(果鲁穆奇文)       | `pa`       |
| 旁遮普语(沙姆奇文)        | `pa-Arab`  |
| 克丘亚语              | `qu`       |
| 凯克其语              | `kek`      |
| 罗姆语               | `rom`      |
| 罗马尼亚语             | `ro`       |
| 伦迪语               | `rn`       |
| 俄语                | `ru`       |
| 萨米语(北部)           | `se`       |
| 萨摩亚语              | `sm`       |
| 桑戈语               | `sg`       |
| 梵语                | `sa`       |
| 桑塔利语              | `sat-Latn` |
| 苏格兰盖尔语            | `gd`       |
| 北索托语              | `nso`      |
| 塞尔维亚语             | `sr`       |
| 塞索托语              | `st`       |
| 塞舌尔克里奥尔语          | `crs`      |
| 掸语                | `shn`      |
| 修纳语               | `sn`       |
| 西西里语              | `scn`      |
| 西里西亚语             | `szl`      |
| 信德语               | `sd`       |
| 僧伽罗语              | `si`       |
| 斯洛伐克语             | `sk`       |
| 斯洛文尼亚语            | `sl`       |
| 索马里语              | `so`       |
| 西班牙语              | `es`       |
| 巽他语               | `su`       |
| 苏苏语               | `sus`      |
| 斯瓦希里语             | `sw`       |
| 斯瓦蒂语              | `ss`       |
| 瑞典语               | `sv`       |
| 塔希提语              | `ty`       |
| 塔吉克语              | `tg`       |
| 柏柏尔语(拉丁)          | `ber-Latn` |
| 柏柏尔语(提非纳文)        | `ber`      |
| 泰米尔语              | `ta`       |
| 鞑靼语               | `tt`       |
| 泰卢固语              | `te`       |
| 德顿语               | `tet`      |
| 泰语                | `th`       |
| 藏语                | `bo`       |
| 提格利尼亚语            | `ti`       |
| 提夫语               | `tiv`      |
| 巴布亚皮钦语            | `tpi`      |
| 汤加语               | `to`       |
| 聪加语               | `ts`       |
| 茨瓦纳语              | `tn`       |
| 图鲁语               | `tcy`      |
| 通布卡语              | `tum`      |
| 土耳其语              | `tr`       |
| 土库曼语              | `tk`       |
| 图瓦语               | `tyv`      |
| 特威语               | `ak`       |
| 乌德穆尔特语            | `udm`      |
| 乌克兰语              | `uk`       |
| 乌尔都语              | `ur`       |
| 维吾尔语              | `ug`       |
| 乌兹别克语             | `uz`       |
| 文达语               | `ve`       |
| 威尼斯语              | `vec`      |
| 越南语               | `vi`       |
| 瓦莱语(Waray)        | `war`      |
| 威尔士语              | `cy`       |
| 沃洛夫语              | `wo`       |
| 科萨语               | `xh`       |
| 雅库特语              | `sah`      |
| 意第绪语              | `yi`       |
| 约鲁巴语              | `yo`       |
| 尤卡坦玛雅语            | `yua`      |
| 萨波特克语             | `zap`      |
| 祖鲁语               | `zu`       |

</details>

##### `translator.edge`

| 参数名           | 类型   | 默认值   |
| --------------- | ------ | ------- |
| `source`        | str    | `auto`  |
| `target`        | str    | `zh-Hans` |
| `sleep`         | float  | 1.0     |

<details>
<summary>支持语言列表 (点击展开)</summary>

| 语言名称        | 代码         |
| ----------- | ---------- |
| 南非荷兰语       | `af`       |
| 阿尔巴尼亚语      | `sq`       |
| 阿姆哈拉语       | `am`       |
| 阿拉伯语        | `ar`       |
| 亚美尼亚语       | `hy`       |
| 阿萨姆语        | `as`       |
| 阿塞拜疆语(拉丁)   | `az`       |
| 孟加拉语        | `bn`       |
| 巴什基尔语       | `ba`       |
| 巴斯克语        | `eu`       |
| 波斯尼亚语(拉丁)   | `bs`       |
| 保加利亚语       | `bg`       |
| 粤语(繁体)      | `yue`      |
| 加泰罗尼亚语      | `ca`       |
| 中文(文言文)     | `lzh`      |
| 中文(简体)      | `zh-Hans`  |
| 中文(繁体)      | `zh-Hant`  |
| 克罗地亚语       | `hr`       |
| 捷克语         | `cs`       |
| 丹麦语         | `da`       |
| 达里语         | `prs`      |
| 迪维希语        | `dv`       |
| 荷兰语         | `nl`       |
| 英语          | `en`       |
| 爱沙尼亚语       | `et`       |
| 法罗语         | `fo`       |
| 斐济语         | `fj`       |
| 菲律宾语        | `fil`      |
| 芬兰语         | `fi`       |
| 法语          | `fr`       |
| 法语(加拿大)     | `fr-ca`    |
| 加利西亚语       | `gl`       |
| 格鲁吉亚语       | `ka`       |
| 德语          | `de`       |
| 希腊语         | `el`       |
| 古吉拉特语       | `gu`       |
| 海地克里奥尔语     | `ht`       |
| 希伯来语        | `he`       |
| 印地语         | `hi`       |
| 苗族语(拉丁)     | `mww`      |
| 匈牙利语        | `hu`       |
| 冰岛语         | `is`       |
| 印度尼西亚语      | `id`       |
| 伊努因纳克顿语     | `ikt`      |
| 因纽特语        | `iu`       |
| 因纽特语(拉丁)    | `iu-Latn`  |
| 爱尔兰语        | `ga`       |
| 意大利语        | `it`       |
| 日语          | `ja`       |
| 卡纳达语        | `kn`       |
| 哈萨克语        | `kk`       |
| 高棉语         | `km`       |
| 克林贡语        | `tlh-Latn` |
| 克林贡语(plqaD) | `tlh-Piqd` |
| 韩语          | `ko`       |
| 库尔德语(中部)    | `ku`       |
| 库尔德语(北部)    | `kmr`      |
| 吉尔吉斯语(西里尔)  | `ky`       |
| 老挝语         | `lo`       |
| 拉脱维亚语       | `lv`       |
| 立陶宛语        | `lt`       |
| 马其顿语        | `mk`       |
| 马尔加什语       | `mg`       |
| 马来语(拉丁)     | `ms`       |
| 马拉雅拉姆语      | `ml`       |
| 马耳他语        | `mt`       |
| 毛利语         | `mi`       |
| 马拉地语        | `mr`       |
| 蒙古语(西里尔)    | `mn-Cyrl`  |
| 蒙古语(传统)     | `mn-Mong`  |
| 缅甸语         | `my`       |
| 尼泊尔语        | `ne`       |
| 挪威语         | `nb`       |
| 奥里亚语        | `or`       |
| 普什图语        | `ps`       |
| 波斯语         | `fa`       |
| 波兰语         | `pl`       |
| 葡萄牙语(巴西)    | `pt`       |
| 葡萄牙语(葡萄牙)   | `pt-pt`    |
| 旁遮普语        | `pa`       |
| 克雷塔罗奥托米语    | `otq`      |
| 罗马尼亚语       | `ro`       |
| 俄语          | `ru`       |
| 萨摩亚语(拉丁)    | `sm`       |
| 塞尔维亚语(西里尔)  | `sr-Cyrl`  |
| 塞尔维亚语(拉丁)   | `sr-Latn`  |
| 斯洛伐克语       | `sk`       |
| 斯洛文尼亚语      | `sl`       |
| 索马里语(阿拉伯)   | `so`       |
| 西班牙语        | `es`       |
| 斯瓦希里语(拉丁)   | `sw`       |
| 瑞典语         | `sv`       |
| 塔希提语        | `ty`       |
| 泰米尔语        | `ta`       |
| 鞑靼语(拉丁)     | `tt`       |
| 泰卢固语        | `te`       |
| 泰语          | `th`       |
| 藏语          | `bo`       |
| 提格利尼亚语      | `ti`       |
| 汤加语         | `to`       |
| 土耳其语        | `tr`       |
| 土库曼语(拉丁)    | `tk`       |
| 乌克兰语        | `uk`       |
| 上索布语        | `hsb`      |
| 乌尔都语        | `ur`       |
| 维吾尔语(阿拉伯)   | `ug`       |
| 乌兹别克语(拉丁)   | `uz`       |
| 越南语         | `vi`       |
| 威尔士语        | `cy`       |
| 尤卡坦玛雅语      | `yua`      |
| 祖鲁语         | `zu`       |

</details>

##### `translator.youdao`

| 参数名           | 类型   | 默认值   |
| --------------- | ------ | ------- |
| `source`        | str    | `auto`  |
| `target`        | str    | `zh-CHS` |
| `sleep`         | float  | 1.0     |

<details>
<summary>支持语言列表 (点击展开)</summary>

| 语言名称       | 代码        |
| ------------- | ----------- |
| 自动识别       | `auto`     |
| 阿尔巴尼亚语    | `sq`       |
| 爱尔兰语       | `ga`      |
| 爱沙尼亚语      | `et`      |
| 阿拉伯语       | `ar`      |
| 阿姆哈拉语      | `am`      |
| 阿塞拜疆语      | `az`      |
| 白俄罗斯语      | `be`      |
| 保加利亚语      | `bg`      |
| 巴斯克语       | `eu`      |
| 冰岛语        | `is`      |
| 波兰语        | `pl`      |
| 波斯尼亚语(拉丁语) | `bs-Latn` |
| 波斯语        | `fa`      |
| 丹麦语        | `da`      |
| 德语         | `de`      |
| 俄语         | `ru`      |
| 法语         | `fr`      |
| 菲律宾语       | `tl`      |
| 芬兰语        | `fi`      |
| 弗里斯兰语      | `fy`      |
| 高棉语        | `km`      |
| 格鲁吉亚语      | `ka`      |
| 古吉拉特语      | `gu`      |
| 海地语        | `ht`      |
| 韩语         | `ko`      |
| 豪萨语        | `ha`      |
| 哈萨克语       | `kk`      |
| 荷兰语        | `nl`      |
| 加利西亚语      | `gl`      |
| 加泰罗尼亚语     | `ca`      |
| 捷克语        | `cs`      |
| 吉尔吉斯斯坦语    | `ky`      |
| 卡纳达语       | `kn`      |
| 克林贡语       | `tlh`     |
| 克罗地亚语      | `hr`      |
| 克洛塔罗乙巳语    | `otq`     |
| 科西嘉语       | `co`      |
| 库尔德语       | `ku`      |
| 拉丁语        | `la`      |
| 老挝语        | `lo`      |
| 拉脱维亚语      | `lv`      |
| 立陶宛语       | `lt`      |
| 罗马尼亚语      | `ro`      |
| 卢森堡语       | `lb`      |
| 马尔加什语      | `mg`      |
| 马耳他语       | `mt`      |
| 马拉地语       | `mr`      |
| 马来语        | `ms`      |
| 马拉雅拉姆语     | `ml`      |
| 毛利语        | `mi`      |
| 马其顿语       | `mk`      |
| 蒙古语        | `mn`      |
| 孟加拉语       | `bn`      |
| 缅甸语        | `my`      |
| 苗族昂山土语     | `mww`     |
| 苗族语        | `hmn`     |
| 南非科萨语      | `xh`      |
| 南非祖鲁语      | `zu`      |
| 尼泊尔语       | `ne`      |
| 挪威语        | `no`      |
| 旁遮普语       | `pa`      |
| 普什图语       | `ps`      |
| 葡萄牙语       | `pt`      |
| 齐切瓦语       | `ny`      |
| 日语         | `ja`      |
| 瑞典语        | `sv`      |
| 塞尔维亚语(拉丁语) | `sr-Latn` |
| 塞尔维亚语(西里尔) | `sr-Cyrl` |
| 塞索托语       | `st`      |
| 萨摩亚语       | `sm`      |
| 僧伽罗语       | `si`      |
| 世界语        | `eo`      |
| 斯洛伐克语      | `sk`      |
| 斯洛文尼亚语     | `sl`      |
| 斯瓦希里语      | `sw`      |
| 苏格兰盖尔语     | `gd`      |
| 索马里语       | `so`      |
| 宿务语        | `ceb`     |
| 泰卢固语       | `te`      |
| 泰米尔语       | `ta`      |
| 泰语         | `th`      |
| 塔吉克语       | `tg`      |
| 土耳其语       | `tr`      |
| 威尔士语       | `cy`      |
| 文言文        | `zh-lzh`  |
| 乌尔都语       | `ur`      |
| 乌克兰语       | `uk`      |
| 乌兹别克语      | `uz`      |
| 夏威夷语       | `haw`     |
| 西班牙语       | `es`      |
| 希伯来语       | `he`      |
| 希腊语        | `el`      |
| 信德语        | `sd`      |
| 匈牙利语       | `hu`      |
| 修纳语        | `sn`      |
| 亚美尼亚语      | `hy`      |
| 伊博语        | `ig`      |
| 意大利语       | `it`      |
| 意第绪语       | `yi`      |
| 印地语        | `hi`      |
| 印度尼西亚语     | `id`      |
| 英语         | `en`      |
| 印尼巽他语      | `su`      |
| 印尼爪哇语      | `jw`      |
| 尤卡坦玛雅语     | `yua`     |
| 约鲁巴语       | `yo`      |
| 越南语        | `vi`      |
| 中文         | `zh-CHS`  |
| 中文(繁体)     | `zh-CHT`  |

</details>

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

**各引擎支持与参数**

| 引擎 Key          | 说明                        | 文档链接                                                                                                                                       | 额外参数                                                                                                                                   |
| --------------- | ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------- |
| **kenlm**       | 基于统计语言模型的中文纠错             | [kenlm 模型(统计模型)](https://github.com/shibing624/pycorrector?tab=readme-ov-file#kenlm%E6%A8%A1%E5%9E%8B%E7%BB%9F%E8%AE%A1%E6%A8%A1%E5%9E%8B) | `language_model_path`, `custom_confusion_path_or_dict`, `proper_name_path`, `common_char_path`, `same_pinyin_path`, `same_stroke_path` |
| **macbert**     | 基于 Transformer 的拼写纠错模型    | [MacBERT 模型](https://github.com/shibing624/pycorrector?tab=readme-ov-file#macbert4csc%E6%A8%A1%E5%9E%8B)                                   | `model_name_or_path`                                                                                                                   |
| **t5**          | T5 架构的中文纠错模型              | [T5 模型](https://github.com/shibing624/pycorrector?tab=readme-ov-file#t5%E6%A8%A1%E5%9E%8B)                                                 | `model_name_or_path`                                                                                                                   |
| **ernie_csc**   | 基于 ERNIE 的中文纠错模型          | [ErnieCSC 模型](https://github.com/shibing624/pycorrector?tab=readme-ov-file#erniecsc%E6%A8%A1%E5%9E%8B)                                     | `model_name_or_path`                                                                                                                   |
| **gpt**         | 基于 ChatGLM / Qwen 等大模型的纠错 | [GPT 模型](https://github.com/shibing624/pycorrector?tab=readme-ov-file#gpt%E6%A8%A1%E5%9E%8B)                                               | `model_name_or_path`, `model_type`, `peft_name`                                                                                        |
| **mucgec_bart** | Bart 架构的中文纠错模型            | [Bart / MuCGEC Bart 模型](https://github.com/shibing624/pycorrector?tab=readme-ov-file#bart%E6%A8%A1%E5%9E%8B)                               | `model_name_or_path`                                                                                                                   |
