## 使用示例

### 1. 下载小说

#### 1.1 强制指定配置文件 (最高优先)

```bash
# 运行 CLI 工具, 指定自定义配置, 下载起点小说 '123456' 和 '654321'
novel-cli --config "/path/to/custom.yaml" download 123456 654321
````

#### 1.2 默认读取当前目录 `settings.yaml`

```bash
# 在包含 ./settings.yaml 的目录下, 直接运行即可
cd novel-folder
novel-cli download 123456 654321
```

#### 1.3 使用已注册的全局配置

```bash
# 当当前目录没有 settings.yaml, 且之前已通过
# `novel-cli settings set-config ./path/to/settings.yaml`
# 注册过配置, CLI 会自动加载该全局配置
novel-cli download 123456 654321
```

#### 1.4 使用内置默认配置

```bash
# 全新环境中, 既未执行 init, 也未指定 --config,
# 则会加载包内默认 settings.yaml
novel-cli download 123456 654321
```

> **Browser 模式登录提示**
> 如果 `mode: browser` 且 `login_required: true`, 程序会在浏览器中弹出登录窗口,
> 请按提示完成登录, 以便获取需要的章节内容。

---

### 2. 全局选项

```text
novel-cli [OPTIONS] COMMAND [ARGS]...

Options:
  --config FILE   配置文件路径
  --help      显示此帮助信息并退出
```

---

### 3. 子命令一览

```text
Commands:
  download     下载小说
  interactive  小说下载与预览的交互式模式
  settings     配置下载器设置
  clean        清理本地缓存和配置文件
```

---

### 4. download 子命令

按书籍 ID 下载完整小说, 支持从命令行或配置文件读取 ID:

```bash
novel-cli download [OPTIONS] [BOOK_IDS]...
```

* **Arguments**
  `BOOK_IDS`: 要下载的书籍 ID 列表 (可省略, CLI 会从配置中读取)

* **Options**
  `--site [qidian]`: 网站来源, 默认为 `qidian`
  `--help`: 显示帮助信息并退出

**示例:**

```bash
# 直接指定要下载的书籍 ID
novel-cli download 1234567890 0987654321

# 不带 ID, 则从配置文件读取
novel-cli download

# 下载笔趣阁的书籍
novel-cli download --site biquge 8_7654
```

#### 下载笔趣阁等通用站点小说

在首次使用前, 请确保已注册站点规则 (仅需执行一次):

```bash
# 将笔趣阁等站点的规则文件注册到配置中
novel-cli settings update-rules ./rules.toml
```

例如访问站点 [笔趣阁](http://www.b520.cc), 小说页面地址如下:

* 示例链接: `http://www.b520.cc/8_8187/`
* 则书籍 ID 为: `8_8187`

使用以下命令开始下载:

```bash
novel-cli download --site biquge 8_8187
```

> **注意：**
> `./rules.toml` 中配置的站点名称 (如 `biquge`) 需与命令中的 `--site` 参数保持一致, 否则无法匹配到对应规则。

> 默认提供的 `./rules.toml` 暂仅包含「笔趣阁」的规则。
> 其他站点可根据需要自行补充, 或等待后续支持。

---

### 5. settings 子命令

用于初始化和管理下载器设置, 包括切换语言、设置 Cookie、更新规则等:

```bash
novel-cli settings [OPTIONS] COMMAND [ARGS]...
```

* `set-lang LANG`: 在中文 (zh) 和英文 (en) 之间切换界面语言
* `set-config PATH`: 设置并保存自定义 YAML 配置文件
* `update-rules PATH`: 从 TOML/YAML/JSON 文件更新站点解析规则
* `set-cookies [SITE] [COOKIES]`: 为指定站点设置 Cookie, 可省略参数交互输入
* `init [--force]`: 在当前目录初始化默认配置文件

**示例:**

```bash
# 切换界面语言为英文
novel-cli settings set-lang en

# 使用新的 settings.yaml
novel-cli settings set-config ./settings.yaml

# 更新站点解析规则
novel-cli settings update-rules ./rules.toml

# 为起点设置 Cookie (方式 1: 一行输入)
novel-cli settings set-cookies qidian '{"token": "abc123"}'

# 为起点设置 Cookie (方式 2: 交互输入)
novel-cli settings set-cookies

# 初始化默认配置到当前目录
novel-cli settings init

# 强制覆盖已存在的配置文件
novel-cli settings init --force
```

---

### 6. clean 子命令

清理下载器生成的本地缓存和全局配置文件:

```bash
novel-cli clean [OPTIONS]
```

* `--logs`: 清理日志目录 (`logs/`)
* `--cache`: 清理脚本缓存与浏览器数据 (`js_script/`、`browser_data/`)
* `--state`: 清理状态文件与 cookies (`state.json`)
* `--all`: 清除所有配置、缓存、状态 (包括设置文件)
* `--yes`: 跳过确认提示
* `--help`: 显示帮助信息并退出

**示例:**

```bash
# 清理缓存目录和浏览器数据
novel-cli clean --cache

# 清理日志和状态文件
novel-cli clean --logs --state

# 交互确认后清理所有数据 (包括配置文件)
novel-cli clean --all

# 无需确认直接清理所有数据
novel-cli clean --all --yes
```

> **注意**: `--all` 会删除包括设置文件在内的所有本地数据, 请慎重使用！

---

> **提示**
>
> * 所有子命令均支持 `--help` 查看本地化帮助文本
> * 切换语言后, 帮助文本与运行时提示会同步更新为中、英文对应
