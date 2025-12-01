# novel-downloader

[![PyPI](https://img.shields.io/pypi/v/novel-downloader.svg)](https://pypi.org/project/novel-downloader/)
[![Python](https://img.shields.io/pypi/pyversions/novel-downloader.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/saudadez21/novel-downloader/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/saudadez21/novel-downloader/actions/workflows/ci.yml)
[![Hits-of-Code](https://hitsofcode.com/github/saudadez21/novel-downloader?branch=main&label=Hits-of-Code)](https://hitsofcode.com/github/saudadez21/novel-downloader/view?branch=main&label=Hits-of-Code)

[中文](./README.md) | [English](./README.en.md)

异步、可扩展的小说下载与处理工具包。

支持断点续爬、多格式导出、文本处理流水线, 并提供 CLI 与可选 Web 界面。

**文档**: [项目文档](https://saudadez21.github.io/novel-downloader/)

**运行要求**: Python 3.11+ (开发环境: Python 3.13)

---

## 功能特性

- **异步与高性能下载**
- **可恢复下载 (断点续爬)**
- **可插拔 HTTP 后端:** `aiohttp` / `httpx` / `curl_cffi`
- **多格式导出:** TXT / EPUB / HTML
- **文本处理流水线:** 去广告、繁简转换、自动翻译等
- **图片章节与混淆章节支持 (可选)**
- **插件系统:** 可扩展站点解析器、导出器、Pipeline 等
- **CLI 与可选 Web GUI**

完整功能列表见: [功能总览](https://saudadez21.github.io/novel-downloader/)

---

## 安装与更新

使用 `pip` 安装最新稳定版本:

```bash
pip install -U novel-downloader
```

如需启用 Web GUI:

```bash
pip install novelkit[web-ui]
```

如需启用其它可选功能 (Web UI、图片转文字、额外后端等), 请参见: [安装指南](https://saudadez21.github.io/novel-downloader/guide/installation/)

---

## 快速开始 (CLI)

```bash
# 下载一本小说
novelkit download https://www.example.com/book/123/

# 使用站点 + 书籍 ID
novelkit download --site n23qb 12282
```

更多示例见: [CLI 使用示例](https://saudadez21.github.io/novel-downloader/guide/cli-examples/)

## 编程接口 (Programmatic API)

```python
import asyncio
from novel_downloader.plugins import registrar
from novel_downloader.schemas import BookConfig, ClientConfig

async def main() -> None:
    site = "n23qb"

    # 指定书籍 ID
    book = BookConfig(book_id="12282")

    # 创建客户端
    cfg = ClientConfig(request_interval=0.5)
    client = registrar.get_client(site, cfg)

    # 在异步上下文中执行下载
    async with client:
        await client.download_book(book)

    # 下载完成后执行导出操作
    client.export_book(book, formats=["txt", "epub"])

if __name__ == "__main__":
    asyncio.run(main())
```

更多示例见: [API 示例](https://saudadez21.github.io/novel-downloader/reference/api-examples/)

---

## 贡献与开发

```bash
git clone https://github.com/saudadez21/novel-downloader.git
cd novel-downloader

# 可选: 为多语言支持编译翻译文件
# pip install babel
# pybabel compile -d src/novel_downloader/locales

pip install .
# 或安装带可选功能:
# pip install .[all]
# pip install -e .[dev,all]
```

欢迎提交 Issue / PR。

---

## 注意事项

* **站点结构变更**: 若目标站点页面结构更新或章节抓取异常, 欢迎提 Issue 或提交 PR
* **登录支持范围**: 登录功能受站点策略与接口限制, 部分场景需要手动配置 Cookie 或进行账号绑定
* **请求频率**: 请合理设置抓取间隔, 避免触发风控或导致 IP 限制

---

## 项目说明

* 本项目仅供学习和研究使用, **不得**用于任何商业或违法用途
* 请遵守目标网站的 `robots.txt` 及相关法律法规
* 使用本项目产生的任何法律责任由使用者自行承担, 作者不承担相关责任
