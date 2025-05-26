# novel-downloader

一个基于 [DrissionPage](https://www.drissionpage.cn) 和 [requests](https://github.com/psf/requests) 的小说下载工具/库。

---

## 项目简介

**novel-downloader** 支持多种小说网站的章节抓取与合并导出,
- **轻量化抓取**: 绝大多数站点仅依赖 `requests` 实现 HTTP 请求, 无需额外浏览器驱动
- 对于起点中文网 (Qidian), 可在配置中选择:
  - `mode: session` : 纯 Requests 模式
  - `mode: browser`  : 基于 `DrissionPage` 驱动 Chrome 的浏览器模式 (可处理更复杂的 JS/加密)。
- **自动登录** (可选)
  - 配置 `login_required: true` 后自动检测并重用历史 Cookie
  - 首次登录或 Cookie 失效时:
    - **browser** 模式: 在程序打开的浏览器窗口登录, 登录后回车继续
    - **session** 模式: 根据提示粘贴浏览器中已登录的 Cookie (参考 [复制 Cookies](docs/copy-cookies.md))

## 功能特性

- 抓取起点中文网免费及已订阅章节内容
- 支持断点续爬, 自动续传未完成任务
- 自动整合所有章节并导出为:
  - TXT
  - EPUB (可选包含章节插图)
- 支持活动广告过滤:
  - [x] 章节标题
  - [ ] 章节正文

---

## 快速开始

```bash
# 克隆 + 安装
pip install novel-downloader

# 如需支持字体解密功能 (decode_font), 请使用:
# pip install novel-downloader[font-recovery]

# 初始化默认配置 (生成 settings.toml)
novel-cli settings init

# 编辑 ./settings.toml 完成 site/book_ids 等
# 可查看 docs/4-settings-schema.md

# 运行下载
novel-cli download 123456
```

- 详细可见: [支持站点列表](docs/6-supported-sites.md)
- 更多使用方法, 查看 [使用示例](docs/5-usage-examples.md)

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
- [环境准备](docs/2-environment-setup.md)
- [配置](docs/3-configuration.md)
- [settings.toml 配置说明](docs/4-settings-schema.md)
- [使用示例](docs/5-usage-examples.md)
- [支持站点列表](docs/6-supported-sites.md)
- [复制 Cookies](docs/copy-cookies.md)
- [文件保存](docs/file-saving.md)
- [TODO](docs/todo.md)
- [开发](docs/develop.md)
- [项目说明](#项目说明)

---

## 项目说明

- 本项目仅供学习和研究使用, 不得用于任何商业或违法用途。请遵守目标网站的 robots.txt 以及相关法律法规。
- 本项目开发者对因使用该工具所引起的任何法律责任不承担任何责任。
- 如果遇到网站结构变化或其他问题, 可能导致程序无法正常工作, 请自行调整代码或寻找其他解决方案。
