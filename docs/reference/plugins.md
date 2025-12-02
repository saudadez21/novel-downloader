## 插件系统 (Plugins)

支持通过插件扩展 (或覆盖) 新的**站点**、**文本处理器 (processors)**、**客户端 (clients)**。

插件可放在本地目录中启用, 也可选择是否覆盖内置实现。

### 在 `settings.toml` 中启用

```toml
[plugins]
# 是否启用本地插件目录
enable_local_plugins = true
# 是否允许本地插件覆盖内置实现
override_builtins = false
# 本地插件路径 (可选)
local_plugins_path = "./novel_plugins"
```

### 目录结构

```text
.
├─ settings.toml
└─ novel_plugins
   ├─ sites
   │  └─ ciweimao            # 示例: 站点键 (site_key), 即 --site 的值
   │     ├─ fetcher.py       # 必需: 实现会话类 (如 CiweimaoFetcher)
   │     ├─ parser.py        # 必需: 实现解析类 (如 CiweimaoParser)
   │     ├─ searcher.py      # 可选: 用于站内搜索
   │     └─ client.py        # 可选: 不提供则使用通用 CommonClient
   └─ processors
      └─ processor_a.py      # 自定义文本处理器, 名称在 settings.toml 的 processors.name 中引用
```

> `sites/<site_key>/` 中的 `<site_key>` 即命令行 `--site` 的值, 例如:
>
> `novel-cli download --site ciweimao 123456`

---

### 扩展一个站点

一个站点通常包含两个必要组件: **Fetcher** (抓取页面) 与 **Parser** (解析页面)

可选组件: **Searcher** (站内搜索) 、**Client** (覆盖默认下载/导出流程)

#### 1. Fetcher (抓取)

* 职责: 登录、抓取 **书籍信息页** 与 **章节页** (可能为多页)
* 建议继承: `BaseFetcher` 或更高层的 `GenericFetcher`
* 注册: 使用装饰器 `@registrar.register_fetcher()`

##### Fetcher 协议 (精简)

```python
class FetcherProtocol(Protocol):
    site_name: str

    async def login(
        self,
        username: str = "",
        password: str = "",
        cookies: dict[str, str] | None = None,
        attempt: int = 1,
        **kwargs: Any,
    ) -> bool: ...
    async def fetch_book_info(self, book_id: str, **kwargs: Any) -> list[str]: ...
    async def fetch_chapter_content(self, book_id: str, chapter_id: str, **kwargs: Any) -> list[str]: ...

    @property
    def is_logged_in(self) -> bool: ...
    @property
    def login_fields(self) -> list[LoginField]: ...
```

需要登录的站点可提供交互字段:

```python
@dataclass
class LoginField:
    name: str
    label: str
    type: Literal["text", "password", "cookie"]
    required: bool
    default: str = ""
    placeholder: str = ""
    description: str = ""
```

##### 继承 `BaseFetcher` (自定义 URL 的简单站点)

```python
from typing import Any
from novel_downloader.plugins.base.fetcher import BaseFetcher
from novel_downloader.plugins.registry import registrar

@registrar.register_fetcher()
class B520Fetcher(BaseFetcher):
    site_name: str = "b520"

    BOOK_INFO_URL = "http://www.b520.cc/{book_id}/"
    CHAPTER_URL   = "http://www.b520.cc/{book_id}/{chapter_id}.html"

    async def fetch_book_info(self, book_id: str, **kwargs: Any) -> list[str]:
        url = self.BOOK_INFO_URL.format(book_id=book_id)
        return [await self.fetch(url, headers={"Referer": "http://www.b520.cc/"})]

    async def fetch_chapter_content(self, book_id: str, chapter_id: str, **kwargs: Any) -> list[str]:
        url = self.CHAPTER_URL.format(book_id=book_id, chapter_id=chapter_id)
        return [await self.fetch(url, headers={"Referer": "http://www.b520.cc/"}, encoding="gbk")]
```

##### 继承 `GenericFetcher` (模板 URL / 分页内置支持)

**单页信息 + 单页章节**

