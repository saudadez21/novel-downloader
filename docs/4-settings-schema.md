## `settings.yaml` 配置说明

### requests 配置

| 参数名            | 类型    | 默认值          | 说明                                   |
|------------------|--------|---------------|--------------------------------------|
| `wait_time`        | int    | 5             | 每次请求等待时间 (秒)                     |
| `retry_times`      | int    | 3             | 请求失败重试次数                          |
| `retry_interval`   | int    | 5             | 重试间隔 (秒)                           |
| `timeout`          | int    | 30            | 页面加载超时时间 (秒)                     |
| `headless`         | bool   | false         | 是否以无头模式启动浏览器                   |
| `user_data_folder` | string | `""`          | 浏览器用户数据目录, 为空则使用默认目录      |
| `profile_name`     | string | `""`          | 使用的浏览器配置名称, 为空则使用默认配置        |
| `auto_close`       | bool   | true          | 页面抓取完后是否自动关闭浏览器               |
| `disable_images`   | bool   | true          | 是否禁用图片加载 (可加速页面渲染)           |
| `mute_audio`       | bool   | true          | 是否静音 (禁用音频播放)                 |


### general 配置

| 参数名               | 类型    | 默认值              | 说明                                   |
|---------------------|--------|-------------------|--------------------------------------|
| `request_interval`   | int    | 5                 | 同一本书各章节请求间隔 (秒)               |
| `raw_data_dir`       | string | `"./raw_data"`    | 原始章节 HTML/JSON 存放目录             |
| `output_dir`         | string | `"./downloads"`   | 最终输出文件存放目录                   |
| `cache_dir`          | string | `"./novel_cache"` | 本地缓存目录 (字体 / 图片等)       |
| `max_threads`        | int    | 4                 | 最大并发下载线程数 (未实现)               |
| `skip_existing`      | bool   | true              | 是否跳过已存在的章节                     |
| `debug.save_html`    | bool   | false             | 是否保存抓取到的原始 HTML 到磁盘         |
| `debug.log_level`    | string | `"INFO"`          | 日志级别: DEBUG, INFO, WARNING, ERROR |


### sites 配置

针对不同网站的专属配置, 通过站点名称区分 (如 `qidian`、`xxxxx` 等)

| 参数名           | 类型             | 默认值    | 说明                                       |
|-----------------|-----------------|---------|------------------------------------------|
| `book_ids`        | array[string]    | —       | 小说 ID 列表 (如 `1010868264`)               |
| `mode`            | string           | `"browser"` | 请求方式:`browser` 或 `session`              |
| `login_required`  | bool             | false   | 是否需要登录才能访问                         |
| `decode_font`     | bool             | false   | 是否尝试本地解码混淆字体                       |
| `use_freq`        | bool             | false   | 是否使用字符频率分析                         |
| `use_ocr`         | bool             | false   | 是否使用 OCR 辅助识别文本                    |
| `save_font_debug` | bool             | false   | 是否保存字体解码调试数据                     |


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

> **提示**:你可以根据自己需求在 `settings.yaml` 中添加或删除字段, 未列出的配置项请参考源码注释或自行扩展。
