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

* **id**: 章节 ID
* **title**: 章节标题
* **content**: 章节正文
* **extra**: JSON 格式的附加字段 (作者话、时间戳等)

示例查询返回的记录 (`get_chapter("1")`):

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

#### 章节图片

```text
raw_data/{site_name}/{book_id}/images/
```

存放章节中下载的所有远程图片, 供 EPUB/HTML 导出时内联或引用。

---

### downloads

存放整合后导出的书籍文件。

#### 全书 TXT 导出 (`make_txt`)

```text
downloads/{book_name}_{author}.txt
```

#### 全书 EPUB 导出 (`make_epub`)

```text
downloads/{book_name}_{author}.epub
```

#### 分卷 EPUB 导出 (`export_by_volume`)

每个卷都会生成独立的 EPUB，文件名中包含卷名:

```text
downloads/{book_name}_{volume_name}_{author}.epub
```