```python
from novel_downloader.plugins.base.fetcher import GenericFetcher
from novel_downloader.plugins.registry import registrar

@registrar.register_fetcher()
class BiquyueduFetcher(GenericFetcher):
    site_name: str = "biquyuedu"
    BOOK_INFO_URL = "https://biquyuedu.com/novel/{book_id}.html"
    CHAPTER_URL   = "https://biquyuedu.com/novel/{book_id}/{chapter_id}.html"
```

**信息/章节为多页**

```python
from novel_downloader.plugins.base.fetcher import GenericFetcher
from novel_downloader.plugins.registry import registrar

@registrar.register_fetcher()
class Biquge5Fetcher(GenericFetcher):
    site_name: str = "biquge5"
    BASE_URL = "https://www.biquge5.com"

    USE_PAGINATED_INFO = True
    USE_PAGINATED_CHAPTER = True

    @classmethod
    def relative_info_url(cls, book_id: str, idx: int) -> str:
        return f"/{book_id}/index_{idx}.html" if idx > 1 else f"/{book_id}/"

    @classmethod
    def relative_chapter_url(cls, book_id: str, chapter_id: str, idx: int) -> str:
        return f"/{book_id}/{chapter_id}_{idx}.html" if idx > 1 else f"/{book_id}/{chapter_id}.html"
```

**信息页和目录页分离**

```python
from novel_downloader.plugins.base.fetcher import GenericFetcher
from novel_downloader.plugins.registry import registrar

@registrar.register_fetcher()
class I25zwFetcher(GenericFetcher):
    site_name: str = "i25zw"

    HAS_SEPARATE_CATALOG = True
    BOOK_INFO_URL    = "https://www.i25zw.com/book/{book_id}.html"
    BOOK_CATALOG_URL = "https://www.i25zw.com/{book_id}/"
    CHAPTER_URL      = "https://www.i25zw.com/{book_id}/{chapter_id}.html"
```

> `GenericFetcher` 还提供分页钩子 `should_continue_pagination(...)`、相对路径拼接等通用逻辑, 便于快速适配。

---

#### 2. Parser (解析)

* 职责: 将原始 HTML 列表解析为**书籍元信息** (含卷/章列表) 与**章节正文**
* 建议继承: `BaseParser`
* 注册: `@registrar.register_parser()`

##### Parser 协议 (精简)

```python
class ParserProtocol(Protocol):
    def parse_book_info(
        self,
        raw_pages: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None: ...
    def parse_chapter_content(
        self,
        raw_pages: list[str],
        chapter_id: str,
        **kwargs: Any,
    ) -> ChapterDict | None: ...
```

**数据结构:**

```python
class ChapterDict(TypedDict):
    id: str
    title: str
    content: str
    extra: dict[str, Any]

class ChapterInfoDict(TypedDict):
    title: str
    url: str
    chapterId: str
    accessible: NotRequired[bool]

class VolumeInfoDict(TypedDict):
    volume_name: str
    chapters: list[ChapterInfoDict]

class BookInfoDict(TypedDict):
    book_name: str
    author: str
    cover_url: str
    update_time: str
    summary: str
    extra: dict[str, Any]
    volumes: list[VolumeInfoDict]
    tags: NotRequired[list[str]]
    word_count: NotRequired[str]
    serial_status: NotRequired[str]
    summary_brief: NotRequired[str]
```

##### 解析示例

