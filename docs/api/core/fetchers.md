## Fetchers

### 目录

- [Fetchers](#fetchers)
  - [目录](#目录)
  - [导入方式](#导入方式)
  - [使用示例](#使用示例)
  - [FetcherProtocol 接口](#fetcherprotocol-接口)

---

### 导入方式

```python
from novel_downloader.core.fetchers import QidianSession
```

描述: 直接导入具体站点的 Fetcher 类

示例:

```python
fetcher = QidianSession(fetcher_cfg)
```

---

```python
from novel_downloader.core import get_fetcher
```

描述: 根据站点名称和 `FetcherConfig` 获取对应 Fetcher 实例

参数:

* `site`: 站点名称, 如 `"qidian"`
* `config`: `FetcherConfig` 配置对象

返回:

* `FetcherProtocol` 实例

示例:

```python
fetcher = get_fetcher("qidian", fetcher_cfg)
```

---

### 使用示例

```python
async with get_fetcher(site, fetcher_cfg) as fetcher:
    # await fetcher.load_state()
    # 需要登录时:
    # 根据 fetcher.login_fields 填写参数并调用 login
    await fetcher.login(username, password)

    # 获取图书信息页面 (可能多页)
    pages = await fetcher.get_book_info(book_id)

    # 获取单个章节内容 (可能多页)
    chapter_pages = await fetcher.get_book_chapter(book_id, chapter_id)

    # 完成后可保存会话状态
    await fetcher.save_state()
```

---

### FetcherProtocol 接口

> `novel_downloader.core.FetcherProtocol`

```python
async def login(
    self,
    username: str = "",
    password: str = "",
    cookies: dict[str, str] | None = None,
    attempt: int = 1,
    **kwargs: Any,
) -> bool:
```

描述: 异步登录操作

参数:

* `username`: 用户名
* `password`: 密码
* `cookies`: 可选 Cookie 字典
* `attempt`: 当前重试次数

返回:

* `bool`, 登录是否成功

示例:

```python
success = await fetcher.login(username="user", password="pass")
```

---

```python
async def get_book_info(
    self,
    book_id: str,
    **kwargs: Any,
) -> list[str]:
```

描述: 获取图书信息页面原始内容 (支持多页)

参数:

* `book_id`: 图书标识

返回:

* `list[str]`, 页面内容列表

示例:

```python
info_pages = await fetcher.get_book_info("1030412702")
```

---

```python
async def get_book_chapter(
    self,
    book_id: str,
    chapter_id: str,
    **kwargs: Any,
) -> list[str]:
```

描述: 获取单章节原始内容 (支持多页)

参数:

* `book_id`: 图书标识
* `chapter_id`: 章节标识

返回:

* `list[str]`, 章节内容列表

示例:

```python
chap_pages = await fetcher.get_book_chapter("1030412702", "77882211")
```

---

```python
async def get_bookcase(
    self,
    **kwargs: Any,
) -> list[str]:
```

描述: 可选接口, 获取用户书架页面内容

返回:

* `list[str]`, 书架页面内容列表

示例:

```python
bookcase = await fetcher.get_bookcase()
```

---

```python
async def init(
    self,
    **kwargs: Any,
) -> None:
```

描述: 异步初始化, 启动浏览器或会话等准备工作

示例:

```python
await fetcher.init()
```

---

```python
async def close(self) -> None:
```

描述: 异步清理, 关闭浏览器或会话

示例:

```python
await fetcher.close()
```

---

```python
async def load_state(self) -> bool:
```

描述: 恢复持久化会话状态

返回:

* `bool`, 恢复是否成功

示例:

```python
restored = await fetcher.load_state()
```

---

```python
async def save_state(self) -> bool:
```

描述: 保存当前会话状态

返回:

* `bool`, 保存是否成功

示例:

```python
saved = await fetcher.save_state()
```

---

```python
async def set_interactive_mode(
    self,
    enable: bool,
) -> bool:
```

描述: 启用或禁用交互模式, 供手动登录

参数:

* `enable`: `True` 启用, `False` 禁用

返回:

* `bool`, 操作是否成功

示例:

```python
await fetcher.set_interactive_mode(True)
```

---

```python
@property
def is_logged_in(self) -> bool:
```

描述: 当前是否已登录验证

返回:

* `bool`

示例:

```python
if fetcher.is_logged_in:
    ...
```

---

```python
@property
def login_fields(self) -> list[LoginField]:
```

描述: 登录所需字段列表, 用于动态填充登录表单

返回:

* `list[LoginField]`

示例:

```python
fields = fetcher.login_fields
```

---

```python
async def __aenter__(self) -> Self:
```

描述: 上下文进入方法, 自动调用 `init()`

示例:

```python
async with fetcher:
    ...
```

---

```python
async def __aexit__(
    self,
    exc_type: type[BaseException] | None,
    exc_val: BaseException | None,
    tb: types.TracebackType | None,
) -> None:
```

描述: 上下文退出方法, 自动调用 `close()`

示例:

```python
# 在 async with 块结束后自动执行
```
