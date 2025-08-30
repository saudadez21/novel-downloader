# novel-downloader

基于 [aiohttp](https://github.com/aio-libs/aiohttp) 的异步小说下载工具 / 库。支持断点续传、广告过滤与 TXT/EPUB 导出, 提供 CLI 与 Web 图形界面。

> 运行要求: **Python 3.11+** (开发环境: Python 3.12)

## 功能特性

* **可恢复下载**: 运行时自动检测本地已完成的部分, 跳过已下载内容
* **多格式导出**: 合并所有章节为
  * `TXT`
  * `EPUB` (可选打包章节插图)
* **广告/活动过滤**:
  * [x] 章节标题过滤
  * [x] 章节正文过滤
* **可选字体混淆还原**: `decode_font`
* **双形态使用**: 命令行 (CLI) 与 Web 图形界面 (GUI)

---

## 安装

使用 `pip` 安装稳定版:

```bash
pip install novel-downloader
```

启用字体解密功能 (`decode_font`):

```bash
pip install "novel-downloader[font-recovery]"
```

> 参见: [安装](docs/1-installation.md)

---

## 快速开始

### 1. 初始化配置

```bash
# 生成默认配置 ./settings.toml
novel-cli config init
```

编辑生成的 `./settings.toml`, 可修改 `request_interval`、`book_ids` 等配置 (参考 [settings.toml 配置说明](docs/3-settings-schema.md))

### 2. 命令行 (CLI)

```bash
# 执行下载任务 (示例: 书籍 ID 为 123456, 默认站点为起点)
novel-cli download 123456
```

* 支持站点见: [支持站点列表](docs/4-supported-sites.md)
* 更多示例见: [CLI 使用示例](docs/5-cli-usage-examples.md)

### 3. 图形界面 (GUI / Web)

```bash
# 启动 Web 界面 (基于当前 settings.toml)
novel-web

# 如需提供局域网/外网访问 (请自行留意安全与网络环境)
# novel-web --listen public
```

---

## 从源码安装 (开发版)

体验最新开发功能:

```bash
git clone https://github.com/saudadez21/novel-downloader.git
cd novel-downloader
pip install .
# 或安装带可选功能:
# pip install .[font-recovery]
```

---

## 文档导航

* [安装](docs/1-installation.md)
* [配置](docs/2-configuration.md)
* [settings.toml 配置说明](docs/3-settings-schema.md)
* [支持站点列表](docs/4-supported-sites.md)
* [CLI 使用示例](docs/5-cli-usage-examples.md)
* [复制 Cookies](docs/copy-cookies.md)
* [文件保存](docs/file-saving.md)
* [模块与接口文档](docs/api/README.md)
* [TODO](docs/todo.md)
* [开发](docs/develop.md)

---

## 项目说明

* 本项目仅供学习和研究使用, **不得**用于任何商业或违法用途; 请遵守目标网站的 `robots.txt` 及相关法律法规
* 由于网站结构可能变化或其他问题, 可能导致无法正常工作, 请按需自行调整代码或寻找其他解决方案
* 使用本项目造成的任何法律责任由使用者自行承担, 项目作者不承担相关责任
