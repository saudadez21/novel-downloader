## `settings.yaml` 配置说明

### requests 配置

| 参数名            | 类型    | 默认值          | 说明                                   |
|------------------|--------|---------------|--------------------------------------|
| `wait_time`        | float  | 5.0           | 每次请求等待时间 (秒)                    |
| `retry_times`      | int    | 3             | 请求失败重试次数                         |
| `retry_interval`   | float  | 5.0           | 重试间隔 (秒)                           |
| `timeout`          | float  | 30.0          | 页面加载超时时间 (秒)                    |
| `max_rps`           | int \| null | null  | 最大请求速率 (requests per second), 为 `null` 则不限制 |
| `headless`         | bool   | false         | 是否以无头模式启动浏览器                   |
| `user_data_folder` | string | `""`          | 浏览器用户数据目录, 为空则使用默认目录      |
| `profile_name`     | string | `""`          | 使用的浏览器配置名称, 为空则使用默认配置        |
| `auto_close`       | bool   | true          | 页面抓取完后是否自动关闭浏览器               |
| `disable_images`   | bool   | true          | 是否禁用图片加载 (可加速页面渲染)           |
| `mute_audio`       | bool   | true          | 是否静音 (禁用音频播放)                 |


### general 配置

| 参数名               | 类型    | 默认值              | 说明                                   |
|---------------------|--------|-------------------|--------------------------------------|
| `request_interval`   | float  | 5.0               | 同一本书各章节请求间隔 (秒)                   |
| `raw_data_dir`       | string | `"./raw_data"`    | 原始章节 HTML/JSON 存放目录             |
| `output_dir`         | string | `"./downloads"`   | 最终输出文件存放目录                   |
| `cache_dir`          | string | `"./novel_cache"` | 本地缓存目录 (字体 / 图片等)       |
| `download_workers`   | int    | 4                 | 并发下载协程数                               |
| `parser_workers`     | int    | 4                 | 并发解析协程数                               |
| `use_process_pool`   | bool   | false             | 是否使用多进程池来处理任务                         |
| `skip_existing`      | bool   | true              | 是否跳过已存在的章节                     |
| `debug.save_html`    | bool   | false             | 是否保存抓取到的原始 HTML 到磁盘         |
| `debug.log_level`    | string | `"INFO"`          | 日志级别: DEBUG, INFO, WARNING, ERROR |

#### general.font_ocr 配置

| 参数名            | 类型         | 默认值     | 说明                                                   |
|------------------|--------------|------------|--------------------------------------------------------|
| `decode_font`     | bool         | false      | 是否尝试本地解码混淆字体                                |
| `use_freq`        | bool         | false      | 是否使用频率分析辅助识别                                 |
| `ocr_version`     | string       | `"v2.0"`   | OCR 使用的模型版本: `v1.0` / `v2.0`                      |
| `use_ocr`         | bool         | true       | 是否启用 OCR 辅助识别                                   |
| `use_vec`         | bool         | false      | 是否使用向量相似度辅助识别文本                            |
| `save_font_debug` | bool         | false      | 是否保存字体调试数据                                     |
| `batch_size`      | int          | 32         | OCR 批处理数量, 影响识别速度和内存使用                   |
| `gpu_mem`         | int          | 500        | GPU 显存限制 (MB)                                       |
| `gpu_id`          | int/null     | null       | 使用哪个 GPU, null 表示自动选择                         |
| `ocr_weight`      | float        | 0.6        | 最终结果中 OCR 部分的权重                                |
| `vec_weight`      | float        | 0.4        | 最终结果中向量识别部分的权重                             |

### sites 配置

针对不同网站的专属配置, 通过站点名称区分 (如 `qidian`、`xxxxx` 等)

| 参数名           | 类型             | 默认值        | 说明                                                           |
|------------------|------------------|---------------|----------------------------------------------------------------|
| `book_ids`        | array[string]     | —             | 小说 ID 列表 (如 `1010868264`)                                 |
| `mode`            | string            | `"browser"`   | 请求方式: `browser` / `session` / `async`                       |
| `login_required`  | bool              | false         | 是否需要登录才能访问                                           |

### output 配置

| 参数名                         | 类型     | 默认值                          | 说明                                       |
|-------------------------------|---------|-------------------------------|-------------------------------------------|
| `clean_text`                  | bool    | true                          | 是否对章节文本做清理                         |
| `formats.make_txt`            | bool    | true                          | 是否生成完整 TXT 文件                       |
| `formats.make_epub`           | bool    | false                         | 是否生成 EPUB 文件                         |
| `formats.make_md`             | bool    | false                         | 是否生成 Markdown 文件 (未实现)             |
| `formats.make_pdf`            | bool    | false                         | 是否生成 PDF 文件 (未实现)                  |
| `naming.append_timestamp`     | bool    | true                          | 在输出文件名中追加时间戳                     |
| `naming.filename_template`    | string  | `"{title}_{author}"`          | 输出文件名模板                              |
| `epub.include_cover`          | bool    | true                          | EPUB 中是否包含封面                         |
| `epub.include_toc`            | bool    | true                          | EPUB 中是否自动生成目录                     |

> **提示**: 可以根据自己需求在 `settings.yaml` 中添加或删除字段, 未列出的配置项请参考源码注释或自行扩展。
