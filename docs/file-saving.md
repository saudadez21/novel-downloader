## 文件保存

运行时会根据配置文件 (如 `./settings.yaml`) 在项目根目录下自动创建三个文件夹:

- `downloads`
- `novel_cache`
- `raw_data`

---

### novel_cache

用于存放运行过程中产生的缓存和调试数据:

- **固定字体缓存** 避免重复下载和解析加密字体:

  ```text
  novel_cache/fixed_fonts/{font_name}.woff2
  novel_cache/fixed_font_map/{font_name}.json
  ```

- **HTML 调试文件** (当 `debug.save_html: true` 时):

  ```text
  novel_cache/{site_name}/{book_id}/html/{chapter_id}.html
  ```

- **字体解码调试数据** (当 `save_font_debug: true` 时):

  ```text
  novel_cache/font_debug/{chapter_id}/debug_data.json
  ```

---

### raw_data

保存每本书的原始 JSON 数据和章节内容:

- **书籍信息与目录**

  ```text
  raw_data/{site_name}/{book_id}/book_info.json
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

- **普通章节内容**

  ```text
  raw_data/{site_name}/{book_id}/chapters/{chapter_id}.json
  ```

  示例结构:

  ```json
  {
    "id": "1",
    "title": "第一章 示例章节",
    "content": "这里是章节正文内容的示例。",
    "author_say": "作者的话示例。",
    "updated_at": "2025-05-09 12:00",
    "update_timestamp": 1744180800,
    "modify_time": 1744184400,
    "word_count": 1024,
    "vip": false,
    "purchased": false,
    "order": 1,
    "seq": 1,
    "volume": "示例卷"
  }
  ```

- **加密章节 (仅限 qidian)**
  当遇到 VIP 章节或加密字体时 (一般对应一个月内更新的章节), 会在下面路径生成解密后的数据:

  ```text
  raw_data/{site_name}/{book_id}/encrypted_chapters/{chapter_id}.json
  ```

---

### downloads

存放整合后导出的文件:

- **TXT 文件**

  ```text
  downloads/{book_name}_{author}.txt
  ```

- **EPUB 文件**（如果启用 `make_epub`）

  ```text
  downloads/{book_name}_{author}.epub
  ```
