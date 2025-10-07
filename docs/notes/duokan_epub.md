# 多看电子书信息

Reference:

* [多看电子书规范扩展开放计划](https://dongzl.github.io/2020/08/01/32-Duokan-Epub-Specification/index.html)
* [多看精排书制作简记](https://www.daoqinxuan.com/archives/1594)
* [多看电子书制作技巧](https://www.jianshu.com/p/ce7fa8b83da8)

---

## 图片

### 图片尺寸

未设置尺寸时：

* 图片大于屏幕：自动按屏幕宽度或高度等比缩小。
* 图片小于屏幕：按原尺寸显示。

多看对百分比的解释与标准 CSS 略有差异：

* 宽度的百分比基于“屏幕宽度”（CSS 标准为基于包含块）。`width: 100%` 为全屏宽，不含出血格；`50%` 占半屏。为避免低分辨率拉伸导致糊化，大图应具备足够像素密度。
* 高度的百分比按图片自身高度计算，与 CSS 一致。
* 建议仅指定宽或高其中一项，避免失真。
* 建议优先使用相对单位（如 `em`、百分比），以适配不同设备像素密度。

### 全屏插图页

在 `opf` 的 `spine` 下为章节添加属性 `duokan-page-fullscreen`：

```xml
<spine>
  <itemref idref="chapter100" properties="duokan-page-fullscreen"/>
</spine>
```

对应 HTML 仅包含一张图片，不需样式，程序将自动铺满：

```xml
<?xml version="1.0" encoding="utf-8" standalone="no"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <title></title>
    <link href="../Styles/stylesheet.css" rel="stylesheet" type="text/css" />
  </head>
  <body>
    <p><img src="../Images/sanguoyanyi.png"/></p>
  </body>
</html>
```

常见用例为封面页和全屏插图页。页面仅需一张图片，文本不会显示。

适配规则仅覆盖 4:3 与 16:9：

* 若主图为 `a.jpg`（4:3），再提供一张 16:9 的 `a~slim.jpg`，与主图同目录。页面仅引用 `a.jpg`，客户端将按屏幕比例自动切换。
* 3:2（如 iPad 横屏）或 16:10 会发生自动裁剪，避免在边缘放置关键信息。
* 仅提供 16:9 封面时，书架封面以 4:3 显示，可能出现压缩变形（iOS 端可能按原比例显示）。

### 交互图

结构示例：

```html
<div class="duokan-image-single">
  <img src="../Images/tree.png" alt="" />
  <p class="duokan-image-maintitle">主标题: 大自然</p>
  <p class="duokan-image-subtitle">副标题: 森林中的树</p>
</div>
```

说明：

* 图像需具备足够分辨率，以保证放大后的清晰度。
* 主副标题可省略，且可置于 `img` 之前。
* 不可嵌套交互图。
* 同一交互容器内可放多张图，每张均可交互；如存在主副标题，仅最后一张图在放大后显示标题。
* 交互后标题在底部显示：Android 可完整显示（除非文本过长），iOS 交互后最多显示两行。
* 可与其他样式共用（如居中、尺寸设定）。
* 纵向长图（宽窄高长）超过屏幕高度时会缩至屏高，主副标题可能不显示；过长时可能不显示该图，需为此类图定义高度。

### 画廊模式

同一位置展示多帧等尺寸图片，支持滑动切换。示例：

```html
<div class="duokan-image-gallery">
  <div class="duokan-image-gallery-cell">
    <img src="images/tree1.png" alt="" />
    <p class="duokan-image-maintitle">主标题: 大自然</p>
    <p class="duokan-image-subtitle">副标题: 柏树</p>
  </div>
  <div class="duokan-image-gallery-cell">
    <img src="images/tree2.png" alt="" />
    <p class="duokan-image-maintitle">主标题: 大自然</p>
    <p class="duokan-image-subtitle">副标题: 柳树</p>
  </div>
  <div class="duokan-image-gallery-cell">
    <img src="images/tree3.png" alt="" />
    <p class="duokan-image-maintitle">主标题: 大自然</p>
    <p class="duokan-image-subtitle">副标题: 杨树</p>
  </div>
</div>
```

建议：

* 各帧图片尽量同尺寸，同步提供主副标题。
* 画廊整体样式挂在 `duokan-image-gallery` 容器上；居中需同时对 `gallery` 与 `cell` 设置。
* 画廊尺寸由内部图片中“宽高比最小”的图片决定，以 `cover` 方式铺放，允许裁切边缘以消除黑边；未交互时切换可能出现裁切，交互后完整显示。
* 高度超过屏幕时，标题可能不显示。

### 上下居中图

在 `spine` 为章节添加 `duokan-page-fitwindow`，对应 HTML 仅保留一张图，文本不显示：

```xml
<spine>
  <itemref idref="chapter01.xhtml" properties="duokan-page-fitwindow"/>
</spine>
```

### 延伸式全屏图（4.4+）

多看 4.4 及以上支持“半屏报纸”式延展，点击后进入可放大/旋转的全屏交互。语法：

```xml
<spine>
  <itemref idref="coverpage" properties="duokan-page-fullscreen-spread-left"/>
</spine>
```

`left` 显示图片左半，改为 `right` 显示右半。此特性适用于横向大图，建议图片在半幅内构成完整画面。

### 多媒体（音频、视频）

受移动端特性影响，需使用多看扩展类名以获得一致展示。

#### 音频

```html
<audio class="duokan-audio content-speaker" placeholder="speaker.jpg" activestate="active-speaker.jpg" title="军港之夜">
  <source src="song.mp3" type="audio/mpeg" />
</audio>
```

* `duokan-audio` 标记为多看音频扩展；`placeholder` 占位图，`activestate` 活动态占位图，`title` 标题。
* 可通过 CSS 设定占位图样式：

```css
audio.content-speaker {
  font-size: 16px;
  width: 0.8em;
}
```

* 出现 `controls` 属性时显示控制栏；音乐格式支持 `mp3`。

#### 视频

```html
<video class="duokan-video content-matrix" poster="matrix.jpg">
  <source src="matrix.mp4" type="video/mp4" />
</video>
```

* `duokan-video` 标记为多看视频扩展；`poster` 遵循所设 CSS 尺寸：

```css
video.content-matrix {
  width: 320px;
  height: 240px;
}
```

* 禁用 `controls` 属性；视频格式支持 `mp4`。

### 对象出血贴边

```css
.head {
  duokan-bleed: (top|left|right|bottom|lefttop|topright|lefttopright|leftright);
}
```

说明：

* 贴边基于元素“已贴近出血格”的前提触发：小图默认贴近左与上，因此 `top`、`left` 生效；`right` 需元素右对齐；`bottom` 贴近下一个段落上边，不是屏幕底边；`leftright` 需左右均贴近出血格。
* 大图未设 `width: 100%` 时，随字号缩小可能低于屏宽而导致贴边失效；设置 `100%` 可避免该问题。
* 贴边针对正文元素（图、文）有效，不处理文字的 `padding` 等属性；更适用于图片，文本贴边仅用于特定设计目的。

---

## 脚注

### 富文本脚注（推荐）

文内插入：

```html
<a class="duokan-footnote" href="#df-1"><img src="../Images/note.png"/></a>
```

章节末尾集中放置内容：

```html
<ol class="duokan-footnote-content">
  <li class="duokan-footnote-item" id="df-1"><p>这是一个注释文本。</p></li>
</ol>
```

通过 `id` 关联，实现跨段落、带样式的复杂脚注，兼容其他阅读器。

### 简易脚注（不兼容其他阅读器）

```html
<a class="duokan-footnote" href="#footnote1" alt="注释内容。"><img src="../Images/note.png"/></a>
```

便于校对，但不支持样式与兼容性。

### 从 AZW3 转 EPUB 的锚点脚注改造

原始互引示例：

```html
<a id="df-2"></a><a href="#df-1">[1]</a>
<a id="df-1"></a><a href="#df-2">[1]</a> 注释内容
```

可通过批量替换与正则，将锚点脚注转换为多看弹出脚注。关键是在保留原 `id` 的前提下建立“注—释”映射。具体正则需按文件结构设计。

---

## 字体

### 多看字体包与用法

内置字体包含：兰亭黑、细黑、宋体、小标宋、仿宋、楷体，以及英文字体（衬线/等宽）与符号字体。对应 `font-family` 值如下：

| 名称                | 对应字体       |
| ----------------- | ---------- |
| "DK-SONGTI"       | 宋体         |
| "DK-FANGSONG"     | 仿宋         |
| "DK-KAITI"        | 楷体         |
| "DK-HEITI"        | 黑体         |
| "DK-XIAOBIAOSONG" | 小标宋        |
| "DK-XIHEITI"      | 细黑体        |
| "DK-SERIF"        | 衬线西文字体     |
| "DK-CODE"         | 等宽西文字体     |
| "DK-SYMBOL"       | 符号字体（如音标等） |

CSS 示例：

```css
p.usekaiti {
  font-family: "DK-KAITI";
}
```

HTML 使用：

```html
<p class="usekaiti">这段文字使用楷体显示</p>
```

常用写法示例（节选）：

```css
font-family: "DK-SONGTI";        /* 多看内置宋体 */
font-family: "DK-FANGSONG";      /* 多看内置仿宋 */
font-family: "DK-KAITI";         /* 多看内置楷体 */
font-family: "DK-HEITI";         /* 多看内置黑体 */
font-family: "DK-XIAOBIAOSONG";  /* 多看内置小标宋 */
font-family: "DK-XIHEITI";       /* 多看内置细黑体 */
font-family: "DK-SERIF";         /* 多看内置衬线西文字体 */
font-family: "DK-CODE";          /* 多看内置等宽西文字体 */
font-family: "DK-SYMBOL";        /* 多看内置符号字体 */
```
