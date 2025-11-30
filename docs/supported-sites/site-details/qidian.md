---
title: 起点中文网
tags:
  - 简体中文
  - 原创
  - 男性向
  - 阅文

---

热门小说网站，提供玄幻小说、武侠小说、原创小说、网游小说、都市小说、言情小说、青春小说、科幻小说等首发小说。

## 基本信息

* 标识符: `qidian`
* 主页: https://www.qidian.com
* 语言: 简体中文
* 站点状态: :green_circle: Active
* 支持分卷: :material-check: 是
* 支持插图: :material-close: 否
* 支持登录: :material-check: 是
* 支持搜索: :material-check: 是

---

## URL 示例

### Book URL

URL:

```
https://www.qidian.com/book/1010868264/
```

* Book ID: `1010868264`

### Chapter URL

URL:

```
https://www.qidian.com/chapter/1010868264/405976997/
```

* Book ID: `1010868264`
* Chapter ID: `405976997`

---

## 登录要求 (Login Requirement)

* 免费章节可直接阅读
* **订阅 / VIP 章节需要有效 Cookie 才能下载**

## VIP 章节说明

!!! warning "VIP 章节需要 Node.js"
    起点的 VIP 章节内容为加密格式, 需要额外工具才能解密。

    下载器在处理 VIP 章节时会调用 Node.js, 因此系统中需要提前安装:

    [Download Node.js](https://nodejs.org/en/download)

    若未安装 Node.js, 则 VIP 章节无法正常解析。

## 其它说明

* 若章节出现重复内容，可在 `settings.toml` -> `[sites.qidian]` 中设置 `use_truncation = true`
* 新章节可能出现字体混淆，可开启 `enable_ocr`
