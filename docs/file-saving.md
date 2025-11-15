## 文件保存

运行时会根据配置文件 (如 `./settings.toml`) 在当前工作目录下自动创建三个文件夹:

- `downloads`
- `novel_cache`
- `raw_data`

---

### novel_cache

用于存放运行过程中产生的缓存和 Cookies 数据

#### 固定字体缓存

用于缓存加密字体，避免重复下载与解析：

```text
novel_cache/fixed_fonts/{font_name}.woff2
novel_cache/fixed_font_map/{font_name}.json
```

---

### raw_data

存放每本书的原始 JSON 数据与章节内容。

#### 书籍信息与目录

```text
raw_data/{site_name}/{book_id}/book_info.<stage>.json
```

示例内容:

```json
{
  "book_name": "示例小说",
  "author": "示例作者",
  "cover_url": "//example.com/cover/12345/cover.webp",
  "update_time": "2025-05-09 19:58:13",
  "serial_status": "连载",
  "word_count": "123.45万字",
  "summary": "这是一本示例小说的简介。",
  "volumes": [
    {
      "volume_name": "示例卷",
      "chapters": [
        {
          "title": "第一章 示例章节",
          "url": "//example.com/chapter/1",
          "chapterId": "1"
        }
      ]
    }
  ]
}
```

#### 章节内容数据库

```text
raw_data/{site_name}/{book_id}/chapter.<stage>.sqlite
```

数据库表结构:

```sql
CREATE TABLE IF NOT EXISTS chapters (
  id           TEXT    NOT NULL PRIMARY KEY,
  title        TEXT    NOT NULL,
  content      TEXT    NOT NULL,
  need_refetch BOOLEAN NOT NULL DEFAULT 0,
  extra        TEXT
);
```

字段说明:

| 字段名       | 说明                                      |
| ----------- | ----------------------------------------- |
| **id**      | 章节 ID                                    |
| **title**   | 章节标题                                   |
| **content** | 章节正文                                   |
| **extra**   | JSON 字符串, 包含附加信息，如资源、更新时间等 |

**extra 字段结构**

`extra` 字段以 JSON 格式保存章节的附加数据:

```json
{
  "site": "example_site",
  "wordCount": 2114,
  "resources": [
    {
      "type": "image",
      "paragraph_index": 0,
      "url": "https://example.com/chap_cover.jpg",
      "alt": "章节封面图"
    },
    {
      "type": "image",
      "paragraph_index": 3,
      "base64": "iVBORw0KGgo...",
      "mime": "image/jpeg",
      "alt": "插图 1"
    },
    {
      "type": "image",
      "paragraph_index": 3,
      "url": "https://example.com/sample2.png",
      "alt": "插图 2"
    },
    {
      "type": "font",
      "url": "https://example.com/font.woff2"
    },
    {
      "type": "font",
      "base64": "d09GRgABAAAA...",
      "mime": "font/woff2"
    },
    {
      "type": "css",
      "text": "body { color: black; }"
    }
  ]
}
```

**resources 字段说明**

资源列表包含章节内出现的远程资源、内嵌资源、字体资源和 CSS 文本:

| 字段名                 | 类型             | 说明                                                   |
| --------------------- | ---------------- | ------------------------------------------------------ |
| **`type`**            | `str`            | 资源类型, 例如: `image` / `font` / `css` / `audio` 等   |
| **`paragraph_index`** | `int` (optional) | 资源对应正文段落的位置 (1-based, `0` 表示章节开头)        |
| **`url`**             | `str` (optional) | 远程资源的 URL                                          |
| **`base64`**          | `str` (optional) | Base64 格式的资源内容                                   |
| **`mime`**            | `str` (optional) | Base64 内容的 MIME 类型, 如 `image/jpeg`、`font/woff2`  |
| **`text`**            | `str` (optional) | 文本内容                                                |
| **`alt`**             | `str` (optional) | 资源的替代文本                                          |
| **`width`**           | `int` (optional) | 图片宽度                                                |
| **`height`**          | `int` (optional) | 图片高度                                                |

说明:

* 一个段落可能包含多个资源, 因此 `paragraph_index` 可以重复
* `paragraph_index = 0` 表示资源在第一段落之前出现

#### 章节资源文件夹

```text
raw_data/{site_name}/{book_id}/media/
```

用于保存本地下载的远程资源 (通常是 `image` 和 `font` 的 URL 内容)。

这些文件会在 EPUB 或 HTML 导出阶段内联或引用。

**存储策略说明**

* URL 资源 (如 `image`、`font`) 会下载到 `media/`
* Base64 资源不会在此目录生成文件, 通常在打包时直接使用
* URL 资源在保存时会使用 URL 的哈希值作为文件名, 并使用推测的扩展名: `{sha1_hash}.{ext}`

---

### downloads

存放整合后导出的书籍文件。

#### 全书 TXT 导出

```text
downloads/{book_name}_{author}.txt
```

#### 全书 EPUB 导出

```text
downloads/{book_name}_{author}.epub
```

#### 分卷 EPUB 导出

每个卷都会生成独立的 EPUB，文件名中包含卷名:

```text
downloads/{book_name}_{volume_name}_{author}.epub
```

#### 全书 HTML 导出

HTML 导出包含完整书籍内容、目录页、章节页面以及相关静态资源。

输出目录结构如下:

```bash
downloads/{book_name}_{author}/
├── index.html                  # 书籍首页 / 目录页
├── css/
│   ├── index.css               # 目录页样式
│   └── chapter.css             # 章节页统一样式
├── js/
│   └── main.js                 # 导航 / 交互逻辑
├── chapters/                   # 章节文本
│   ├── c001.html
│   ├── c002.html
│   ├── c003.html
│   └── ...
└── media/
    ├── cover.jpg               # 封面图
    ├── img_1.png               # 章节中引用的图片
    ├── img_2.png
    └── ...                     # 字体 / 资源缓存
```
