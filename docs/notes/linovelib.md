# 哔哩轻小说 (linovelib) 分析笔记

日期: 2025/05/25

## 一、混淆脚本与字体注入

在部分章节页面中, 能发现如下经混淆压缩的 JavaScript 代码:

```js
<script>;eval(function(p,a,c,k,e,r){e=function(c){return c.toString(a)};if(!''.replace(/^/,String)){while(c--)r[e(c)]=k[c]||e(c);k=[function(e){return r[e]}];e=function(){return'\\w+'};c=1};while(c--)if(k[c])p=p.replace(new RegExp('\\b'+e(c)+'\\b','g'),k[c]);return p}('b 3=c d();3.e(`@0-f{0-4:1;0-g:h;i:5(\'/6/0/1.7\')8(\'7\'),5(\'/6/0/1.j\')8(\'k\')}#l p:m-n-o-q(2){0-4:"1"!r}`);9.a=[...9.a,3];',28,28,'font|read||sheet|family|url|public|woff2|format|document|adoptedStyleSheets|const|new|CSSStyleSheet|replaceSync|face|display|block|src|ttf|truetype|TextContent|nth|last|of||type|important'.split('|'),0,{}));</script>
```

通过 `console.log` 打印可知, 其功能是动态创建并注入一段 CSS 规则, 用以加载自定义字体, 核心解密如下:

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

p.s. 和之前的起点机制类似, 不过这里用的是固定字体文件, 而起点是从固定集合中选一个, 再动态生成本次请求的专用字体。

对应的 CSS 定义为:

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

由此推断: 页面对倒数第二个 `<p>` 元素应用了自定义 "read" 字体, 而当前最后一个 `<p></p>` 始终为空。

---

## 二、字体渲染测试

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

观察可见: 部分字符渲染为空白, 如示例中所示。

编码格式为: 每两位私有使用区 (PUA) 字符后跟一位汉字

但由于 read 字体并未为这些正常汉字嵌入字形信息, 故其在渲染时始终表现为空白

注: 也可以查看 `width="0"` 的字 例如:

```bash
> ttx ./read.ttf
Dumping ".\read.ttf" to ".\read.ttx"...
Dumping 'GlyphOrder' table...
Dumping 'head' table...
Dumping 'hhea' table...
Dumping 'maxp' table...
Dumping 'OS/2' table...
Dumping 'hmtx' table...
Dumping 'cmap' table...
Dumping 'loca' table...
Dumping 'glyf' table...
Dumping 'name' table...
Dumping 'post' table...
```

这里可以看出 `0x4e00` 和 `0x4e01` 为空白

```ttx
  <hmtx>
    <mtx name="glyph07404" width="0" lsb="0"/>
    <mtx name="glyph07405" width="0" lsb="0"/>
    ...

  <cmap>
    <tableVersion version="0"/>
    <cmap_format_4 platformID="0" platEncID="3" language="0">
      <map code="0x4e00" name="glyph07404"/><!-- CJK UNIFIED IDEOGRAPH-4E00 -->
      <map code="0x4e01" name="glyph07405"/><!-- CJK UNIFIED IDEOGRAPH-4E01 -->
    ...

  <glyf>

    <!-- The xMin, yMin, xMax and yMax values
         will be recalculated by the compiler. -->
    ...

    <TTGlyph name="glyph07404"/><!-- contains no outline data -->

    <TTGlyph name="glyph07405"/><!-- contains no outline data -->

    ...
```

---

## 三、空映射字符统计

利用 fontTools 库统计空映射字符数量:

```python
from fontTools.ttLib import TTFont

if __name__ == "__main__":
    font_ttf = TTFont(FONT_PATH)
    all_chars = {chr(c) for c in font_ttf.getBestCmap()}

    blank = set()
    for ch in all_chars:
        img = render_text(ch, font)
        if img.getextrema() == (255, 255):
            blank.add(ch)

    # 排除常见空白字符
    blank -= {" ", "\u3000"}
    print(len(blank))  # 3500
```

结果显示, 该字体中共有 **3500** 个字符映射为空白。

---

## 四、内容复原思路

1. **字体固定**: 由于字体文件地址固定, 且各章节均采用同一字体, 无需每次动态 OCR。
2. **映射表微调**: 复用此前在起点小说中训练的 OCR 模型, 结合字体的字形特征微调, 和一些其它工具, 生成定制映射表。
3. **批量复原**: 对倒数第二段 HTML 文本, 若存在加密代码, 去除空映射后批量映射, 即可自动还原加密内容。