```python
from typing import Any
from lxml import html
from novel_downloader.plugins.base.parser import BaseParser
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import BookInfoDict, ChapterDict, ChapterInfoDict, VolumeInfoDict

@registrar.register_parser()
class AaatxtParser(BaseParser):
    site_name: str = "aaatxt"

    def parse_book_info(self, raw_pages: list[str], **kwargs: Any) -> BookInfoDict | None:
        if not raw_pages:
            return None

        tree = html.fromstring(raw_pages[0])
        book_name = self._first_str(tree.xpath("//div[@class='xiazai']/h1/text()"))
        author    = self._first_str(tree.xpath("//span[@id='author']/a/text()"))
        cover_url = self._first_str(tree.xpath("//div[@id='txtbook']//div[@class='fm']//img/@src"))
        update_time = self._first_str(tree.xpath("//div[@id='txtbook']//li[contains(text(), '上传日期')]/text()"),
                                      replaces=[("上传日期:", "")])
        summary  = self._first_str(tree.xpath("//div[@id='jj']//p/text()"))
        download_url = self._first_str(tree.xpath("//div[@id='down']//li[@class='bd']//a/@href"))

        chapters: list[ChapterInfoDict] = []
        for a in tree.xpath("//div[@id='ml']//ol/li/a"):
            url = a.get("href", "").strip()
            chapter_id = url.split("/")[-1].replace(".html", "")
            title = a.text_content().strip()
            chapters.append({"title": title, "url": url, "chapterId": chapter_id})

        volumes: list[VolumeInfoDict] = [{"volume_name": "正文", "chapters": chapters}]
        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "update_time": update_time,
            "summary": summary,
            "volumes": volumes,
            "extra": {"download_url": download_url},
        }

    def parse_chapter_content(self, raw_pages: list[str], chapter_id: str, **kwargs: Any) -> ChapterDict | None:
        if not raw_pages:
            return None
        tree = html.fromstring(raw_pages[0])
        raw_title = self._first_str(tree.xpath("//div[@id='content']//h1/text()"))
        title = raw_title.split("-", 1)[-1].strip()

        paragraphs = []
        for txt in tree.xpath("//div[@class='chapter']//text()"):
            line = txt.strip()
            if not line or self._is_ad_line(txt):
                continue
            paragraphs.append(line)

        if not paragraphs:
            return None

        content = "\n".join(paragraphs)

        return {"id": chapter_id, "title": title, "content": content, "extra": {"site": self.site_name}}
```

---

#### 3. Searcher (可选)

* 职责: 站内搜索, 返回 `SearchResult` 列表
* 继承: `BaseSearcher`
* 注册: `@registrar.register_searcher()`

##### Searcher 示例

```python
import logging
from lxml import html
from novel_downloader.plugins.base.searcher import BaseSearcher
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import SearchResult

logger = logging.getLogger(__name__)

@registrar.register_searcher()
class B520Searcher(BaseSearcher):
    site_name = "b520"
    priority  = 30
    BASE_URL  = "http://www.b520.cc/"
    SEARCH_URL = "http://www.b520.cc/modules/article/search.php"

    async def _fetch_html(self, keyword: str) -> str:
        try:
            async with self.session.get(self.SEARCH_URL, params={"searchkey": keyword},
                                      headers={"Referer": "http://www.b520.cc/"}) as resp:
                resp.raise_for_status()
                return await self._response_to_str(resp)
        except Exception:
            logger.error("Failed to fetch HTML for keyword '%s' from '%s'", keyword, self.SEARCH_URL)
            return ""

    def _parse_html(self, html_str: str, limit: int | None = None) -> list[SearchResult]:
        doc = html.fromstring(html_str)
        rows = doc.xpath('//table[@class="grid"]//tr[position()>1]')
        results: list[SearchResult] = []
        for idx, row in enumerate(rows):
            href = self._first_str(row.xpath(".//td[1]/a[1]/@href"))
            if not href:
                continue
            if limit is not None and idx >= limit:
                break

            book_id = href.strip("/").split("/")[-1]
            book_url = self._abs_url(href)
            title = self._first_str(row.xpath(".//td[1]/a[1]/text()"))
            latest_chapter = self._first_str(row.xpath(".//td[2]/a[1]/text()")) or "-"
            author = self._first_str(row.xpath(".//td[3]//text()"))
            word_count = self._first_str(row.xpath(".//td[4]//text()"))
            update_date = self._first_str(row.xpath(".//td[5]//text()"))

            results.append(SearchResult(
                site=self.site_name,
                book_id=book_id,
                book_url=book_url,
                cover_url="",
                title=title,
                author=author,
                latest_chapter=latest_chapter,
                update_date=update_date,
                word_count=word_count,
                priority=self.priority + idx,
            ))
        return results
```

---

### 扩展文本处理器 (Processors)

