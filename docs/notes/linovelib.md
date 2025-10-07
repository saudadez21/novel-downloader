# 哔哩轻小说 (linovelib) 分析笔记

创建日期: 2025/05/25

修改日期: 2025/10/06

## 2025/08 ~ ??? 混淆逻辑

### 一、`pctheme.js` 的正则替换映射

`pctheme.js` 中包含形如 "链式 `replace(new RegExp(…) , '…')`" 的批量替换，约 100 对。

例如:

```js
eval(function(p,a,c,k,e,r){e=String;if(!''.replace(/^/,String)){while(c--)r[c]=k[c]||c;k=[function(e){return r[e]}];e=function(){return'\\w+'};c=1};while(c--)if(k[c])p=p.replace(new RegExp('\\b'+e(c)+'\\b','g'),k[c]);return p}('4=4.0(1 2("","3"),"的")...',5,5,'replace|new|RegExp|gi|k'.split('|'),0,{}));
```

解混淆后本质为:

* 对正文文本执行若干 `str.replace(new RegExp(SRC, 'gi'), DST)`
* `SRC` 多为私有区或特殊部件字符 (如 ``)，`DST` 为常用汉字 (如 `的`)

示例:

```js
k = k
  .replace(new RegExp("", "gi"), "的")
  .replace(new RegExp("", "gi"), "一")
  .replace(new RegExp("", "gi"), "是")
  .replace(new RegExp("", "gi"), "了")
  .replace(new RegExp("", "gi"), "我")
  .replace(new RegExp("", "gi"), "不")
  .replace(new RegExp("", "gi"), "人")
  .replace(new RegExp("", "gi"), "在")
  .replace(new RegExp("", "gi"), "他")
  .replace(new RegExp("", "gi"), "有")
  .replace(new RegExp("", "gi"), "这");
```

处理方法:

解析 `pctheme.js` 文本，正则匹配 `new RegExp\(["'](.+?)["'],"gi"\)\s*,\s*["'](.+?)["']` 收集为 `map[SRC] = DST` 并保存为 json。

参考还原 (Python):

```python
import json
from pathlib import Path

LINOVELIB_MAP_PATH = Path("/path/to/map.json")
_PCTHEMA_MAP: dict[str, str] = json.loads(
    LINOVELIB_MAP_PATH.read_text(encoding="utf-8")
)

def _map_subst(text: str) -> str:
    """
    Apply PC theme character substitution to the input text.
    """
    return "".join(_PCTHEMA_MAP.get(c, c) for c in text)
```

### 二、`chapterlog.js` 的段落打乱与恢复 (Seeded Fisher–Yates)

