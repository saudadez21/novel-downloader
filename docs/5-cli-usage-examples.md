## CLI 使用示例

### 1. 下载小说

支持的站点列表详见: [站点支持文档](./6-supported-sites.md)

#### 1.1 显式指定配置文件 (优先级最高)

```bash
# 使用自定义配置文件, 下载起点小说 '123456' 和 '654321'
novel-cli --config "/path/to/custom.toml" download 123456 654321
```

#### 1.2 使用当前目录下的 `settings.toml`

```bash
# 在包含 ./settings.toml 的目录中运行 CLI 即可
cd novel-folder
novel-cli download 123456 654321
```

#### 1.3 使用已注册的全局配置

```bash
# 如果当前目录下没有 settings.toml, CLI 会尝试使用已注册的全局配置
# 注册命令示例:
# novel-cli settings set-config ./path/to/settings.toml
novel-cli download 123456 654321
```

> **登录提示说明**
> 若针对当前下载站点的配置中 `mode: browser` 且启用了 `login_required: true`, 程序将自动弹出浏览器窗口引导登录,
> 请根据提示完成操作, 以便访问受限章节内容。
>
> 如果是其他模式 (如 `session`) 并启用了 `login_required: true`, CLI 将检测当前是否已登录;
> 若未登录, 将提示你在命令行中手动输入当前站点的有效 Cookie 信息或账户信息

---

### 2. 全局选项

```text
novel-cli COMMAND [ARGS]...

Options:
  --help      显示此帮助信息并退出
```

---

### 3. 子命令一览

```text
Commands:
    clean               清理缓存和配置文件
    config              配置文件路径
    download            下载小说
    export              导出已下载的小说
```

---

### 4. download 子命令

按书籍 ID 下载完整小说, 支持从命令行或配置文件读取 ID:

```bash
novel-cli download [-h] [--site SITE] [--config CONFIG] [book_ids ...]
```

**参数说明**:

* `book_ids`: 要下载的书籍 ID (可选, 省略时将从配置文件读取)
* `--site [qidian|biquge|...]`: 站点名称缩写, 默认 `qidian`
* `--help`: 显示帮助信息

**示例**:

```bash
# 下载指定书籍 (默认 起点)
novel-cli download 1234567890

# 指定站点 (如 biquge)
novel-cli download --site biquge 8_8187

# 从配置文件中读取 ID
novel-cli download
```

查看完整支持站点列表: [`supported-sites.md`](./6-supported-sites.md)

---

### 5. config 子命令

用于初始化和管理下载器设置, 包括切换语言、设置 Cookie、更新规则等:

```bash
novel-cli config COMMAND [ARGS]...
```

**参数说明**:

* `init [--force]`: 在当前目录初始化默认配置文件
* `set-lang LANG`: 在中文 (zh) 和英文 (en) 之间切换界面语言
* `set-config PATH`: 设置并保存自定义 YAML 配置文件
* `update-rules PATH`: 从 TOML/YAML/JSON 文件更新站点解析规则
* `set-cookies [SITE] [COOKIES]`: 为指定站点设置 Cookie, 可省略参数交互输入

**示例:**

```bash
# 切换界面语言为英文
novel-cli config set-lang en

# 使用新的 settings.toml
novel-cli config set-config ./settings.toml

# 初始化默认配置到当前目录
novel-cli config init

# 强制覆盖已存在的配置文件
novel-cli config init --force
```

---

### 6. clean 子命令

清理下载器生成的本地缓存和全局配置文件:

```bash
novel-cli clean [OPTIONS]
```

**参数说明**:

* `--logs`: 清理日志目录 (`logs/`)
* `--cache`: 清理脚本缓存与浏览器数据 (`js_script/`、`browser_data/`)
* `--data`: 清理状态文件与 cookies (`state.json`)
* `--config`: 清理全局设置
* `--models`: 清理模型缓存目录
* `--all`: 清除所有配置、缓存、状态 (包括设置文件)
* `--yes`: 跳过确认提示
* `--help`: 显示帮助信息并退出

**示例:**

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

> **注意**: `--all` 会删除包括设置文件在内的所有本地数据, 请慎重使用！

---

### 7. export 子命令

导出已下载的小说为指定格式的文件:

```bash
novel-cli export [OPTIONS] book_ids [book_ids ...]
```

**参数说明**:

* `book_ids`: 要导出的一个或多个小说 ID
* `--format`: 导出格式, 可选值为 `txt`, `epub`, `all`, 默认 `all`
* `--site SITE`: 网站来源 (如 `biquge`, `qidian`), 默认 `qidian`
* `--config CONFIG`: 可选指定配置文件路径

**示例:**

```bash
# 导出为默认格式 (txt + epub)
novel-cli export 12345 23456

# 指定导出格式为 EPUB
novel-cli export --format epub 88888

# 指定站点来源并导出多本书
novel-cli export --site biquge 12345 23456

# 使用指定配置文件导出
novel-cli export --config ./settings.toml 4321
```

> **注意**: 必须提供至少一个 `book_ids`

---

> **提示**
>
> * 所有子命令均支持 `--help` 查看帮助文本
