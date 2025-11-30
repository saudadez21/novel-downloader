# NovelDownloader 文档

> 一个异步、可扩展的小说下载与处理工具包

---

## 项目简介

**NovelDownloader** 提供从网页内容获取、章节解析、文本处理到导出文件的完整工作流。

核心特性包括:

* 异步下载与断点续传
* 多格式导出 (TXT / EPUB / HTML)
* 文本清洗与增强流水线 (processors)
* 可插拔站点解析器与处理器
* 可编程 API
* 命令行 (CLI) 与可选 Web GUI

> 运行要求: **Python 3.11+** (开发环境: Python 3.13)

---

## 功能特性

### 下载能力

* 支持断点续爬: 自动识别已下载的章节
* 可插拔 HTTP 后端:
    * `aiohttp` (默认)
    * `httpx`
    * `curl_cffi` (适合反爬站点)

---

### 多格式导出

* TXT
* EPUB
* HTML

---

### 内容清洗与增强

* 广告过滤
    * 标题过滤
    * 正文过滤
* 文本处理流水线 (processors), 包括但不限于:
    * 正则清理
    * 繁简转换
    * 机器翻译
* 图片章节与混淆章节处理 (可选组件):
    * 原图下载
    * 去水印
    * 图像预处理
    * OCR 文本提取
    * 字体混淆还原

---

### 扩展能力

* 插件系统: 可扩展站点解析、文本处理、导出格式等
* 可插拔 HTTP 客户端
* 可自定义处理流水线与导出逻辑

---

### 使用方式

* 命令行 (CLI)
* Web 图形界面 (可选安装)
* Python 编程接口

---

## 安装

使用 pip 安装:

```bash
pip install -U novel-downloader
```

安装全部可选功能:

```bash
pip install novel-downloader[all]
```

更多安装方式见: [安装指南](guide/installation.md)。

---

## 快速开始

### 设置语言 (可选)

```bash
# 设置为中文
novel-cli config set-lang zh_CN

# 设置为英文
novel-cli config set-lang en_US
```

### 初始化配置文件

```bash
novel-cli config init
```

生成 `settings.toml` 后可根据需求调整:

* 抓取间隔
* 默认站点配置
* 文本处理流水线

详细说明见: [配置结构](guide/settings-reference.md)。

### 命令行 (CLI)

```bash
# 自动解析 URL 并下载
novel-cli download https://example.com/book/1234/

# 使用站点名与书籍 ID
novel-cli download --site qidian 12345
```

更多参数:

```bash
novel-cli --help
novel-cli download --help
```

* 支持站点见: [支持站点列表](supported-sites/index.md)
* 更多示例见: [CLI 使用说明](guide/cli-examples.md)
* 运行中可使用 `CTRL+C` 取消任务

### 图形界面 (Web GUI)

Web GUI 依赖额外组件 (如 NiceGUI), 默认不会随主程序一起安装。

如需使用 Web 图形界面，请先安装对应的可选依赖。

**安装 Web GUI 依赖**

```bash
pip install novel-downloader[web-ui]
```

> 若只需使用 CLI，可忽略此步骤。

**启动 Web GUI**

```bash
novel-web
```

如需提供局域网/外网访问 (请自行留意安全与网络环境):

```bash
novel-web --listen public
```

在运行过程中, 可使用 `CTRL+C` 停止服务。

**更多资料**

* 支持站点见: [支持站点列表](supported-sites/index.md)
* 更多示例见: [WEB 使用说明](guide/web-examples.md)

---

## 编程接口示例

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

完整 API 文档见: [API Reference](reference/api-examples.md)。

---

## 文本处理 (`processors`)

NovelDownloader 支持多阶段文本处理流水线, 包括:

* 正则清理 (自定义去广告/去水印)
* 繁简转换 (基于 [opencc-python](https://github.com/yichen0831/opencc-python))
* 自动翻译 (支持 `google` / `edge` / `youdao` 等翻译器)
* 文本纠错 (基于 [pycorrector](https://github.com/shibing624/pycorrector))
* 自定义处理器

详见: [Processors 文档](guide/processors-reference.md)。

---

## 插件系统

NovelDownloader 通过注册系统扩展功能, 包括:

* 新站点解析器
* 新文本处理器
* 新导出器

文档见: [插件开发指南](reference/plugins.md)。

---

## 从源码安装

```bash
git clone https://github.com/saudadez21/novel-downloader.git
cd novel-downloader

# 可选: 为多语言支持编译翻译文件
# pip install babel
# pybabel compile -d src/novel_downloader/locales

pip install .
# 或安装带可选功能:
# pip install .[all]
```

---

## 常见问题

* **需要登录的站点**: 参考 [复制 Cookies](guide/copy-cookies.md)。
* **导出文件位置**: 见 [文件保存](guide/file-saving.md)。

---

## 注意事项

* **站点结构变更**: 若目标站点页面结构更新或章节抓取异常, 欢迎提 Issue 或提交 PR
* **登录支持范围**: 登录功能受站点策略与接口限制, 部分场景需要手动配置 Cookie 或进行账号绑定
* **请求频率**: 请合理设置抓取间隔, 避免触发风控或导致 IP 限制

---

## 项目说明

* 本项目仅供学习和研究使用, **不得**用于任何商业或违法用途; 请遵守目标网站的 `robots.txt` 及相关法律法规
* 使用本项目产生的任何法律责任由使用者自行承担, 作者不承担相关责任