`chapterlog.js` 使用 [`javascript-obfuscator`](https://github.com/javascript-obfuscator/javascript-obfuscator) 混淆，机制要点:

1. 仅处理 `#TextContent` 下非空 `<p>` 段落。
2. 若段落数 <= 20: 顺序不变。
3. 若段落数 > 20: 前 20 段固定，其余段按章节 ID 派生的种子进行 Fisher–Yates 打乱。
4. 伪随机序列采用线性同余: `s = (s*9302 + 49397) % 233280`，选位 `j = floor(s/233280*(i+1))`。
5. 种子 `seed = chapterId*127 + 235`。

核心逻辑复原如下:

```js
var chapterId = ReadParams.chapterid;
if (!chapterId) return;

var textContainer = document.querySelector("#TextContent");
if (!textContainer) return;

var allNodes = Array.prototype.slice.call(textContainer.childNodes);
var paragraphs = []; // 收集非空 <p>
for (var i = 0; i < allNodes.length; i++) {
  var node = allNodes[i];
  if (node.nodeType === 1 && node.tagName.toLowerCase() === "p" && node.innerHTML.replace(/\s+/g, "").length > 0) {
    paragraphs.push({ node: node, idx: i });
  }
}

var paragraphCount = paragraphs.length;
if (!paragraphCount) return;

function shuffle(array, seed) {
  var len = array.length;
  seed = Number(seed);
  for (var i = len - 1; i > 0; i--) {
    seed = (seed * 9302 + 49397) % 233280;           // 线性同余伪随机
    var j = Math.floor(seed / 233280 * (i + 1));     // Fisher–Yates 选位
    var tmp = array[i]; array[i] = array[j]; array[j] = tmp;
  }
  return array;
}

var seed = Number(chapterId) * 127 + 235;            // 种子派生
var order = [];

if (paragraphCount > 20) {
  var fixed = [], rest = [];
  for (var i = 0; i < paragraphCount; i++) (i < 20 ? fixed : rest).push(i);
  shuffle(rest, seed);
  order = fixed.concat(rest);                        // 前 20 固定，其余打乱
} else {
  for (var i = 0; i < paragraphCount; i++) order.push(i);
}

// 映射
var reordered = [];
for (var i = 0; i < paragraphCount; i++) {
  reordered[order[i]] = paragraphs[i].node;
}
```

参考还原 (Python):

```python
def _chapterlog_order(n: int, cid: int) -> list[int]:
    """
    Compute the paragraph reordering index sequence used by /scripts/chapterlog.js.

    :param n: Total number of non-empty paragraphs in the chapter.
    :param cid: Chapter ID (used as the seed for the shuffle).
    """
    if n <= 0:
        return []
    if n <= 20:
        return list(range(n))

    fixed = list(range(20))
    rest = list(range(20, n))

    # Seeded Fisher-Yates
    m = 233_280
    a = 9_302
    c = 49_397
    s = cid * 127 + 235  # seed
    for i in range(len(rest) - 1, 0, -1):
        s = (s * a + c) % m
        j = (s * (i + 1)) // m
        rest[i], rest[j] = rest[j], rest[i]

    return fixed + rest

def restore_paragraphs(paragraphs: list[str], cid: int) -> list[str]:
    order = _chapterlog_order(len(paragraphs), cid_int)
    reordered_p = [""] * len(paragraphs)
    for i, p in enumerate(paragraphs):
        reordered_p[order[i]] = p
    return reordered_p
```

---

## ??? ~ 2025/08 混淆逻辑

> 说明: 以下为 2025/08 之前的混淆方案，现已被替代。

### 一、混淆脚本与字体注入

部分章节页面包含经混淆压缩的脚本，其作用是动态注入 `@font-face` 并将自定义字体应用到指定段落。还原后的核心逻辑如下:

```js
const sheet = new CSSStyleSheet();
sheet.replaceSync(`
  @font-face {
    font-family: read;
    font-display: block;
    src: url('/public/font/read.woff2') format('woff2'),
         url('/public/font/read.ttf') format('truetype');
  }
  #TextContent p:nth-last-of-type(2) {
    font-family: "read" !important;
  }
`);
document.adoptedStyleSheets = [
  ...document.adoptedStyleSheets,
  sheet
];
```

页面对倒数第二个 `<p>` 应用自定义字体 `read`; 最后一个 `<p>` 恒为空行。与起点的做法相似，但此处字体文件固定，非按请求动态生成。

对应 CSS:

```css
@font-face {
  font-family: read;
  font-display: block;
  src: url('/public/font/read.woff2') format('woff2'),
       url('/public/font/read.ttf') format('truetype');
}
#TextContent p:nth-last-of-type(2) {
  font-family: "read" !important;
}
```

### 二、字体渲染测试

为验证该字体映射情况, 使用 `Pillow` 库对示例字符串进行渲染:

```python
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

CELL_SIZE = 64
FONT_SIZE = 52
FONT_PATH = Path.cwd() / "read.woff2"
TEXT_SAMPLE = "「床瑰蛾妹」"  # 即使与全世界为敌

def render_text(
    text: str,
    font: ImageFont.FreeTypeFont,
    cell_size: int = CELL_SIZE,
    chars_per_line: int = 16,
) -> Image.Image | None:
    """
    Render a string into a image.
    """
    lines = textwrap.wrap(text, width=chars_per_line) or [""]
    img_w = cell_size * chars_per_line
    img_h = cell_size * len(lines)

    img = Image.new("L", (img_w, img_h), color=255)
    draw = ImageDraw.Draw(img)
    for row, line in enumerate(lines):
        for col, ch in enumerate(line):
            x = (col + 0.5) * cell_size
            y = (row + 0.5) * cell_size
            draw.text((x, y), ch, font=font, fill=0, anchor="mm")

    return img

if __name__ == "__main__":
    font = ImageFont.truetype(str(FONT_PATH), FONT_SIZE)
    image = render_text(TEXT_SAMPLE, font)
    image.show()
```

