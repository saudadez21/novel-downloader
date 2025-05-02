# novel-downloader

一个基于 [DrissionPage](https://www.drissionpage.cn) 和 [requests](https://github.com/psf/requests) 的小说下载器。

---

## 项目简介

**novel-downloader** 是一个通用的小说下载库 / CLI 工具,
- 大多数支持的站点仅依赖 [`requests`](https://github.com/psf/requests) 进行 HTTP 抓取
- 对于起点中文网 (Qidian), 可在配置中选择:
  - `mode: session` : 纯 Requests 模式
  - `mode: browser`  : 基于 DrissionPage 驱动 Chrome 的浏览器模式 (可处理更复杂的 JS/加密)。
- 如果在 `browser` 模式下且 `login_required: true`, 首次运行会自动打开浏览器, 请完成登录后继续。

---

## 功能特性

- 爬取起点中文网的小说章节内容 (支持免费与已订阅章节)
- 自动整合所有章节并输出为完整的 TXT 文件
- 支持活动广告过滤:
  - [x] 章节标题
  - [ ] 章节正文
  - [ ] 作者说

---

## 安装

**Python 环境**
为避免包冲突, 建议创建独立环境:
推荐使用 Conda 或 `venv` 创建独立环境, 避免包冲突:
```bash
conda create -n novel-downloader python=3.11 -y
conda activate novel-downloader
```
或
```bash
python -m venv .venv
source .venv/bin/activate
```

项目提供了完整的 Python 包结构 (含 `pyproject.toml`),
可以通过 `pip install .` 或 `pip install git+https://github.com/BowenZ217/novel-downloader.git` 安装为库, 并使用 `novel-cli` CLI 入口。

```bash
# 克隆项目
git clone https://github.com/BowenZ217/novel-downloader.git
cd novel-downloader

# 安装为库并生成 CLI
pip install .
```

安装完成后, 会在系统 `PATH` 中生成 `novel-cli` 可执行命令。

---

## 环境准备

### **浏览器依赖 (仅 Browser 模式)**
   - 如使用 `mode: browser`, 需安装 **Google Chrome/Chromium**。
   - 如果出现 “无法找到浏览器可执行文件路径, 请手动配置” 提示, 请参考 [DrissionPage 入门指南](https://www.drissionpage.cn/get_start/before_start/)。

### Qidian 的 VIP 章节解析 (session 模式)

**注**: 如果使用的是 `mode: browser` 模式, 无需进行以下步骤: 程序会自动打开浏览器提示登录并维持会话, 可直接解析 VIP 章节, 无需安装 Node.js 或设置 Cookie。

起点的 VIP 章节采用了基于 JavaScript 的加密 (Fock 模块)。在 `mode: session` 模式下, 当遇到 VIP 章节时, 程序会调用本地 `Node.js` 脚本进行解密。

此功能依赖系统已安装 [Node.js](https://nodejs.org/), 并确保 `node` 命令可在命令行中访问。

未安装 `Node.js` 时, 程序将报错提示 `Node.js is not installed or not in PATH.`。
建议安装稳定版本 (LTS) 即可: [https://nodejs.org](https://nodejs.org)

**注意:VIP 章节访问需要登录 Cookie。**
在使用 `session` 模式前, 请先通过以下命令设置自己的 cookie, 并确保包含以下关键字段:

```
ywguid, ywkey, ywopenid, w_tsfp, ...
```

这些字段通常会在登录状态下由浏览器自动生成。

你可以在浏览器登录起点后, 通过浏览器开发者工具 (F12) 复制完整的 Cookie 字符串:

1. 打开浏览器, 登录 [https://www.qidian.com](https://www.qidian.com)
2. 按 `F12` 打开开发者工具
3. 切到「Console」控制台
4. 粘贴下面这行代码并回车:
    ```js
    copy(document.cookie)
    ```
5. 然后直接粘贴到终端使用:
    ```bash
    novel-cli settings set-cookies qidian "粘贴这里"
    ```

    或者直接运行命令后按提示交互输入:
    ```bash
    novel-cli settings set-cookies
    ```

---

## 配置

1. 复制示例配置:
   ```bash
   cp config/sample_settings.yaml config/settings.yaml
   ```

2. 编辑 `config/settings.yaml`, 示例内容:
   ```yaml
   sites:
     qidian:
       # 小说 ID 列表
       book_ids:
         - "1234567890"
         - "0987654321"
       # 抓取模式, 可选 "session" 或 "browser"
       mode: "session"
       # 是否要登录后再爬取
       login_required: true
   ```

3. 将配置文件注册到 CLI:
   ```bash
   novel-cli settings set-config config/settings.yaml
   ```

4. 将自定义规则注册到 CLI:
   ```bash
   novel-cli settings update-rules config/sample_rules.toml
   ```

---

## 使用示例

- **指定配置文件启动**
  ```bash
  novel-cli --config "/path/to/settings.yaml"
  ```

- **在项目根目录下使用默认 `config/settings.yaml`**
  ```bash
  novel-cli --config "config/settings.yaml"
  ```

> `novel-cli` 可在**任意目录**下运行, 如果需要使用特点配置文件只需通过 `--config` 指定文件路径。

例如在将配置文件注册到 CLI 后可以新建目录并在里面运行:

```bash
# 创建一个新的工作目录
mkdir my-novel-folder

# 进入目录
cd my-novel-folder

# 运行 CLI 工具, 下载起点的 '123456' 和 '654321'
novel-cli download 123456 654321
```

### Browser 模式登录提示

如果使用 `mode: browser` 且 `login_required: true`, 程序可能会打开浏览器提示登录, 请按提示登录你的账号, 以便程序能获取需要的小说内容。

---

## 全局选项

```
novel-cli [OPTIONS] COMMAND [ARGS]...

Options:
  --config FILE   配置文件路径
  -h, --help      显示此消息并退出
```

---

## 子命令一览

```
Commands:
  download     下载小说
  interactive  小说下载与预览的交互式模式
  settings     配置下载器设置
```

---

### download

按书籍 ID 下载完整小说, 支持从命令行或配置文件读取 ID:

```
novel-cli download [OPTIONS] [BOOK_IDS]...

  按书籍 ID 下载完整小说。

Arguments:
  BOOK_IDS           要下载的书籍 ID 列表 (可省略, 从配置读取)

Options:
  --site [qidian]    网站来源, 默认为 'qidian'
  -h, --help         显示此消息并退出
```

**示例:**

```bash
# 直接指定要下载的书籍 ID
novel-cli download 1234567890 0987654321

# 不带 ID, 则从配置文件中读取
novel-cli download

# 下载笔趣阁的书籍
novel-cli download --site biquge 8_7654
```

---

### settings

配置和管理下载器相关设置:

```
novel-cli settings [OPTIONS] COMMAND [ARGS]...

  配置下载器设置

Options:
  -h, --help      显示此消息并退出

Commands:
  set-lang LANG       在中文 (zh) 和英文 (en) 之间切换语言
  set-config PATH     设置并保存自定义 YAML 配置文件
  update-rules PATH   从 TOML/YAML/JSON 文件更新站点规则
  set-cookies [SITE] [COOKIES]   为指定站点设置 Cookie, 可省略参数交互输入
```

**示例:**

```bash
# 切换界面语言为英文
novel-cli settings set-lang en

# 使用新的 settings.yaml
novel-cli settings set-config config/settings.yaml

# 更新站点解析规则
novel-cli settings update-rules config/sample_rules.toml

# 为起点设置 Cookie (方式 1:一行输入)
novel-cli settings set-cookies qidian '{"token": "abc123"}'

# 为起点设置 Cookie (方式 2:交互输入)
novel-cli settings set-cookies
```

---

当然可以，下面是模仿 `settings` 的风格写的 `clean` 子命令说明，适合放进 README:

---

### clean

清理下载器生成的本地缓存和配置文件:

```
novel-cli clean [OPTIONS]

  清理缓存和配置文件
```

**Options:**

| 选项             | 说明                                        |
| -------------- | ----------------------------------------- |
| `--logs`       | 清理日志目录 (logs/)                             |
| `--cache`      | 清理脚本缓存与浏览器数据 (js\_script/, browser\_data/) |
| `--state`      | 清理状态文件与 cookies (state.json)                        |
| `--all`        | 清除所有配置、缓存、状态 (包括设置文件)                      |
| `--yes`        | 跳过确认提示                                    |
| `--help`       | 显示此消息并退出                                  |

---

**示例:**

```bash
# 清理缓存目录和浏览器数据
novel-cli clean --cache

# 清理日志和状态文件
novel-cli clean --logs --state

# 清理所有数据 (包括配置文件)，交互确认
novel-cli clean --all

# 无需确认直接清除所有数据 (适合脚本使用)
novel-cli clean --all --yes
```

> 注意:`--all` 会清除包括设置文件在内的所有本地数据，使用时请谨慎！

---

> **提示**:
> - 所有子命令均支持 `--help` 查看本地化帮助文本
> - 切换语言后, 帮助文本与运行时提示会同步变更为中文或英文

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

---

## 文件保存

- 章节存储: 每部小说的章节内容会保存在配置文件中指定的 `raw_data_dir` 文件夹中, 章节文件名格式为 `{chapterId}.txt`。
- 整合输出: 读取所有章节后, 程序会将它们整合成一个完整的 TXT 文件, 并保存到 `output_dir` 中。若启用 `append_timestamp` 选项, 生成的文件名会在原书名基础上附加当前时间戳, 以免重复保存时覆盖旧文件。

---

## TODO

以下为计划中的特性及优化方向

### 支持更多站点


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
