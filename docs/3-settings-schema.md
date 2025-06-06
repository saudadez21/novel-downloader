## `settings.toml` 配置说明

### requests 配置

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

### general 配置

全局通用行为设置, 包括下载控制 / 目录结构 / 存储方式与调试选项等

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

### sites 配置

针对不同网站的专属配置, 通过站点名称区分 (如 `qidian`、`xxxxx` 等)

| 参数名           | 类型             | 默认值        | 说明                                                           |
|------------------|------------------|---------------|----------------------------------------------------------------|
| `book_ids`        | array[string]     | -             | 小说 ID 列表 (如 `1010868264`)                                 |
| `mode`            | string            | `"browser"`   | 请求方式: `browser` / `session` /                             |
| `login_required`  | bool              | false         | 是否需要登录才能访问                                           |

### output 配置

控制输出格式 / 文件命名规则以及生成文件的内容设置

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

> **提示**: 可根据实际需求在 `settings.toml` 中增删字段, 未列出的配置项可参考源码注释或自行扩展。
