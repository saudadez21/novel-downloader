## `settings.toml` 配置说明

### general 配置

全局运行时设置, 面向下载 / 并发 / 速率限制 / 目录与存储的通用开关

#### 主配置项

| 参数名                | 类型    | 默认值             | 说明                                       |
| -------------------- | ------- | ----------------- | ------------------------------------------ |
| `raw_data_dir`       | `str`   | `"./raw_data"`    | 书籍数据存放目录                             |
| `output_dir`         | `str`   | `"./downloads"`   | 最终导出文件目录                             |
| `cache_dir`          | `str`   | `"./novel_cache"` | 本地缓存目录 (字体 / 图片等)                  |
| `request_interval`   | `float` | 0.5               | **同一本书**章节请求的间隔 (秒)               |
| `workers`            | `int`   | 4                 | 下载任务协程数量                             |
| `max_connections`    | `int`   | 10                | 最大并发连接数                               |
| `max_rps`            | `float` | 1000.0            | 全局 RPS 上限 (requests per second)         |
| `retry_times`        | `int`   | 3                 | 请求失败重试次数                             |
| `backoff_factor`     | `float` | 2.0               | 重试的退避因子 (每次重试等待时间将按倍数增加, 如 `2s`, `4s`, `8s`) |
| `timeout`            | `float` | 10.0              | 单次请求超时 (秒)                            |
| `storage_batch_size` | `int`   | 1                 | `sqlite` 每批提交的章节数 (提高写入性能)       |
| `cache_book_info`    | `bool`  | `true`            | 是否启用 book_info 缓存                      |
| `cache_chapter`      | `bool`  | `true`            | 是否启用章节缓存                             |
| `fetch_inaccessible` | `bool`  | `false`           | 是否尝试获取未订阅章节                        |
| `backend`            | `str`   | `"aiohttp"`       | 全局 HTTP 请求后端, 可选 `"aiohttp"`, `"httpx"`, `"curl_cffi"` |
| `http2`              | `bool`  | `true`            | 仅对 `httpx` 生效, 启用 HTTP/2 支持           |
| `impersonate`        | `str/None` | `None`         | 仅对 `curl_cffi` 生效, 启用浏览器指纹仿真模式  |

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

#### parser 子节

该配置用于处理 **混淆字体解码** 与 **图片章节 OCR 识别**, 并控制图片章节的 **去水印**。

| 参数名             | 类型            | 默认值      | 说明                                                        |
| ------------------ | -------------- | ---------- | ----------------------------------------------------------- |
| `enable_ocr`       | `bool`         | false      | 是否启用本地 OCR, 用于识别混淆字体或图片章节文本                |
| `batch_size`       | `int`          | 32         | OCR 模型推理时的批处理大小                                    |
| `remove_watermark` | `bool`         | false      | 是否尝试对图片章节进行去水印 (部分站点支持)                     |
| `model_name`       | `str/None`     | None       | OCR 模型名称, 如果设置为 `None`, 则使用 `PP-OCRv5_server_rec`  |
| `model_dir`        | `str/None`     | None       | OCR 模型存储路径                                              |
| `input_shape`      | `tuple/None`   | None       | OCR 模型输入图像尺寸, 格式为 (C, H, W)                         |
| `device`           | `str/None`     | None       | 用于推理的设备, 例如: "cpu"、"gpu"、"npu"、"gpu:0"、"gpu:0,1"  |
| `cpu_threads`      | `int`          | 10         | 在 CPU 上推理时使用的线程数量                                  |
| `enable_hpi`       | `bool`         | false      | 是否启用高性能推理                                             |

功能说明:

**混淆字体章节**

* 若未开启解析或解析失败, 程序将在导出 EPUB/HTML 时自动嵌入对应字体文件, 确保显示正常

依赖说明:

若启用了 `enable_ocr`, 需安装额外的图像处理依赖

```bash
pip install novel-downloader[image-utils]
```

OCR 功能依赖 `PaddleOCR` 及其模型, 请参考安装指南:

* [安装说明](./installation.md)

