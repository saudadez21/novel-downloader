## CLI 使用示例

支持的站点列表详见: [站点支持文档](./4-supported-sites.md)

### 目录

- [CLI 使用示例](#cli-使用示例)
  - [目录](#目录)
  - [快速开始](#快速开始)
  - [配置优先级](#配置优先级)
    - [常见方式](#常见方式)
  - [登录/鉴权](#登录鉴权)
  - [全局用法与帮助](#全局用法与帮助)
  - [子命令总览](#子命令总览)
    - [1. download 子命令](#1-download-子命令)
    - [2. search 子命令](#2-search-子命令)
    - [3. export 子命令](#3-export-子命令)
    - [4. config 子命令](#4-config-子命令)
    - [5. clean 子命令](#5-clean-子命令)
  - [附录 A: 术语与约定](#附录-a-术语与约定)

### 快速开始

```bash
# 下载指定书籍 (默认站点: qidian)
novel-cli download 1234567890

# 指定站点下载 (例如 biquge)
novel-cli download --site biquge 8_8187

# 导出为 EPUB
novel-cli export --format epub 88888
```

---

### 配置优先级

1. 命令行 `--config PATH`
2. 当前目录 `./settings.toml`
3. 已注册的全局配置 (通过 `config set-config` 设置)

#### 常见方式

* **显式指定配置 (优先级最高)**

  ```bash
  novel-cli --config "/path/to/settings.toml" download 123456 654321
  ```

* **使用当前目录的 `settings.toml`**

  ```bash
  cd novel-folder
  novel-cli download 123456 654321
  ```

* **使用已注册的全局配置**

  ```bash
  # 先注册一次全局配置
  novel-cli config set-config ./path/to/settings.toml
  # 任意目录直接使用
  novel-cli download 123456 654321
  ```

---

### 登录/鉴权

当配置启用 `login_required: true` 时, CLI 会检测登录状态; 若未登录, 将提示在命令行输入当前站点的有效 Cookie 或账号信息。

---

### 全局用法与帮助

```text
novel-cli COMMAND [ARGS]...

Options:
  --help    显示此帮助信息并退出
```

> 所有子命令均支持 `--help` 查看对应帮助文本。

---

### 子命令总览

```text
Commands:
  download    下载小说
  search      搜索小说
  export      导出已下载的小说
  config      管理配置与语言
  clean       清理缓存与配置
```

---

#### 1. download 子命令

按书籍 ID 下载完整小说, 支持从命令行或配置文件读取 ID

**Synopsis**

```bash
novel-cli download [-h] [--site SITE] [--config CONFIG] [--start START] [--end END] [--no-export] [book_ids ...]
```

**Options**

* `book_ids ...`: 要下载的书籍 ID (可选, 省略时将从配置文件读取)
* `--site SITE`: 站点键 (如 `qidian`, `biquge`, ...), 默认 `qidian`
* `--start START`: 起始章节**唯一 ID** (仅用于第一个 `book_id`)
* `--end`: 结束章节**唯一 ID**, **包含** (仅用于第一个 `book_id`)
* `--no-export`: 仅下载, 不进行导出。启用后将跳过导出步骤

> `--start` / `--end` 用于临时下载部分章节, 仅影响**第一个**命令行提供的 `book_id`。
>
> `--start` 和 `--end` 接收**章节唯一 ID**, 并非 "第几章" 的序号。可参考 [`supported-sites.md`](./4-supported-sites.md) 内说明。
>
> 需要复杂范围/忽略章节等, 请在配置文件使用结构化 `book_ids`; 参见 [配置文件说明](./3-settings-schema.md)。

**Examples**

```bash
# 下载指定起点小说的书籍
novel-cli download 1234567890

# 指定站点 (如 biquge)
novel-cli download --site biquge 8_8187

# 只下载起点小说的一部分章节
novel-cli download --start 10001 --end 10200 1234567890

# 仅下载, 跳过导出步骤
novel-cli download --no-export 1234567890

# 从配置文件中读取 ID
novel-cli download
```

---

#### 2. search 子命令

按关键字搜索小说

**Synopsis**

```bash
novel-cli search [-h] [--site SITE] [--config CONFIG] [--limit N] [--site-limit M] keyword
```

**Options**

* `keyword`: 搜索关键字
* `--site SITE`, `-s SITE`: 指定搜索站点, 可多次使用以指定多个站点, 不指定则搜索全部支持站点
* `--limit N`: 总体结果上限 (最小 1), 默认为 `20`
* `--site-limit M`: 单站点结果上限 (最小 1), 默认为 `5`

**Examples**

```bash
# 搜索所有站点 (默认全部)
novel-cli search 三体

# 指定单个站点 (如 biquge)
novel-cli search --site biquge 三体

# 搜索 biquge, 返回最多 5 条结果
novel-cli search --site biquge --limit 5 三体

# 总体返回最多 20 条, 每站点最多 5 条
novel-cli search --limit 20 --site-limit 5 三体

# 指定多个站点 (biquge 和 qianbi)
novel-cli search -s biquge -s qianbi 三体
```

---

#### 3. export 子命令

导出已下载的小说为指定格式

**Synopsis**

```bash
novel-cli export [-h] [--format FORMAT] [--site SITE] [--config CONFIG] book_id [book_ids ...]
```

**Options**

* `book_ids`: 要导出的一个或多个书籍 ID
* `--format FORMAT`: 导出格式: `txt` / `epub` / `all`, 默认 `all`
* `--site SITE`: 站点键 (如 `biquge`, `qidian`, ...), 默认 `qidian`

**Examples**

```bash
# 导出指定起点小说为默认格式 (txt + epub)
novel-cli export 12345 23456

# 指定导出格式为 EPUB
novel-cli export --format epub 88888

# 指定站点来源并导出多本书
novel-cli export --site biquge 12345 23456
```

> 必须提供至少一个 `book_id`。

---

#### 4. config 子命令

初始化和管理下载器设置, 包括切换语言等

**Synopsis**

```bash
novel-cli config COMMAND [ARGS]...
```

**Subcommands**

* `init [--force]`: 在当前目录初始化默认配置文件 (`./settings.toml`); `--force` 覆盖已存在文件
* `set-lang LANG`: 切换 CLI 语言 (`zh` / `en`)
* `set-config PATH`: 注册自定义 TOML 为**全局配置**

**Examples**

```bash
# 切换界面语言为英文
novel-cli config set-lang en

# 注册新的 settings.toml
novel-cli config set-config ./settings.toml

# 初始化默认配置到当前目录
novel-cli config init

# 强制覆盖已存在的配置文件
novel-cli config init --force
```

---

#### 5. clean 子命令

清理本地缓存与全局配置

**Synopsis**

```bash
novel-cli clean [OPTIONS]
```

**Options**

* `--logs`: 清理日志目录 (`logs/`)
* `--cache`: 清理脚本缓存与浏览器数据 (`js_script/`、`browser_data/`)
* `--data`: 清理状态文件与 Cookies
* `--config`: 清理全局设置
* `--all`: **清除所有**配置、缓存、状态
* `--yes`: 跳过确认提示

**Examples**

```bash
# 清理缓存目录和浏览器数据
novel-cli clean --cache

# 清理日志和状态文件
novel-cli clean --logs --data

# 交互确认后清理所有数据 (包括配置文件)
novel-cli clean --all

# 无需确认直接清理所有数据
novel-cli clean --all --yes
```

> **注意**: `--all` 会删除包括设置文件在内的所有本地数据, 请谨慎使用。

---

### 附录 A: 术语与约定

* **SITE (站点键) **: 在命令中用于指明站点的短名称 (如 `qidian`, `biquge`, `qianbi`) 。完整列表见 [站点支持文档](./4-supported-sites.md)。
* **章节唯一 ID**: 站点侧用于标识章节的 ID, **不是**连续的 "第 N 章" 序号; 在 `--start`/`--end` 中应传入此 ID。
* **配置文件路径**: 若未显式传入 `--config`, CLI 会按「配置优先级」自动解析。