观察可见:

部分字符渲染为空白, 如示例中所示。

页面编码形式通常表现为「两位 PUA 字符 + 一位汉字」的交替组合; 但 `read` 字体未为这些常见汉字嵌入字形，因此渲染为空。

### 三、空字形统计与判定

`read.ttf` 中存在大量 "映射存在但字形为空" 的条目，以 `ttx` 导出可见 (`ttx ./read.ttf`):

* `cmap` 映射到诸如 `glyph07404`
* `hmtx` 中对应 `width=0`
* `glyf` 的 `TTGlyph` 不含轮廓

示例：

```ttx
<hmtx>
  <mtx name="glyph07404" width="0" lsb="0"/>
  <mtx name="glyph07405" width="0" lsb="0"/>
...
<cmap_format_4 ...>
  <map code="0x4e00" name="glyph07404"/>
  <map code="0x4e01" name="glyph07405"/>
...
<TTGlyph name="glyph07404"/><!-- contains no outline data -->
<TTGlyph name="glyph07405"/><!-- contains no outline data -->
```

由此可见，`0x4e00` 和 `0x4e01`（即“ 一 ”、“ 丁 ”）虽在映射表中存在，但对应的字形数据为空，且宽度为 0，渲染时显示为空白。

**判定原则:**

1. `glyf` 中无轮廓
2. `hmtx` 中水平宽度为 0

满足任一条件即可认定为空字形。

示例统计 (基于 `fontTools`):

```python
from fontTools.ttLib import TTFont

def count_blank_glyphs(path: str) -> list[str]:
    font = TTFont(path)
    cmap = font.getBestCmap()
    hmtx_table = font["hmtx"]

    blank_chars: list[str] = []
    for code, glyph_name in cmap.items():
        width, _ = hmtx_table[glyph_name]

        if width == 0:
            blank_chars.append(chr(code))

    return blank_chars

if __name__ == "__main__":
    blanks = count_blank_glyphs("read.ttf")
    print(f"空字形数量: {len(blanks)}")
```

统计结果: 共有 **3500** 个空字形。

### 四、字体还原思路与结果

由于 `read.ttf`/`read.woff2` 地址固定，所有章节复用同一字体，无需逐章 OCR。

字体信息示例:

```
字体名称: MI LANTING
版本: Version 2.3.3;GB Outside YS Regular
TrueType Outlines
```

由此可定位原始字体来源 (如 `MI LANTING`)。

对 `read.ttx` 的 `cmap` 观察可知混淆主要位于 PUA 区间 `0xE000` - `0xF8FE`。

先通过渲染检查是否是混淆的范围 (在此省略)

再测试确认该区间字符数:

```python
def extract_font_charset(
    font_path: str | Path,
    lower_bound: int | None = None,
    upper_bound: int | None = None,
) -> set[str]:
    """
    Extract the set of Unicode characters encoded by a TrueType/OpenType font.

    :param font_path: Path to a TTF/OTF font file.
    :param lower_bound: Inclusive lower bound of code points (e.g. 0x4E00).
    :param upper_bound: Inclusive upper bound of code points (e.g. 0x9FFF).
    :return: A set of Unicode characters present in the font's cmap within the specified range.
    """
    with TTFont(font_path) as font_ttf:
        cmap = font_ttf.getBestCmap() or {}

    charset: set[str] = set()
    for cp in cmap:
        if lower_bound is not None and cp < lower_bound:
            continue
        if upper_bound is not None and cp > upper_bound:
            continue
        charset.add(chr(cp))

    return charset

ENCRYPTED_FROM = 0xE000
ENCRYPTED_TO = 0xF8FE

read_chars = extract_font_charset("read.ttf", ENCRYPTED_FROM, ENCRYPTED_TO)

print(f"共提取到 {len(read_chars)} 个字符")
```

一共 3606 个字符