`PaddleOCR` 配置参考官方文档:

* [PaddleOCR 文档](https://www.paddleocr.ai/main/version3.x/module_usage/text_recognition.html#_4)

#### output 子节

控制导出格式, 文件命名与 EPUB 细节

| 参数名                        | 类型         | 默认值                | 说明                                       |
| ----------------------------- | ----------- | --------------------- | ------------------------------------------ |
| `formats`                     | `list[str]` | `[]`                  | 输出格式                                    |
| `render_missing_chapter`      | `bool`      | `true`                | 是否在导出时为缺失章节插入占位内容            |
| `append_timestamp`            | `bool`      | `true`                | 输出文件名是否追加时间戳                     |
| `filename_template`           | `str`       | `"{title}_{author}"`  | 文件名模板                                  |
| `include_picture`             | `bool`      | `true`                | 是否嵌入章节中的图片 (可能增加文件体积)       |

#### 调试子节

| 参数名                | 类型    | 默认值             | 说明                                  |
| -------------------- | ------- | ----------------- | ------------------------------------- |
| `debug.save_html`    | `bool`  | `false`           | 是否保存抓取到的原始 HTML 到磁盘         |
| `debug.log_level`    | `str`   | `"INFO"`          | 日志级别: DEBUG, INFO, WARNING, ERROR  |
| `debug.log_dir`      | `str`   | `"./logs"`        | 运行日志存放目录                        |

#### 示例配置

```toml
[general]
retry_times = 3
backoff_factor = 2.0
timeout = 10.0
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

model_name = "PP-OCRv5_mobile_rec"
```

---

### sites 配置

站点级设置 (如 `qidian`, `b520`, ...), **站点级会覆盖全局行为**, 每个站点配置位于 `[sites.<site>]` 下

#### 通用键

| 参数名             | 类型                                  | 默认值 | 说明                                   |
| ----------------- | ------------------------------------- | ------ | ------------------------------------- |
| `book_ids`        | `list<str>` / `list<dict>`            | -      | 小说 ID 列表                           |
| `login_required`  | `bool`                                | false  | 是否需要登录才能访问                    |

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

| 字段名        | 类型          | 必需 | 说明                        |
| ------------ | ------------- | --- | --------------------------- |
| `book_id`    | `str`         | 是  | 小说的唯一标识 ID             |
| `start_id`   | `str`         | 否  | 起始章节 ID (含起)            |
| `end_id`     | `str`         | 否  | 结束章节 ID (含止)            |
| `ignore_ids` | `list[str]`   | 否  | 需要跳过的章节 ID             |

#### 示例配置

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

[[sites.qidian.book_ids]]
book_id = "1010868264"
start_id = "434742822"
end_id = "528536599"
ignore_ids = ["507161874", "516065132"]

[[sites.qidian.book_ids]]
book_id = "1012584111"
```

**站点覆盖全局行为**

站点配置可以覆盖全局配置。

如下例中, 全局的 `request_interval = 0.5` 会被 `sites.qidian` 中的 `request_interval = 2.0` 覆盖:

```toml
[general]
timeout = 10.0
request_interval = 0.5

[sites.qidian]
login_required = true
request_interval = 2.0  # 覆盖全局的 0.5
```

---

### plugins 配置

插件系统相关设置, 用于开启/覆盖内置实现。

#### 主配置项

| 参数名                  | 类型     | 默认值               | 说明                                          |
| ---------------------- | -------- | ------------------- | --------------------------------------------- |
| `enable_local_plugins` | `bool`   | `false`             | 是否启用本地插件目录 (扫描并加载本地插件)                          |
| `override_builtins`    | `bool`   | `false`             | 是否允许本地插件**覆盖**同名的内置实现 (如同名站点/处理器/导出器)           |
| `local_plugins_path`   | `str`    | `"./novel_plugins"` | 本地插件目录路径; 仅在 `enable_local_plugins = true` 时生效 |

> 更多插件编写说明 (自定义站点、处理器、导出器), 见: [插件系统文档](../reference/plugins.md)

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
```
