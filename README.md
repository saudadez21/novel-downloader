# novel-downloader

[![PyPI](https://img.shields.io/pypi/v/novel-downloader.svg)](https://pypi.org/project/novel-downloader/)
[![Python](https://img.shields.io/pypi/pyversions/novel-downloader.svg)](https://www.python.org/downloads/)
[![Build and Publish](https://github.com/saudadez21/novel-downloader/actions/workflows/release.yml/badge.svg?branch=main)](https://github.com/saudadez21/novel-downloader/actions/workflows/release.yml)
[![Downloads](https://img.shields.io/pypi/dm/novel-downloader.svg)](https://pypistats.org/packages/novel-downloader)
[![Hits-of-Code](https://hitsofcode.com/github/saudadez21/novel-downloader?branch=main&label=Hits-of-Code)](https://hitsofcode.com/github/saudadez21/novel-downloader/view?branch=main&label=Hits-of-Code)

异步小说下载工具 / 库。支持断点续传、广告过滤与 TXT/EPUB 导出, 提供 CLI 与 Web 图形界面。

> 运行要求: **Python 3.11+** (开发环境: Python 3.12)

> 基于 [aiohttp](https://github.com/aio-libs/aiohttp)

## 功能特性

* **可恢复下载**: 自动检测本地已完成的章节, 跳过重复下载
* **多格式导出**:
  * `TXT`
  * `EPUB` (可选打包章节插图)
* **广告/活动过滤**:
  * [x] 章节标题过滤
  * [x] 章节正文过滤
* **可选字体混淆还原**: `decode_font`
* **双形态使用**: 命令行 (CLI) 与 Web 图形界面 (GUI)
* **文本处理流水线 (processors)**: 正则清理 / 繁简转换 / 文本纠错等
* **插件系统**: 可扩展站点、处理器、导出器等能力

---

## 安装与更新

使用 `pip` 安装或更新到最新稳定版:

```bash
pip install -U novel-downloader
```

若需要启用字体解密功能 (`decode_font`), 请使用:

```bash
pip install -U "novel-downloader[font-recovery]"
```

> 参见: [安装](docs/1-installation.md)

---

## 快速开始

### 0. 设置语言 (可选)

支持多语言界面 (i18n), 可通过命令切换:

```bash
# 设置为中文
novel-cli config set-lang zh_CN

# 设置为英文
novel-cli config set-lang en_US
```

### 1. 初始化配置

```bash
# 生成默认配置 ./settings.toml
novel-cli config init
```

编辑生成的 `./settings.toml`, 可修改 `request_interval`、`book_ids` 等配置 (参考 [settings.toml 配置说明](docs/3-settings-schema.md))

### 2. 命令行 (CLI)

![cli_download](./docs/images/cli_download.gif)

常用示例:

```bash
# 使用书籍页面 URL 自动解析并下载
novel-cli download https://www.hetushu.com/book/5763/index.html

# 使用配置文件中的 book_ids 启动下载
novel-cli download --site qidian

# 指定站点 + 书籍 ID 启动下载
novel-cli download --site n23qb 12282
```

更多参数:

```bash
novel-cli --help
novel-cli download --help
```

* 支持站点见: [支持站点列表](docs/4-supported-sites.md)
* 更多示例见: [CLI 使用示例](docs/5-cli-usage-examples.md)
* 运行中可使用 `CTRL+C` 取消任务

### 3. 图形界面 (Web GUI)

```bash
# 启动 Web 界面 (基于当前 settings.toml)
novel-web

# 如需提供局域网/外网访问 (请自行留意安全与网络环境)
# novel-web --listen public
```

* 支持站点见: [支持站点列表](docs/4-supported-sites.md)
* 更多示例见: [WEB 使用示例](docs/6-web-usage-examples.md)
* 运行中可使用 `CTRL+C` 停止服务

### 4. 编程接口 (Programmatic API)

示例:

```python
import asyncio
from novel_downloader.plugins import registrar
from novel_downloader.schemas import BookConfig, ClientConfig

async def main() -> None:
    # 指定站点标识
    site = "n23qb"

    # 指定书籍 ID
    book = BookConfig(book_id="12282")

    # 创建客户端配置
    cfg = ClientConfig(request_interval=0.5)

    # 获取站点客户端实例
    client = registrar.get_client(site, cfg)

    # 在异步上下文中执行下载
    async with client:
        await client.download(book)

    # 下载完成后执行导出操作
    client.export(book, formats=["txt", "epub"])

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 文本处理 (`processors`)

导出前可对文本进行**多阶段流水线处理**, 例如:

* 正则清理 (自定义去广告/去水印)
* 繁简转换 (基于 [opencc-python](https://github.com/yichen0831/opencc-python))
* 文本纠错 (基于 [pycorrector](https://github.com/shibing624/pycorrector))

处理按顺序执行, 并生成中间产物用于后续导出。

> 详细配置示例见: [processors 配置](./docs/3-settings-schema.md#processors-配置)

---

## 插件系统

通过插件可扩展或覆盖现有能力 (站点/处理器/导出器等)

在 `settings.toml` 启用插件并按接口实现后, 即可无缝加入下载流程

例如新增站点解析器 (如 "刺猬猫" -> `ciweimao`), 实现目录页与章节页的抓取及解析方后即可直接下载:

```bash
novel-cli download --site ciweimao 123456
```

> 详见: [插件系统文档](./docs/plugins.md)

---

## 从源码安装 (开发版)

体验最新开发功能:

```bash
git clone https://github.com/saudadez21/novel-downloader.git
cd novel-downloader

# 可选: 启用多语言支持
# 安装 Babel 并编译翻译文件
# pip install babel
# pybabel compile -d src/novel_downloader/locales

pip install .
# 或安装带可选功能:
# pip install .[font-recovery]
```

---

## 常见问题 / 排错

* **网站结构变更导致解析失败**: 请先更新到最新版本, 或参考支持站点文档与插件机制自定义适配。
* **需要登录的站点**: 按 [复制 Cookies](docs/copy-cookies.md) 操作。
* **导出文件位置**: 见 [文件保存](docs/file-saving.md)。

---

## 文档导航

* [安装](docs/1-installation.md)
* [配置](docs/2-configuration.md)
* [settings.toml 配置说明](docs/3-settings-schema.md)
* [支持站点列表](docs/4-supported-sites.md)
* [CLI 使用示例](docs/5-cli-usage-examples.md)
* [WEB 使用示例](docs/6-web-usage-examples.md)
* [复制 Cookies](docs/copy-cookies.md)
* [文件保存](docs/file-saving.md)
* [模块与接口文档](docs/api.md)
* [TODO](docs/todo.md)

---

## 项目说明

* 本项目仅供学习和研究使用, **不得**用于任何商业或违法用途; 请遵守目标网站的 `robots.txt` 及相关法律法规
* 由于网站结构变化或其他原因, 可能导致本项目不稳定或不可用, 请按需调整或寻找替代方案
* 使用本项目产生的任何法律责任由使用者自行承担, 作者不承担相关责任
