## 通用工具函数

### 目录

- [通用工具函数](#通用工具函数)
  - [目录](#目录)
  - [OCR 工具](#ocr-工具)
  - [时间工具](#时间工具)
  - [章节存储](#章节存储)
  - [Cookies 工具](#cookies-工具)
  - [加密/解密工具](#加密解密工具)
  - [网络工具](#网络工具)

### OCR 工具

> `novel_downloader.utils.fontocr`

---

```python
class FontOCR:
    def predict(
        self,
        images: list[np.ndarray],
        top_k: int = 1,
    ) -> list[list[tuple[str, float]]]:
        """
        Run OCR on input images.

        :param images: list of np.ndarray objects to predict
        :param top_k: number of top candidates to return per image
        :return: list of lists containing (character, score)
        """

    @staticmethod
    def render_char_image_array(
        char: str,
        render_font: ImageFont.FreeTypeFont,
        is_reflect: bool = False,
        size: int = 64,
    ) -> np.ndarray | None:
        """
        Render a single character into an RGB square image.

        :param char: character to render
        :param render_font: FreeTypeFont instance to render with
        :param is_reflect: if True, flip the image horizontally
        :param size: output image size (width and height in pixels)
        :return: rendered image as np.ndarray in RGB or None if blank
        """
```

描述: 对图像执行 OCR，返回高于阈值字符及分数

示例:

```python
from PIL import ImageFont
from novel_downloader.utils.fontocr import FontOCR

CHAR_IMAGE_SIZE = 64
CHAR_FONT_SIZE = 52

sample_chars = ["你", "好"]
font_path = "./sample.woff2"
font = ImageFont.truetype(font_path, CHAR_FONT_SIZE)
ocr = FontOCR()

imgs = []
for ch in sample_chars:
    img = ocr.render_char_image_array(ch, font, reflect)
    if img is not None:
        out.append(img)

result = ocr.predict(imgs)
print(result)
```

### 时间工具

> `novel_downloader.utils.time_utils`

---

```python
def time_diff(
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
d, h, m, s = time_diff("2025-06-01 00:00:00", "UTC+8")
```

---

```python
def jitter_sleep(
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
jitter_sleep(2.0, add_spread=0.5, mul_spread=1.5)
```

---

```python
async def async_jitter_sleep(
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
await async_jitter_sleep(3.0, mul_spread=1.1, max_sleep=5.0)
```

### 章节存储

> `novel_downloader.utils.ChapterStorage`

---

```python
class ChapterStorage:
    def __init__(self, raw_base: Path | str, priorities: dict[int, int]) -> None:
```

**描述**
初始化章节存储, 使用 SQLite 数据库, 支持根据不同 `source_id` 的优先级保留最优版本。

**参数**

* `raw_base`: 存储根目录 (数据库文件将写入 `<raw_base>/chapter_data.sqlite`)
* `priorities`: 源 ID 到优先级的映射, 数值越低代表优先级越高。例如：`{0: 10, 1: 100}`

**示例**

```python
storage = ChapterStorage("./data/book123", {0: 10, 1: 20})
storage.connect()
```

---

```python
def connect(self) -> None:
```

**描述**
打开并初始化 SQLite 连接, 创建表和索引, 并缓存已有 `(chapter_id, source_id)` 键。

---

```python
def exists(self, chap_id: str, source_id: int | None = None) -> bool:
```

**描述**
检查章节是否存在。

**参数**

* `chap_id`: 章节 ID
* `source_id` (可选): 指定源 ID 则检查该源; 否则检查任意源是否存在

**返回**

* `bool`

**示例**

```python
storage.connect()
exists_any = storage.exists("77882211")
exists_src0 = storage.exists("77882211", source_id=0)
```

---

```python
def upsert_chapter(self, data: ChapterDict, source_id: int) -> None:
```

**描述**
插入或更新单个章节记录。

**参数**

* `data`: 包含 `id`, `title`, `content`, `extra` 的 `ChapterDict`
* `source_id`: 整数型源 ID

**示例**

```python
storage.upsert_chapter(
    {"id":"77882211","title":"第1章","content":"...","extra":{}},
    source_id=0
)
```

---

```python
def upsert_chapters(self, data: list[ChapterDict], source_id: int) -> None:
```

**描述**
批量插入或更新多个章节。

**参数**

* `data`: `ChapterDict` 列表
* `source_id`: 整数型源 ID

**示例**

```python
batch = [
    {"id":"77882211",...},
    {"id":"77882212",...},
]
storage.upsert_chapters(batch, source_id=0)
```

---

```python
def get_chapter(self, chap_id: str, source_id: int) -> ChapterDict | None:
```

**描述**
根据指定 `chap_id` 和 `source_id` 获取单个章节。

**参数**

* `chap_id`: 章节 ID
* `source_id`: 源 ID

**返回**

* `ChapterDict` 或 `None`

**示例**

```python
data = storage.get_chapter("77882211", source_id=0)
```

---

```python
def get_chapters(self, chap_ids: list[str], source_id: int) -> dict[str, ChapterDict | None]:
```

**描述**
批量获取同一源下的多个章节。

**参数**

* `chap_ids`: 章节 ID 列表
* `source_id`: 源 ID

**返回**

* 映射每个 `chap_id` 到 `ChapterDict` 或 `None`

**示例**

```python
chap_map = storage.get_chapters(["77882211","77882212"], source_id=0)
```

---

```python
def get_best_chapter(self, chap_id: str) -> ChapterDict | None:
```

**描述**
从所有源中按优先级选出给定 `chap_id` 的最佳章节。

**参数**

* `chap_id`: 章节 ID

**返回**

* `ChapterDict` 或 `None`

**示例**

```python
best = storage.get_best_chapter("77882211")
```

---

```python
def get_best_chapters(self, chap_ids: list[str]) -> dict[str, ChapterDict | None]:
```

**描述**
批量获取多个章节的最佳版本 (按优先级选出) 。

**参数**

* `chap_ids`: 章节 ID 列表

**返回**

* 映射每个 `chap_id` 到 `ChapterDict` 或 `None`

**示例**

```python
best_map = storage.get_best_chapters(["77882211","77882212"])
```

---

```python
def count(self) -> int:
```

**描述**
返回已存储的章节总数。

**示例**

```python
total = storage.count()
```

---

```python
def close(self) -> None:
```

**描述**
关闭数据库连接并清空缓存的键。

**示例**

```python
storage.close()
```

### Cookies 工具

> `novel_downloader.utils.cookies`

---

```python
def parse_cookies(cookies: str | Mapping[str, str]) -> dict[str, str]:
```

描述: 解析 Cookie 字符串或映射为标准字典

参数:

* `cookies`: Cookie 字符串或字典

返回:

* `dict[str, str]`

示例:

```python
ck = parse_cookies("k1=v1; k2=v2")
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
