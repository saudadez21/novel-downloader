# novel-downloader

一个基于 [aiohttp](https://github.com/aio-libs/aiohttp) 的小说下载工具/库。

> 本项目开发环境为 Python 3.12, 需确保运行环境为 Python 3.11 及以上版本

## 功能特性

- 支持断点续爬, 自动续传未完成任务
- 自动整合所有章节并导出为:
  - TXT
  - EPUB (可选包含章节插图)
- 支持活动广告过滤:
  - [x] 章节标题
  - [x] 章节正文

---

## 快速开始

### 安装

使用 `pip` 安装:

```bash
pip install novel-downloader
```

如需启用字体解密功能 (`decode_font`, 用于处理起点中文网对近一个月更新章节所采用的字体混淆技术), 请使用扩展安装方式:

```bash
pip install novel-downloader[font-recovery]
```

- 详细可见: [安装](docs/1-installation.md)

---

### CLI 模式

```bash
# 初始化默认配置 (生成 settings.toml)
novel-cli config init

# 编辑 ./settings.toml 完成 site/book_ids 等
# 可查看 docs/3-settings-schema.md

# 执行下载任务
novel-cli download 123456
```

- 详细可见: [支持站点列表](docs/4-supported-sites.md)
- 更多使用方法, 查看 [使用示例](docs/6-cli-usage-examples.md)

---

### TUI 模式 (终端用户界面)

**注意**: TUI 模式仍在开发中, 目前尚未实现登录和修改设置等功能。建议优先使用稳定的 CLI 模式。

```bash
# 初始化默认配置 (生成 settings.toml)
novel-cli config init

# 编辑 ./settings.toml 修改网络配置
# 可查看 docs/3-settings-schema.md

# 启动 TUI 界面
novel-tui
```

- 详细可见: [支持站点列表](docs/4-supported-sites.md)
- 更多使用方法, 查看 [使用示例](docs/5-tui-usage-examples.md)

---

### GUI 模式 (图形界面)

尚未实现

---

## 从 GitHub 安装 (开发版)

如需体验开发中的最新功能, 可通过 GitHub 安装:

```bash
git clone https://github.com/BowenZ217/novel-downloader.git
cd novel-downloader
pip install .
# 或安装带可选功能:
# pip install .[font-recovery]
```

---

## 文档结构

- [项目简介](#项目简介)
- [安装](docs/1-installation.md)
- [配置](docs/2-configuration.md)
- [settings.toml 配置说明](docs/3-settings-schema.md)
- [支持站点列表](docs/4-supported-sites.md)
- [TUI 使用示例](docs/5-tui-usage-examples.md)
- [CLI 使用示例](docs/6-cli-usage-examples.md)
- [复制 Cookies](docs/copy-cookies.md)
- [文件保存](docs/file-saving.md)
- [模块与接口文档](docs/api/README.md)
- [TODO](docs/todo.md)
- [开发](docs/develop.md)
- [项目说明](#项目说明)

---

## 项目说明

- 本项目仅供学习和研究使用, 不得用于任何商业或违法用途。请遵守目标网站的 robots.txt 以及相关法律法规。
- 本项目开发者对因使用该工具所引起的任何法律责任不承担任何责任。
- 如果遇到网站结构变化或其他问题, 可能导致程序无法正常工作, 请自行调整代码或寻找其他解决方案。
