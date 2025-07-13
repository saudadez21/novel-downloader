## 通用工具函数

### 目录

- [通用工具函数](#通用工具函数)
  - [目录](#目录)
  - [文件工具](#文件工具)
  - [OCR 工具](#ocr-工具)
  - [时间工具](#时间工具)
  - [章节存储](#章节存储)
  - [Cookies 工具](#cookies-工具)
  - [加密/解密工具](#加密解密工具)
  - [网络工具](#网络工具)

### 文件工具

> `novel_downloader.utils.file_utils`

---

```python
def read_binary_file(filepath: str | Path) -> Optional[bytes]:
```

描述: 读取二进制文件内容

参数:

* `filepath`: 文件路径

返回:

* `Optional[bytes]`，文件内容或 `None`

示例:

```python
data = read_binary_file(Path("example.bin"))
```

---

```python
def read_text_file(filepath: str | Path, encoding: str = "utf-8") -> Optional[str]:
```

描述: 读取文本文件并按指定编码返回字符串

参数:

* `filepath`: 文件路径
* `encoding`: 文本编码，默认 `"utf-8"`

返回:

* `Optional[str]`

示例:

```python
text = read_text_file("example.txt")
```

---

```python
def read_json_file(filepath: str | Path, encoding: str = "utf-8") -> Optional[Any]:
```

描述: 读取并解析 JSON 文件

参数:

* `filepath`: 文件路径
* `encoding`: 文本编码，默认 `"utf-8"`

返回:

* `Optional[Any]`，解析后的对象或 `None`

示例:

```python
config = read_json_file("config.json")
```

---

```python
def save_as_json(
    content: str,
    filepath: str | Path,
    *,
    encoding: str = "utf-8",
    on_exist: Literal["overwrite", "skip", "rename"] = "overwrite",
) -> bool:
```

描述: 将对象序列化为 JSON 并保存

参数:

* `content`: 待保存对象
* `filepath`: 目标路径
* `encoding`: 文件编码，默认 `"utf-8"`
* `on_exist`: 冲突处理，`"overwrite"`/`"skip"`/`"rename"`

返回:

* `bool`，操作是否成功

示例:

```python
ok = save_as_json(data, "data.json", on_exist="rename")
```

---

```python
def save_as_txt(
    content: Any,
    filepath: str | Path,
    *,
    encoding: str = "utf-8",
    on_exist: Literal["overwrite", "skip", "rename"] = "overwrite",
) -> bool:
```

描述: 将内容保存为文本文件

参数: 同 `save_as_json`

返回:

* `bool`

示例:

```python
ok = save_as_txt("Hello World", "greeting.txt")
```

### OCR 工具

> `novel_downloader.utils.fontocr`

---

```python
class FontOCR:
    def query(
        self,
        images: Image.Image | list[Image.Image],
        top_k: int = 3,
    ) -> list[tuple[str, float]] | list[list[tuple[str, float]]]:
```

描述: 对图像执行 OCR + 嵌入匹配，返回高于阈值字符及分数

参数:

* `images`: 单张或多张 `PIL.Image.Image`
* `top_k`: 每张图返回最高候选数，默认 `3`

返回:

* 单图时 `list[tuple[str, float]]`
* 多图时 `list[list[tuple[str, float]]]`

示例:

```python
ocr = FontOCR(...)
result = ocr.query([img1, img2], top_k=5)
```

### 时间工具

> `novel_downloader.utils.time_utils`

---

```python
def calculate_time_difference(
    from_time_str: str,
    tz_str: str = "UTC",
    to_time_str: str | None = None,
    to_tz_str: str = "UTC",
) -> tuple[int, int, int, int]:
```

描述: 计算两个时区日期时间之间的差异

参数:

* `from_time_str`: 起始时间，格式 `"YYYY-MM-DD HH:MM:SS"`
* `tz_str`: 起始时区，默认 `"UTC"`
* `to_time_str`: 结束时间；`None` 则使用当前
* `to_tz_str`: 结束时区，默认 `"UTC"`

返回:

* `tuple(day, hour, minute, second)`

示例:

```python
d, h, m, s = calculate_time_difference("2025-06-01 00:00:00", "UTC+8")
```

---

```python
def sleep_with_random_delay(
    base: float,
    *,
    add_spread: float = 0.0,
    mul_spread: float = 1.0,
    max_sleep: float | None = None,
) -> None:
```

描述: 同步随机抖动休眠

参数:

* `base`: 基础时长（秒）
* `add_spread`: 最大加性抖动
* `mul_spread`: 最大乘性因子
* `max_sleep`: 上限时长

示例:

```python
sleep_with_random_delay(2.0, add_spread=0.5, mul_spread=1.5)
```

---

```python
async def async_sleep_with_random_delay(
    base: float,
    *,
    add_spread: float = 0.0,
    mul_spread: float = 1.0,
    max_sleep: float | None = None,
) -> None:
```

描述: 异步版随机抖动休眠

参数: 同上

示例:

```python
await async_sleep_with_random_delay(3.0, mul_spread=1.1, max_sleep=5.0)
```

### 章节存储

> `novel_downloader.utils.chapter_storage`

---

```python
class ChapterStorage:
    def __init__(self, raw_base: Path, namespace: str, backend_type: str = "json"):
```

描述: 初始化存储，可选 JSON 或 SQLite 后端

参数:

* `raw_base`: 存储根路径
* `namespace`: 名称空间
* `backend_type`: `"json"`/`"sqlite"`

示例:

```python
storage = ChapterStorage(Path("./data/book123/"), "chapters", backend_type="json")
```

---

```python
    def exists(self, chap_id: str) -> bool:
```

描述: 检查章节是否存在

参数:

* `chap_id`: 章节 ID

返回:

* `bool`

示例:

```python
exists = storage.exists("77882211")
```

---

```python
    def get(self, chap_id: str) -> ChapterDict | dict[str, Any]:
```

描述: 获取章节数据

参数:

* `chap_id`: 章节 ID

返回:

* `ChapterDict` 或 空字典

示例:

```python
data = storage.get("77882211")
```

---

```python
    def save(
        self,
        data: ChapterDict,
        on_exist: SaveMode = "overwrite",
    ) -> None:
```

描述: 保存章节记录

参数:

* `data`: 章节数据
* `on_exist`: 冲突策略

示例:

```python
storage.save({"id": "77882211", "title": "第1章", "content": "...", "extra": {}}, on_exist="overwrite")
```

### Cookies 工具

> `novel_downloader.utils.cookies`

---

```python
def resolve_cookies(cookies: str | Mapping[str, str]) -> dict[str, str]:
```

描述: 解析 Cookie 字符串或映射为标准字典

参数:

* `cookies`: Cookie 字符串或字典

返回:

* `dict[str, str]`

示例:

```python
ck = resolve_cookies("k1=v1; k2=v2")
```

### 加密/解密工具

> `novel_downloader.utils.crypto_utils`

---

```python
def rc4_crypt(
    key: str,
    data: str,
    *,
    mode: str = "encrypt",
    encoding: str = "utf-8",
) -> str:
```

描述: RC4 加/解密并 Base64 编码/解码

参数:

* `key`: 密钥
* `data`: 明文或 Base64 密文
* `mode`: `"encrypt"`/`"decrypt"`
* `encoding`: 编码

返回:

* `str`

示例:

```python
cipher = rc4_crypt("secret", "hello", mode="encrypt")
plain = rc4_crypt("secret", cipher, mode="decrypt")
```

### 网络工具

> `novel_downloader.utils.network`

---

```python
def download(
    url: str,
    target_dir: str | Path | None = None,
    filename: str | None = None,
    *,
    timeout: int = 10,
    retries: int = 3,
    backoff: float = 0.5,
    headers: dict[str, str] | None = None,
    stream: bool = False,
    on_exist: Literal["overwrite", "skip", "rename"] = "overwrite",
    default_suffix: str = "",
    chunk_size: int = _DEFAULT_CHUNK_SIZE,
) -> Path | None:
```

描述: 下载文件并保存

参数:

* `url`: 链接
* `target_dir`: 保存目录
* `filename`: 文件名
* `timeout`, `retries`, `backoff`, `headers`, `on_exist`

返回:

* `Path` 或 `None`

示例:

```python
img_path = download("https://.../img.png", Path("./imgs"))
font_path = download("https://.../font.ttf", Path("./fonts"))
js_path = download("https://.../script.js", Path("./js"))
```