* 职责: 在导出前对 **书籍元信息** 与 **章节** 进行变换
* 协议: `ProcessorProtocol`
* 注册: `@registrar.register_processor()`

```python
class ProcessorProtocol(Protocol):
    def __init__(self, config: dict[str, Any]) -> None: ...
    def process_book_info(self, book_info: BookInfoDict) -> BookInfoDict: ...
    def process_chapter(self, chapter: ChapterDict) -> ChapterDict: ...
```

**配置传入规则**

在 `settings.toml` 中:

```toml
[[general.processors]]
name = "cleaner"
overwrite = false
config_1 = true
config_2 = 2
config_3 = "three"
```

则处理器构造器 `__init__(config)` 收到:

```json
{
  "config_1": true,
  "config_2": 2,
  "config_3": "three"
}
```

> 现有内置处理器文档: 见 `docs/3-settings-schema.md#processors-配置`
> 包括 `cleaner` (正则/替换) 、`zh_convert` (OpenCC 简繁转换) 、`corrector` (pycorrector 纠错, 效果因模型而异)。

---

### 注册机制

插件通过**装饰器注册**, 导入模块时自动完成登记, 无需手动导表/清单:

* 站点会话：`@registrar.register_fetcher()`
* 站点解析器：`@registrar.register_parser()`
* 站点搜索器：`@registrar.register_searcher()`
* 站点客户端：`@registrar.get_client()`
* 文本处理器：`@registrar.register_processor()`

#### 1. 关键名如何确定

注册器会根据插件模块的路径自动推导出唯一键名 (key), 用来在运行时定位插件。

**站点类插件 (Fetcher / Parser / Client / Searcher)**

键名来源于模块路径中的:

```
sites.<site_key>.<kind>
```

例如以下结构:

```
novel_plugins/
└── sites/
    └── ciweimao/
        ├── fetcher.py
        ├── parser.py
        └── searcher.py
```

对应的站点键名为:

```
ciweimao
```

命令行即可直接使用该键:

```bash
novel-cli download --site ciweimao 123456
```

> 站点键名始终自动转换为小写; 若以数字开头, 请加前缀 `n` (如 `123abc` -> `n123abc`)

**文本处理器 (Processor)**

键名来源于模块路径中 `processors.` 之后的部分。

例如模块:

```
novel_downloader.plugins.processors.cleaner
```

自动推导键名:

```
cleaner
```

在配置文件中可直接引用:

```toml
[[general.processors]]
name = "cleaner"
```

如果处理器使用了子包，例如:

```
novel_plugins/processors/text/zh_convert.py
```

则键名为:

```
text.zh_convert
```

#### 2. 搜索/加载顺序与覆盖关系

注册表会按 "命名空间" 顺序尝试导入模块 (懒加载):

1. 内置命名空间: `novel_downloader.plugins`
2.  (可选) 本地命名空间: 默认 `novel_plugins`, 由 `settings.toml` 中 `[plugins]` 控制

配置文件里:

* `enable_local_plugins = true` 开启本地插件
* `local_plugins_path = "./novel_plugins"` 指定目录
* `override_builtins = true` 时, 本地命名空间将**排在内置之前**, 可覆盖同名实现

> 站点模块的动态导入路径: `{namespace}.sites.<site_key>.<kind>`
>
> 处理器模块的动态导入路径: `{namespace}.processors.<name>`

---

#### 3. 获取与回退策略

* `get_client(site)`: 未找到站点专属实现时, 自动回退到 **通用实现** (`CommonClient`)
* `get_fetcher(site)` / `get_parser(site)`: 未找到会抛 `ValueError("Unsupported site")`
* `get_processor(name)`: 未找到会抛 `ValueError("Unsupported processor")`
* `get_searcher_class(site)`: 未找到会抛 `ValueError("Unsupported site")`
* `get_searcher_classes()`: 在未指定站点时, 会尝试加载所有已知站点的 `searcher` 模块并返回可用列表

> 所有注册均在**模块被导入时**生效, 请确保插件文件能被 Python 导入 (路径正确、无语法错误)
