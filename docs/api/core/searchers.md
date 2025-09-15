## Searchers

### 目录

- [Searchers](#searchers)
  - [目录](#目录)
  - [导入方式](#导入方式)
  - [返回类型](#返回类型)

---

### 导入方式

```python
from novel_downloader.core.searchers import search
```

描述: 根据提供的关键词, 在指定站点或全部已配置站点中搜索小说, 并返回符合条件的结果列表

参数:

* `keyword`: 要搜索的关键字
* `sites`: 要搜索的站点键列表, 可选
* `limit`: 综合返回结果的最大数量, 默认为 `10`
* `per_site_limit`: 每个站点返回结果的最大数量, 默认为 `5`

示例:

```python
from novel_downloader.core.searchers import search

# 在所有站点搜索 '三体', 最多返回 10 条结果
results = search(
    keyword="三体",
)

# 在 b520 和 n23qb 站点搜索 '遮天'
results = search(
    keyword="遮天",
    sites=["b520", "n23qb"],
    limit=20,
    per_site_limit=5,
)

for item in results:
    print(f"[{item['site']}] {item['title']} by {item['author']} (ID: {item['book_id']})")
```

### 返回类型

```python
class SearchResult(TypedDict, total=True):
    site: str        # 站点键, 如 'b520'
    book_id: str     # 书籍在该站点中的唯一 ID
    title: str       # 小说标题
    author: str      # 作者
    priority: int    # 检索优先级, 值越小优先级越高
```

函数返回 `list[SearchResult]`, 按 `priority` 升序排列