随后对 `read.ttx` 与 `MI LANTING.ttx` 进行字形级匹配还原。

直接 `O(n×m)` 全量比较在两侧均约 2.7 万字形时成本过高，故采用以下剪枝与加速:

* 仅在 PUA 区间 (`0xE000` - `0xF8FE`) 匹配
* 利用空字形先验: 已知 `read` 中约 3500 个 "空字形" 在原字体中有真实字形，可优先匹配
* 基于字形组件与轮廓构建 **规范化指纹** 并哈希预筛
* 预筛失败再回退全量严格比较
* 未匹配项单独记录，后续人工复核

经优化后，预估耗时由约 8 小时降至约 1 分钟 (环境相关)。

核心脚本:

```python
#!/usr/bin/env python3
from lxml import etree
from lxml.etree import _Element
import hashlib
import json
from pathlib import Path
from functools import lru_cache
from tqdm import tqdm

ENCRYPTED_FROM = 0xE000
ENCRYPTED_TO   = 0xF8FE

def load_ttx_glyphs(ttx_path: str) -> dict[str, _Element]:
    """Load TTGlyph elements: glyphName -> TTGlyph Element"""
    root = etree.parse(ttx_path).getroot()
    glyphs: dict[str, _Element] = {}
    for g in root.findall(".//TTGlyph"):
        name = g.get("name")
        if name:
            glyphs[name] = g
    return glyphs

def load_cmap_map(ttx_path: str) -> dict[int, str]:
    """Build cmap: codepoint(int) -> glyphName(str)"""
    root = etree.parse(ttx_path).getroot()
    cmap_map: dict[int, str] = {}
    for map_node in root.findall(".//map"):
        code = map_node.get("code")
        name = map_node.get("name")
        if not code or not name:
            continue
        try:
            cp = int(code, 16) if code.startswith("0x") else int(code)
        except Exception:
            try:
                cp = int(code)
            except Exception:
                continue
        cmap_map[cp] = name
    return cmap_map

def load_hmtx_widths(ttx_path: str) -> dict[str, int]:
    """Read <hmtx><mtx name=... width=.../> -> glyphName -> width(int)"""
    root = etree.parse(ttx_path).getroot()
    widths: dict[str, int] = {}
    for mtx in root.findall(".//hmtx/mtx"):
        name = mtx.get("name")
        w = mtx.get("width")
        if name is None or w is None:
            continue
        try:
            widths[name] = int(w)
        except Exception:
            continue
    return widths

def make_blank_checker(glyphs: dict[str, _Element], widths: dict[str, int]):
    """
    Return a callable is_blank(glyph_name) that memoizes:
      - True if no contour AND (no components OR all components are blank)
      - OR width == 0 (hmtx)
    """
    @lru_cache(maxsize=None)
    def _is_blank(name: str) -> bool:
        if widths.get(name) == 0:
            return True
        g = glyphs.get(name)
        if g is None:
            return True  # missing -> treat as blank to be safe
        contours = g.findall("contour")
        if contours:
            return False
        comps = g.findall("component")
        if not comps:
            return True
        for c in comps:
            child = c.get("glyphName")
            if not child:
                continue
            if not _is_blank(child):
                return False
        return True
    return _is_blank

def _compare_components_xml(comp_nodes_a: list[_Element], comp_nodes_b: list[_Element]) -> bool:
    """Strict compare for <component> lists — exact equality on x,y,scalex,scaley."""
    if len(comp_nodes_a) != len(comp_nodes_b):
        return False
    for ca, cb in zip(comp_nodes_a, comp_nodes_b):
        ax = ca.get("x") or ca.get("dx")
        ay = ca.get("y") or ca.get("dy")
        bx = cb.get("x") or cb.get("dx")
        by = cb.get("y") or cb.get("dy")
        if ax != bx or ay != by:
            return False
        asx = ca.get("scalex") or ca.get("scale")
        asy = ca.get("scaley") or ca.get("scaleY")
        bsx = cb.get("scalex") or cb.get("scale")
        bsy = cb.get("scaley") or cb.get("scaleY")
        if (asx is not None) or (bsx is not None):
            if asx != bsx:
                return False
        if (asy is not None) or (bsy is not None):
            if asy != bsy:
                return False
    return True

def _contour_sig(c: _Element) -> str:
    parts = []
    for pt in c.iter("pt"):
        x = pt.get("x") or ""
        y = pt.get("y") or ""
        on = pt.get("on") or ""
        parts.append(x); parts.append(","); parts.append(y); parts.append(","); parts.append(on); parts.append(";")
    return "".join(parts)

def _compare_contours_xml(glyph_a: _Element, glyph_b: _Element) -> bool:
    """Fast contour comparison by serialized point strings."""
    contours_a = glyph_a.findall("contour")
    contours_b = glyph_b.findall("contour")
    if len(contours_a) != len(contours_b):
        return False
    for ca, cb in zip(contours_a, contours_b):
        if _contour_sig(ca) != _contour_sig(cb):
            return False
    return True

def compare_glyphs_ttx(
    glyphs_a: dict[str, _Element], name_a: str,
    glyphs_b: dict[str, _Element], name_b: str,
) -> bool:
    """Component comparison first; otherwise contour comparison."""
    ga = glyphs_a.get(name_a); gb = glyphs_b.get(name_b)
    if ga is None or gb is None:
        return False
    comps_a = ga.findall("component")
    comps_b = gb.findall("component")
    if comps_a and comps_b:
        return _compare_components_xml(comps_a, comps_b)
    return _compare_contours_xml(ga, gb)

def glyph_fingerprint(elem: _Element) -> str:
    """Name-agnostic fingerprint based on components transforms or contour points."""
    comps = elem.findall("component")
    if comps:
        parts = ["C|", str(len(comps)), "|"]
        for c in comps:
            x  = c.get("x") or c.get("dx") or ""
            y  = c.get("y") or c.get("dy") or ""
            sx = c.get("scalex") or c.get("scale") or ""
            sy = c.get("scaley") or c.get("scaleY") or ""
            parts.extend((x, ",", y, ",", sx, ",", sy, ";"))
        return "".join(parts)
    contours = elem.findall("contour")
    parts = ["O|", str(len(contours)), "|"]
    for cont in contours:
        parts.append(_contour_sig(cont)); parts.append("|")
    return "".join(parts)

def glyph_hash(elem: _Element) -> str:
    return hashlib.md5(glyph_fingerprint(elem).encode("utf-8", "ignore")).hexdigest()

def is_disallowed_target(cp: int) -> bool:
    ch = chr(cp)
    if ch.isspace():
        return True
    # PUA (BMP)
    if 0xE000 <= cp <= 0xF8FF:
        return True
    return False

def build_mapping_from_ttx(ttx_encrypted: str, ttx_normal: str) -> tuple[dict[str, str], list[list]]:
    glyphs_enc  = load_ttx_glyphs(ttx_encrypted)
    glyphs_norm = load_ttx_glyphs(ttx_normal)

    cmap_enc    = load_cmap_map(ttx_encrypted)
    cmap_norm   = load_cmap_map(ttx_normal)

    widths_enc  = load_hmtx_widths(ttx_encrypted)
    widths_norm = load_hmtx_widths(ttx_normal)

    is_blank_enc  = make_blank_checker(glyphs_enc, widths_enc)
    is_blank_norm = make_blank_checker(glyphs_norm, widths_norm)

    enc_all = [(cp, name) for cp, name in cmap_enc.items() if ENCRYPTED_FROM <= cp <= ENCRYPTED_TO]

    encrypted_items = sorted(enc_all, key=lambda x: (0 if is_blank_enc(x[1]) else 1, x[0]))

    hash_index: dict[str, list[tuple[int, str]]] = {}
    for cp_n, gname_n in cmap_norm.items():
        if is_disallowed_target(cp_n):
            continue
        if is_blank_norm(gname_n):
            continue
        g = glyphs_norm.get(gname_n)
        if g is None:
            continue
        h = glyph_hash(g)
        hash_index.setdefault(h, []).append((cp_n, gname_n))

    mapping: dict[str, str] = {}
    unmatched: list[list] = []

    for cp_s, gname_s in tqdm(encrypted_items, desc="encrypted", unit="glyph"):
        if is_blank_enc(gname_s):
            unmatched.append([cp_s, gname_s])
            continue

        g_enc = glyphs_enc.get(gname_s)
        if g_enc is None:
            unmatched.append([cp_s, gname_s])
            continue

        h = glyph_hash(g_enc)
        candidates = hash_index.get(h, [])
        matched = False
        for cp_n, gname_n in candidates:
            if compare_glyphs_ttx(glyphs_enc, gname_s, glyphs_norm, gname_n):
                mapping[f"\\u{cp_s:04x}"] = chr(cp_n)
                matched = True
                break

        if not matched:
            for cp_n, gname_n in cmap_norm.items():
                if is_disallowed_target(cp_n):
                    continue
                if is_blank_norm(gname_n):
                    continue
                if compare_glyphs_ttx(glyphs_enc, gname_s, glyphs_norm, gname_n):
                    mapping[f"\\u{cp_s:04x}"] = chr(cp_n)
                    matched = True
                    break

        if not matched:
            unmatched.append([cp_s, gname_s])

    return mapping, unmatched

if __name__ == "__main__":
    ttx_enc  = "read.ttx"
    ttx_norm = "MI LANTING.ttx"

    mapping, unmatched = build_mapping_from_ttx(ttx_enc, ttx_norm)

    Path("mapping_from_ttx.json").write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")
    Path("unmatched_from_ttx.json").write_text(json.dumps(unmatched, ensure_ascii=False, indent=2), encoding="utf-8")
```

