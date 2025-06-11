# 多看电子书信息

Reference:

- [多看电子书规范扩展开放计划](https://dongzl.github.io/2020/08/01/32-Duokan-Epub-Specification/index.html)
- [多看精排书制作简记](https://www.daoqinxuan.com/archives/1594)
- [多看电子书制作技巧](https://www.jianshu.com/p/ce7fa8b83da8)

---

## 图片

#### 图片尺寸定义

如果不设置图片尺寸, 当图片尺寸超过了屏幕的尺寸, 多看会将图片自动缩小到屏幕的宽度或高度; 图片尺寸小于屏幕的时候则按原图显示。

多看的图片尺寸定义与 `CSS` 规范有点区别, 主要体现在百分比上面。由于目前移动设备都是视网膜屏幕, 我们在 `pc` 显示器上所谓的 1 像素可能在手机上意味着 4 像素 (2x2) , 不同的电子书软件对此的解释也不一样, 所以设定图片尺寸最好用相对尺寸 `em` 或者百分比。

多看中, 图片宽度的百分比是相对于屏幕的 (`CSS` 规范中百分比相对于图片本身的宽度) , 如果宽度为 `100%`, 则图片宽度撑满整个屏幕宽度 (不包括出血格) , `50%` 则占屏幕一半宽度。所以图片的分辨率要比较高, 如果分辨率本身就很低, 设置宽度 `100%` 就会满屏幕的马赛克。

由于 `epub` 是一种流式排版, 只有左右顶部是确定位置的, 所以多看对于图片的高度百分比 `CSS` 规范一样, 只是图片自身高度的百分比。

通常制作电子书时只需要设定宽度或高度的一个属性就可以了, 否则图像容易失真。

### 全屏插图页

全屏插图页扩展在 `ePub` 文件的 `opf` 文件中的 `spine` 节点下, `spine` 节点定义了 `ePub` 文件中文章出现的顺序, 每一个 `itemref` 项为一章, 我们扩展一个 `properties` 属性值 `duokan-page-fullscreen`, 示例如下:

```xml
<spine>
    <itemref idref="chapter100" properties="duokan-page-fullscreen">
    ...
</spine>
```

这样 `id` 为 `chapter100` 的章就会按全屏插图页逻辑处理, 而相应的 `html` 内容应如下所示:

```xml
<?xml version="1.0" encoding="utf-8"standalone="no"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
    "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">

<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <title></title>
    <link href="../Styles/stylesheet.css"rel="stylesheet" type="text/css" />
  </head>

  <body>
    <p><img src="../Images/sanguoyanyi.png"/></p>
  </body>
</html>
```

注意, `html` 中应只含有一个 `img`, 不需要设置任何样式, 程序会自动将图片撑满展示。

一般封面页需要加全屏, 全屏插图页也需要加全屏。在对应的页面中只需要存在一张图片文件即可, 不需要写文本, 写了也不会显示出来。

对于不同的屏幕尺寸, 多看只针对 `4:3` 和 `16:9` 两种宽高比做了适配。具体方式是:

> 需要全屏显示的图片为 `a.jpg`, 宽高比为 `4:3`, 则再做一张 `16:9` 的图片命名为 `a~slim.jpg` 放进 `epub` (与 `a.jpg` 同一位置) , 在页面中只需加载 `a.jpg` 即可。多看会根据屏幕尺寸自动显示不同宽高比的图片。

1. 对于 `3:2` (iPad横置时) 或 `16:10` 的屏幕尺寸, 多看会相应裁剪这些图片, 所以图片不要在边缘上留关键信息。
2. 假如不按照上述方法处理, 例如 `16:9` 的图片命名为 `a.jpg` 而 `4:3` 的图片命名为 `a~slim.jpg`, 多看会裁剪图片或上下留黑边。
3. 多看的书架显示书的封面均按照 `4:3` 显示, 如果只有 `16:9` 的封面, 多看会把图片压扁显示 (`iOS` 版可能会按原始宽高比显示书架封面)

### 交互图

对于交互图, 应用层会响应点击放大操作, 提供额外的交互体验, 具体扩展如下所示:

```html
<div class="duokan-image-single">
  <img src="../Images/tree.png"alt="" />
  <p class="duokan-image-maintitle">主标题: 大自然</p>
  <p class="duokan-image-subtitle">副标题: 森林中的树</p>
</div>
```

为了保证点击放大之后的图像呈现效果, 采用交互模式的图像数据应该保证足够的分辨率。

一篇笔记里提及:

1. 主标题和副标题可以不出现;
2. 主标题和副标题可以在 `img` 之前出现;
3. 交互图不可以嵌套出现。

另一篇笔记里提及:

1. 在应用了交互类的 `div` 里面, 可以使用多个图片 (多看 2.x 中多图片只能每行显示一张, 3.x 以上就可以并列显示了) , 每张图都可以交互, 但是如果 `div` 中有主副标题的话, 只有最后一张图放大后会显示主副标题;
2. 图片交互后, 会在底部固定显示主副标题, 但是不同系统中的实现方式不同。`android` 中, 不管主副标题有多少字, 交互后都会显示出来 (除非标题内容多得超过整个屏幕) , 而 `iOS` 中, 主副标题在交互后只能显示两行。所以在做画册之类标题的文本内容极多的电子书时, 需要注意这一点。
3. 交互图片可以与其它样式混用, 如居中显示和设置图片尺寸。
4. 如果图片宽高比为 `portrait` (宽比高要窄甚至窄很多) , 高度超过了屏幕高度时, 多看会将图片高度缩小到屏幕高度, 但主副标题可能无法显示出来——但如果超出太多, 多看就完全不显示这张图了。所以这种情况下需要定义图片高度。

### 画廊模式

画廊模式可以支持在同一个位置显示多张大小一致的图像, 用户可以通过滑动等手势切换不同的图像内容。

如下, 即为一个拥有三帧画面的画廊 (每一个 `duokan-image-gallery-cell` 声明一个分帧) :

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

一篇笔记里提及:

1. 各分帧图片最好保持同样大小;
2. 最好各分帧都存在主标题和副标题;
3. 画廊整体样式应该放在 `duokan-image-gallery` 所在的 `div` 上。

另一篇笔记里提及:

1. 画廊的大小取决于其内部所有图片中宽高比最小的那个。简单的说, 图片尺寸不一样但宽高比一样的话, 画廊都可以很完整的显示, 但如果有某个图片的宽高比值和其它图片差很多, 画廊就会调整大小, 使得所有图片都能以 `cover` 方式显示 (换言之画廊内部不允许出现黑边,  但允许裁剪图片外部) 所以画廊的图片最好尺寸一致, 如果不一致的话, 未交互时切换图片可能会发生图片的裁切, 但交互后图片都会完整显示。
2. 画廊的居中显示必须对 `gallery` 和 `cell` 两级属性都设置居中才会有居中效果。
3. 同交互图一样, 如果画廊高度超过屏幕高度, 也会导致标题不显示。

### 上下居中图

这个属性在多看漫画书中用的比较多, 当然你也可以用到普通的书里面。语法如下:

```xml
<spine>
    <itemref idref="chapter01.xhtml" properties="duokan-page-fitwindow">
    ...
</spine>
```

同样, 对应的 `html` 文件只需要一张图片即可, 不需要别的文字或者代码, 就算写了多看也不会显示出来, 而只会将图片上下居中显示。

### 延伸式全屏图

注意, 这个属性是多看4.4以上才有的, 最开始是用于s.这本书中, 显示的效果是全屏显示一半的报纸, 点击按钮之后进入交互的全屏显示, 可以放大和旋转。如果是多看的低版本, 这个属性无效。

语法如下:

```xml
<spine>
    <itemref idref="coverpage" properties="duokan-page-fullscreen-spread-left">
    ...
</spine>
```

这个代码会全屏显示图片的左半部分, 当然你把 `left` 改成 `right` 也可以, 就会显示图片的右半部分。只有这两个属性是有效的。

注意图片只能选择长宽比较大的 (横躺的图片) , 最好是长度的一半正好能显示一个完整的图。

### 多媒体 (音频、视频)

由于移动设备的一些特性, `html` 中标准的音频、视频的排版特点并不完全满足我们的需求, 因此, 需要进行一些"小小"的扩展, 才能得到比较完美的展示效果。

##### 音频

在 `HTML 5` 规范中, 音频采用标准的 `audio` 标签, 但需要扩展说明其占位图像, 示例如下:

```html
<audio class="duokan-audio content-speaker" placeholder="speaker.jpg" activestate="active-speaker.jpg" title="军港之夜">
    <source src="song.mp3" type="audio/mpeg" />
</audio>
```

`duokan-audio` 为扩展标签, 表明了该 `audio` 标签为多看扩展类型, `placeholder` 用于表示占位图, `activestate` 表示活动状态下的占位图, `title` 表示标题名。

一般情况下可以指定 `audio` 采用的 `CSS` 样式, 在绘制占位图时需要遵循该样式, 示例代码如下:

```css
audio.content-speaker {
    font-size: 16px;
    width: 0.8em;
}
```

`audio` 的 `controls` 属性出现时, 表明应用层需要显示控制栏, 如果不出现, 则无需显示控制栏。

音乐只支持 `mp3` 格式。

##### 视频

在 `HTML 5` 规范中, 视频采用标准的 `video` 标签, 示例如下:

```html
<video class="duokan-video content-matrix" poster="matrix.jpg">
    <source src="matrix.mp4" type="video/mp4" />
</video>
```

`duokan-video` 为扩展标签, 表明了该 `video` 标签为多看扩展类型。

一般情况下可以指定 `video` 采用的 `CSS` 样式, 在绘制 `poster` 时需要遵循该样式, 示例代码如下:

```css
video.content-matrix {
    width: 320px;
    height: 240px;
}
```

`video` 的 `controls` 属性禁止出现。

视频只支持 `mp4` 格式。

### 对象出血贴边

```css
.head {
    duokan-bleed: (top|left|right|bottom|lefttop|topright|lefttopright|leftright);
}
```

需要注意的是多看的这个语法并不是无条件 "贴边", 而是在图片的边贴到出血格位置的前提下才会进行相应的贴边。例如, 图片的尺寸非常小, 达不到屏幕宽度, 由于图片默认左边和顶边都是贴近出血格位置的, 则默认 `top` 和 `left` 属性都会起效; 但图片只有设置了靠右对齐时。`right` 属性才会起效; `bottom` 实际上只是贴近下一个段落的顶边, 并不是贴近屏幕的底边 (因为没有办法让前端元素贴近屏幕底边); 类似的, `leftright` 属性就需要左右边都要贴近出血格才会起效。

1. 如果图片本身尺寸很大而不设置 `100%` 的宽度, 当缩小字号的时候, 图片也会跟着缩小, 缩小到宽度不足屏幕宽度的时候, 就会导致贴边失效。如果设置了 `100%` 的宽度, 不管字号是多大, 图片都会固定贴边, 不会影响排版效果。
2. 贴边只针对正文元素, 如图片或文字都是可以贴边的, 但不会处理文字的 `padding` 等属性。所以贴边主要还是用于图片, 文字贴边只能用于特定的排版设计。

---

## 脚注

### 富文本脚注

用户可以通过单击文内脚注的图标, 弹出显示脚注内容的窗口。文内注可以支持复杂的内容描述, 比如多段落, 带有样式的文本等等, 具体描述如下:

在需要插入注的位置插入如下代码:

```html
<a class="duokan-footnote"href="#df-1"><img src=" ../Images/note.png"/></a>
```

在文章的末尾插入如下代码:

```html
<ol class="duokan-footnote-content">
    <li class="duokan-footnote-item"id="df-1"><p>这是一个注释文本。</p></li>
</ol>
```

注和内容之间使用 `id` 链接, 通过这样的扩展方式, 可以将整个章节的所有文内注内容集中在一个有序列表中, 这部分内容不会直接在页面上渲染出来, 而是通过应用层的交互来呈现。

这种方法的好处:

1. 兼容别的电子书软件;
2. 注释文本复杂的时候可以分行, 使用样式甚至插入图片。

第二种:

```html
<a class="duokan-footnote" href="#footnote1" alt="注释内容。"><img src=" ../Images/note.png"/></a>
```

这种方法不兼容别的电子书软件, 也不能使用样式。但好处是校对比较方便。

总的来说还是推荐使用第一种方法。

`AZW3` 转制的 `EPUB`, 则是通过互相引用锚来实现注释的来回跳转。简示如下:

```html
<a id="df-2"></a><a href="#df-1">[1]</a>
<a id="df-1"></a><a href="#df-2">[1]</a> 注释内容
```

如果需要改成多看的弹出注释, 可以借助批量替换、正则表达式实现转换。具体的表达式, 也需要根据文件本身的代码进行设计。关键在于借助原有的 `ID`, 实现注释和内容的链接。

---

## 字体

### 多看字体使用

多看字体包包括兰亭黑、细黑、宋体、小标宋、仿宋、楷体、衬线/非衬线英文字体和符号字体, `CSS` 中的 `fontfamily` 写相应的代码即可。

| 名称              | 对应字体                         |
| ----------------- | -------------------------------- |
| "DK-SONGTI"       | 宋体                             |
| "DK-FANGSONG"     | 仿宋                             |
| "DK-KAITI"        | 楷体                             |
| "DK-HEITI"        | 黑体                             |
| "DK-XIAOBIAOSONG" | 小标宋                           |
| "DK-XIHEITI"      | 细黑体                           |
| "DK-SERIF"        | 衬线西文字体                     |
| "DK-CODE"         | 等宽西文字体                     |
| "DK-SYMBOL"       | 符号字体 (不常见符号, 如音标等)  |

多看官方客户端可用字体列表:

CSS写法:

```css
效果
font-family: "DK-SONGTI";
使用多看系统自带宋体。
font-family: "DK-FANGSONG";
使用多看系统自带仿宋。
font-family: "DK-KAITI";
使用多看系统自带楷体。
font-family: "DK-HEITI";
使用多看系统自带黑体。
font-family: "DK-XIAOBIAOSONG";
使用多看系统自带小标宋。
font-family: "DK-XIHEITI";
使用多看系统自带细黑体。
font-family: "DK-SERIF";
使用多看系统自带衬线西文字体。
font-family: "DK-CODE";
使用多看系统自带等宽西文字体。
font-family: "DK-SYMBOL";
使用多看系统自带符号字体 (不常见符号, 如音标等) 。
```

示例:

首先在CSS文件中增加下面的样式

```css
p.usekaiti {
  font-family: "DK-KAITI";
}
```

然后在 `xhtml` 文件中使用

```html
<p class="usekaiti">这段文字使用楷体显示</p>
```

这样就 ok 了。
