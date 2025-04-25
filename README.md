# novel-downloader

一个基于 [DrissionPage](https://www.drissionpage.cn) 和 [requests](https://github.com/psf/requests) 的小说下载器。

---

## 项目简介

**novel-downloader** 是一个通用的小说下载库 / CLI 工具,
- 大多数支持的站点仅依赖 [`requests`](https://github.com/psf/requests) 进行 HTTP 抓取
- 对于起点中文网 (Qidian), 可在配置中选择:
  - `mode: requests` : 纯 Requests 模式
  - `mode: browser`  : 基于 DrissionPage 驱动 Chrome 的浏览器模式（可处理更复杂的 JS/加密）。
- 如果在 `browser` 模式下且 `login_required: true`, 首次运行会自动打开浏览器, 请完成登录后继续。

项目提供了完整的 Python 包结构（含 `pyproject.toml`）,
可以通过 `pip install .` 或 `pip install git+https://github.com/BowenZ217/novel-downloader.git` 安装为库, 并使用 `novel-cli` CLI 入口。

---

## 功能特性

- 爬取起点中文网的小说章节内容 (支持免费与已订阅章节)
- 自动整合所有章节并输出为完整的 TXT 文件
- 支持活动广告过滤:
  - [x] 章节标题
  - [ ] 章节正文
  - [ ] 作者说

---

## 环境准备

1. **浏览器依赖 (仅 Browser 模式)**
   - 如使用 `mode: browser`, 需安装 **Google Chrome/Chromium**。
   - 如果出现 “无法找到浏览器可执行文件路径, 请手动配置” 提示, 请参考 [DrissionPage 入门指南](https://www.drissionpage.cn/get_start/before_start/)。

2. **Python 环境**
   为避免包冲突, 建议创建独立环境：
   推荐使用 Conda 或 `venv` 创建独立环境, 避免包冲突：
   ```bash
   conda create -n novel-downloader python=3.11 -y
   conda activate novel-downloader
   ```
   或
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

---

## 安装

```bash
# 克隆项目
git clone https://github.com/BowenZ217/novel-downloader.git
cd novel-downloader

# 安装为库并生成 CLI
pip install .
```

安装后, 将在 PATH 中暴露 `novel-cli` 命令。

---

## 配置

1. 复制并重命名配置文件：
   ```bash
   cp config/sample_settings.yaml config/settings.yaml
   ```

2. 编辑 `config/settings.yaml`, 示例：
   ```yaml
   sites:
     qidian:
       # 小说 ID 列表
       book_ids:
         - "1234567890"
         - "0987654321"
       # 抓取模式: requests 或 browser
       mode: "browser"
       # 尝试登录后爬取
       login_required: true
   ```

---

## 使用说明

`novel-cli` 支持在**任意目录**下运行, 只需通过 `--config` 参数指定配置文件路径即可。

### 使用示例

```bash
# 指定配置文件路径
novel-cli --config "/path/to/settings.yaml"

# 示例：在当前目录下的 config 文件夹中指定配置文件
novel-cli --config "config/settings.yaml"
```

无论你当前在哪个目录, 只要提供正确的配置文件路径, `novel-cli` 就能正常运行。

```bash
# 创建一个新的工作目录
mkdir my-novel-folder

# 拷贝配置文件到该目录
cp settings.yaml my-novel-folder/

# 进入目录
cd my-novel-folder

# 运行 CLI 工具, 使用相对路径指定配置
novel-cli --config "settings.yaml"
```

### Browser 模式登录提示

如果使用 `mode: browser` 且 `login_required: true`, 程序可能会打开浏览器提示登录, 请按提示登录你的账号, 以便程序能获取需要的小说内容。

---

## 命令参数

查看所有参数和说明:
```bash
novel-cli -h
```

---

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
| `book_ids`        | array[string]    | —       | 小说 ID 列表（如 `1010868264`）               |
| `mode`            | string           | `"browser"` | 请求方式：`browser` 或 `session`              |
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

> **提示**：你可以根据自己需求在 `settings.yaml` 中添加或删除字段, 未列出的配置项请参考源码注释或自行扩展。

---

## 文件保存

- 章节存储: 每部小说的章节内容会保存在配置文件中指定的 `raw_data_dir` 文件夹中, 章节文件名格式为 `{chapterId}.txt`。
- 整合输出: 读取所有章节后, 程序会将它们整合成一个完整的 TXT 文件, 并保存到 `output_dir` 中。若启用 `append_timestamp` 选项, 生成的文件名会在原书名基础上附加当前时间戳, 以免重复保存时覆盖旧文件。

---

## TODO

以下为计划中的特性及优化方向

### 支持更多站点


### 移除 Qidian 对 DrissionPage 的依赖，改为解析 JS 注入数据 (session 模式)


### 加密字体识别优化 (基于 PaddleOCR)
- [x] 收集常见类似于加密字体的样本图像
- [x] 标注训练集并转换为 PaddleOCR 可用格式
- [ ] 使用 PaddleOCR 进行模型微调训练
- [ ] 加入验证集用于训练过程监控与调优
- [ ] 替换默认模型以提升整体识别效果

---

## 项目说明

- 本项目仅供学习和研究使用, 不得用于任何商业或违法用途。请遵守目标网站 (起点中文网) 的 robots.txt 以及相关法律法规。
- 本项目开发者对因使用该工具所引起的任何法律责任不承担任何责任。
- 如果遇到网站结构变化或其他问题, 可能导致程序无法正常工作, 请自行调整代码或寻找其他解决方案。