**匹配结果与验证**

经过完整比对后，初步得到 **3513** 对映射关系，并有 **93** 项未找到对应字形。

随后将这 **93 项** 分别通过 HTML 对照方式，用 `read.ttf` 与原字体 (`MI LANTING.ttf`) 同时渲染同一段字符，人工对比结果如下:

* 其中 **122 项** 实际上是正常可见字符 (并非混淆映射目标)
* 仅有 **2 项** 确认为真实的映射缺口

这两项缺口手动补全如下:

```json
{
  "\uf63b": "啰",
  "\ue8c0": "瞭"
}
```

补全后，映射总数达到 **3515** 对。

**与空字形对比**

由于此前在 `read.ttf` 中统计得到 **3500** 个空字形 (即 `width=0` 且无轮廓)，两者数量非常接近，因此对两集合进行交叉比对:

* 映射表的 value 集合与空字形集合之间，**空字形集合是映射值的子集**。
* 仅多出 **15 个额外字符**，这些字符全部为**符号类误匹配**，即虽然图形结构相似，但并非常用汉字。

这些误匹配的字符如下:

```json
{
  "\ue7c7": "ḿ",
  "\ue7c8": "ǹ",
  "\ue7e7": "〾",
  "\ue7e8": "⿰",
  "\ue7e9": "⿱",
  "\ue7ea": "⿲",
  "\ue7eb": "⿳",
  "\ue7ec": "⿴",
  "\ue7ed": "⿵",
  "\ue7ee": "⿶",
  "\ue7ef": "⿷",
  "\ue7f0": "⿸",
  "\ue7f1": "⿹",
  "\ue7f2": "⿺",
  "\ue7f3": "⿻"
}
```

这些字符属于 Unicode 的部件或注音符号区，而非 CJK 统一汉字。

最终稳定为 **3500** 对一一对应。

### 五、使用与还原

保存一份映射表 JSON。使用时:

1. 先读取映射表并取其前 3500 个值构成空白集合
2. 对混淆段落：先剔除空白字符，再按映射表替换

示例:

```python
import json
from itertools import islice
from pathlib import Path

LINOVELIB_FONT_MAP_PATH = Path("/path/to/map.json")
_FONT_MAP: dict[str, str] = json.loads(
    LINOVELIB_FONT_MAP_PATH.read_text(encoding="utf-8")
)
_BLANK_SET: set[str] = set(islice(_FONT_MAP.values(), 3500))

def _apply_font_map(text: str) -> str:
    """
    Apply font mapping to the input text, skipping characters in blank set.
    """
    return "".join(_FONT_MAP.get(c, c) for c in text if c not in _BLANK_SET)
```
