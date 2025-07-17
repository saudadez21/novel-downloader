## 文件保存

运行时会根据配置文件 (如 `./settings.toml`) 在项目根目录下自动创建三个文件夹:

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

- **章节内容**

  ```text
  raw_data/{site_name}/{book_id}/chapter_data.sqlite
  ```

  示例章节结构:

  ```json
  {
    "id": "1",
    "title": "第一章 示例章节",
    "content": "这里是章节正文内容的示例。",
    "extra": {
        "author_say": "作者的话示例。",
        "updated_at": "2025-05-09 12:00",
        "update_timestamp": 1744180800,
        "modify_time": 1744184400,
        "word_count": 1024,
        "seq": 1,
        "volume": "示例卷"
    }
  }
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
