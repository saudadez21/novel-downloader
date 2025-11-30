---
title: Qidian Web Analysis Notes
date: 2025-06-07
---

# 起点小说 Web 端分析笔记

创建日期: 2025/06/07

## 一、反调试

网站实现了基于 JavaScript 的调试陷阱 (debugger trap) 作为反调试手段。

当浏览器开发者工具 (DevTools) 被打开时, 脚本中的 debugger 语句会被触发, 导致执行自动暂停, 干扰正常调试过程。

示例代码:

```js
(function anonymous(
) {
debugger
})
```

### 规避方式 (仅供研究学习)

> 请合理使用调试工具应遵守相关法律法规及道德准则, 不得用于任何形式的恶意行为。

#### 方法 1: 在 DevTools 中手动禁用断点

可通过开发者工具 `Sources` 面板中的 `Deactivate breakpoints` 功能 (快捷键 `Ctrl + F8`) 来全局禁用所有断点。然后通过 `F8` (Resume script execution) 继续。

> 注意: 该方法会同时使你手动设置的断点失效

#### 方法 2: 屏蔽断点相关脚本文件的加载

可借助浏览器插件对关键 JavaScript 文件进行请求重定向, 阻止其加载。

例如使用插件 [Requestly: OpenSource Web Development Toolkit](https://chromewebstore.google.com/detail/requestly-opensource-web/mdnleldcmiljblolnjhpnblkcekpdkpa), 创建重定向规则, 将包含 `probev3.js` 的请求 URL 都指向一个不可访问或不存在的地址, 例如 `http://192.168.0.102:8080/probev3.js`。

> 提示: 目标文件不需要真实存在, 只需确保其无法被正常加载即可实现拦截效果。

#### 方法 3: hook 掉 debugger 的构造函数

## 二、Cookies 参数分析

在处理相关请求参数时, 参考了已有的分析成果, 结合实际测试后发现可直接复用其逻辑进行构造与使用。

参考资料:

- [某蜂窝w_tsfp参数分析-kylin1020-吾爱破解](https://www.52pojie.cn/thread-1916130-1-1.html)
- [某蜂窝w_tsfp参数分析-kylin1020-知乎](https://zhuanlan.zhihu.com/p/693729324)

技术要点小结:

- 参数 `w_tsfp` 使用了 RC4 加密算法
- 每次请求时, 前端会基于当前时间戳动态生成原始数据
- 随后使用固定的密钥 (key) 对其进行 RC4 加密, 生成新的加密字符串
- 该加密结果作为 `w_tsfp` 值, 附加至请求的 Cookie 中, 实现验证机制

## 三、章节内容解析

在请求小说章节时, 页面中的主要数据通常嵌入在以下标签中:

```html
<script id="vite-plugin-ssr_pageContext" type="application/json">...</script>
```

该标签内包含完整的 SSR (Server-Side Rendering) 上下文数据, JavaScript 运行时会基于该 JSON 内容进行页面渲染。因此, 在解析页面时可以直接提取并解析其中的 JSON 数据。

示例代码:

```python
from lxml import html

def find_ssr_page_context(html_str: str) -> dict[str, Any]:
    """
    Extract SSR JSON from <script id="vite-plugin-ssr_pageContext">.
    """
    try:
        tree = html.fromstring(html_str)
        script = tree.xpath('//script[@id="vite-plugin-ssr_pageContext"]/text()')
        if script:
            data: dict[str, Any] = json.loads(script[0].strip())
            return data
    except Exception as e:
        pass
    return {}
```

### 数据结构与字段说明

其中的 `content` 字段为章节正文的 HTML 内容, 其他相关字段如下:

```python
page_context = ssr_data.get("pageContext", {})
page_props = page_context.get("pageProps", {})
page_data = page_props.get("pageData", {})
chapter_info = page_data.get("chapterInfo", {})

# 正文 HTML
raw_html = chapter_info.get("content", "")

# 解密相关字段
chapter_id = chapter_info.get("chapterId", chapter_id)
fkp = chapter_info.get("fkp", "")
fuid = cookie.get("ywguid", "")  # 登录后的 cookie 中包含的身份标识

# 字体混淆及样式相关
css_str = chapter_info["css"]
randomFont_str = chapter_info["randomFont"]
fixedFontWoff2_url = chapter_info["fixedFontWoff2"]

# 状态标识
is_buy = chapter_info.get("isBuy", 0)
vip_flag = chapter_info.get("vipStatus", 0)
fens_flag = chapter_info.get("fEnS", 0)
ces_flag = chapter_info.get("cES", 0)
```

### 加密判断逻辑

章节内容的可读性取决于以下几个状态位的组合:

* `vip_flag == 0` 且 `fens_flag == 0`: 内容未加密, 可直接解析并提取 `<p>` 标签段落。
* `vip_flag == 1` 且 `fens_flag == 1`: 内容经过加密, 需通过特定方式解密后提取段落。
* `ces_flag == 2`: 开启字体加密, 解密流程除正文外还需处理字体映射关系。

> 注: 上述标识位也可统一用 `!= 0` 进行判断

---

### 解密逻辑分析

通过浏览器断点调试可发现, 解密核心逻辑集中于 `4819793b.qeooxh.js` 中, 主要由 `chunk-476a3f3b.js` 内以下函数调用:

```js
function initFock(userKey, fkp) {
    if (!window.Fock)
        throw new Error("missing Fock");
    window.Fock.initialize(),
    window.Fock.setupUserKey(userKey),
    fkp && eval(atob(fkp))
}
function unlockFock(e, t) {
    return new Promise((function(n, o) {
        try {
            var r;
            null === (r = window.Fock) || void 0 === r || r.unlock(e, t, (function(e, t) {
                0 === e ? n(t) : o(new Error("F:e:u: ".concat(e)))
            }
            ))
        } catch (i) {
            o(i)
        }
    }
    ))
}
```

使用流程如下:

```js
async function decrypt(enContent, cuChapterId, fkp, fuid) {
  Fock.initialize();
  Fock.setupUserKey(fuid);
  eval(atob(fkp));

  return new Promise((resolve, reject) => {
    Fock.unlock(enContent, cuChapterId, (code, decrypted) => {
      if (code === 0) {
        resolve(decrypted);
      } else {
        reject(new Error(`Fock.unlock failed, code=${code}`));
      }
    });
  });
}
```

部署时只需在 Node.js 环境中补充浏览器所需的环境对象, 即可模拟解密流程。

---

## 四、字体加密内容复原方案

章节加密不仅体现在正文, 还包括字体及渲染顺序的混淆。主要策略分为两部分:

### 1. CSS 级混淆分析

在页面中, 字符的真实呈现顺序被 CSS 规则刻意打乱。

通过分析 HTML 标签、属性以及相关伪元素样式, 可以重建文本的原始内容。常见的混淆策略包括:

* `font-size: 0`: 元素内容不可见, 应在解析时忽略
* `scaleX(-1)`: 对字符进行水平镜像, 不影响实际语义, 仅需在重建时还原为正常方向
* `::before` / `::after`: 通过伪元素插入特定字符 (如 `content: '遇'`)
* `content: attr(...)`: 将自定义属性中的内容注入渲染流
* `order`: 配合 Flex 布局重排节点顺序, 需依据样式指令恢复文本原序

**示例 CSS**:

```css
.sy-0 { font-size: 0; }
ya1 { order: 1; }
yf4 { order: 2; }
y7r { order: 3; }
yjq { order: 4; }
yq3 { order: 5; }
y87 { order: 6; }
ypy { order: 7; }
ylx { order: 8; }
yfc { order: 9; }
ypl { order: 10; }
y3x { order: 11; }
ys5 { order: 12; }
y0v { order: 13; }
ywp { order: 14; }
y1p { order: 15; }
.p1 ya1::after { content: '这'; }
.p1 yf4::after { content: '儿'; }
.p1 y7r::before { content: attr(ywda); }
.p1 yjq::after { content: '真'; }
.p1 yjq::first-letter { font-size: 0; }
.p1 yq3::before { content: attr(ygmh); }
.p1 y87::after { content: '一'; }
.p1 ypy::before { content: attr(ya0u); }
.p1 ylx::before { content: attr(yn2e); }
.p1 yfc::after { content: '丽'; }
.p1 ypl::before { content: attr(ylxl); }
.p1 y3x::before { content: attr(y5jn); }
.p1 ys5::after { content: '间'; }
.p1 y0v::before { content: attr(ythw); }
```

**示例 HTML**:

```html
<p class="p1"><ylx yigi="也" yn2e="美"></ylx><ypl ylxl="的" yxry="开"></ypl><y3x y5jn="乡" ylyh="为"></y3x><yjq>种</yjq><y7r y6ak="学" ywda="可"></y7r><yfc></yfc><yq3 yiiv="国" ygmh="是"></yq3><ys5></ys5><yf4></yf4><ypy ya0u="个" yquq="要"></ypy><ya1></ya1><y87></y87><y0v ythw="！" yg84="了"></y0v></p>
<p>在整个英格兰境<y class="sy-0">隐藏</y>内，我不相<y class="sy-0">测试</y>信我竟能找<y class="sy-0">藏字</y>到这样一个能与尘<y class="sy-0">藏字</y>世<y class="sy-0">藏字</y>的喧嚣完全隔绝的地<y class="sy-0">测试</y><y class="sy-0">藏字</y>方，<y class="sy-0">藏字</y>一个厌世者的<y class="sy-0">乱码</y>理想的<y class="sy-0">测试</y>天堂。</p>
```

**渲染效果示例**:

<style>
.sy-0 { font-size: 0; }
ya1 { order: 1; }
yf4 { order: 2; }
y7r { order: 3; }
yjq { order: 4; }
yq3 { order: 5; }
y87 { order: 6; }
ypy { order: 7; }
ylx { order: 8; }
yfc { order: 9; }
ypl { order: 10; }
y3x { order: 11; }
ys5 { order: 12; }
y0v { order: 13; }
ywp { order: 14; }
y1p { order: 15; }
.p1 { display: flex; }
.p1 ya1::after { content: '这'; }
.p1 yf4::after { content: '儿'; }
.p1 y7r::before { content: attr(ywda); }
.p1 yjq::after { content: '真'; }
.p1 yjq::first-letter { font-size: 0; }
.p1 yq3::before { content: attr(ygmh); }
.p1 y87::after { content: '一'; }
.p1 ypy::before { content: attr(ya0u); }
.p1 ylx::before { content: attr(yn2e); }
.p1 yfc::after { content: '丽'; }
.p1 ypl::before { content: attr(ylxl); }
.p1 y3x::before { content: attr(y5jn); }
.p1 ys5::after { content: '间'; }
.p1 y0v::before { content: attr(ythw); }
</style>

<p class="p1"><ylx yigi="也" yn2e="美"></ylx><ypl ylxl="的" yxry="开"></ypl><y3x y5jn="乡" ylyh="为"></y3x><yjq>种</yjq><y7r y6ak="学" ywda="可"></y7r><yfc></yfc><yq3 yiiv="国" ygmh="是"></yq3><ys5></ys5><yf4></yf4><ypy ya0u="个" yquq="要"></ypy><ya1></ya1><y87></y87><y0v ythw="！" yg84="了"></y0v></p>
<p>在整个英格兰境<y class="sy-0">隐藏</y>内，我不相<y class="sy-0">测试</y>信我竟能找<y class="sy-0">藏字</y>到这样一个能与尘<y class="sy-0">藏字</y>世<y class="sy-0">藏字</y>的喧嚣完全隔绝的地<y class="sy-0">测试</y><y class="sy-0">藏字</y>方，<y class="sy-0">藏字</y>一个厌世者的<y class="sy-0">乱码</y>理想的<y class="sy-0">测试</y>天堂。</p>

### 2. 字体文件加密

每个章节会加载两类加密字体, 用于隐藏真实字符编码:

* `randomFont_str` (章节级动态字体): 每章唯一, 字体内部编码随机变换
* `fixedFontWoff2_url` (字体池随机分发): 从服务器维护的字体池中随机返回一份字体文件, 同一字体可能被多个章节重复使用, 字体池会周期性轮换更新

典型的 CSS 引用示例:

```css
font-family: LIIBFYOT, HTEMPCHB, 'SourceHanSansSC-Regular', 'SourceHanSansCN-Regular', ...
```

其中 `LIIBFYOT` 和 `HTEMPCHB` 即为加密字体, 由于页面使用的字体未直接暴露真实字形与原文字符之间的对应关系, 因此需要构建映射才能恢复正文内容。

#### 字体还原思路与映射建立

> 字体由 [svg2ttf](https://github.com/fontello/svg2ttf) 生成, 即使对应同一字符, 不同版本字形仍存在细微差异。
>
> 因此, 最可行的方式是通过 OCR 自动识别字形并建立映射。

**初期还原阶段**

在缺乏历史映射数据的阶段, 可采用 OCR 的方式恢复章节文本:

* 使用字形结构相似的公开字体 (如 `SourceHanSans`) 对模型进行轻量微调
* 从页面中导出所有可见字符, 生成逐字图像样本
* 使用 OCR 进行逐字识别 (单字识别, 无上下文)
* 若模型识别结果稳定且逻辑合理, 可初步得到章节的明文内容

**自动化建立持久字体映射**

实际观察表明:

* 大部分章节在发布 **约一个月后** 会回退为 **纯文本加密** (不再使用混淆字体)
* 在这一状态下, 服务器返回的 HTML 已基本等价于纯文本, 只需解密正文即可获得准确明文

在这种情况下, 可以进行高质量比对:

* 获取同一章节的 **纯文本版本** (回退后)
* 与其历史的 **加密字体版本** 对齐比对
* 由此精确建立字形与真实字符之间的映射

随着时间积累, 映射库会越来越完整, 从而有效覆盖绝大部分字体池和章节字体, 为模型进一步微调提供高质量训练数据

**识别增强与误差控制**

当前识别流程以 **单字图像 + 无上下文 OCR** 为主，因此可能出现:

* 相似字形混淆
* 少量识别误差
* 字形退化带来的不稳定性

可行的优化方向包括:

* 加入上下文约束: 基于语言模型的 "多字联动识别", 减少歧义
* 概率式输出整句校准: 使用 NLP 语言模型对多候选结果进行纠错
* 字形聚类与历史映射复用: 对相似字形自动聚类, 提高映射复用率

由于工程复杂度较高, 目前实现仍保持在较简洁的结构

> 如有更优的实现方式或改进建议, 欢迎通过 Issue 提出或进行补充。

## 五、章节重复内容的异常与修复方法

在某些小说章节中, 存在**正文段落被重复附加一份伪变形副本**的情况。

该副本内容与原段落高度相似, 但部分关键词被替换或语序被调整, 推测是网站在返回数据时出于防爬策略主动插入的扰动内容。

### 表现形式

伪重复内容通常位于**正文尾部**, 其与前段内容极为接近, 常见的词汇变形包括但不限于:

* **人名替换**：如 `张三` -> `李四`
* **人称替换**：如 `我` -> `你`、`他`
* **属性词替换**：如 `大` <-> `小`、`男` <-> `女`
* **语序调整或轻微变形**：如 `还没有` <-> `还有没`

### 示例

原始段落:

```txt
张三停在废弃的车站前。
他望着远方沉思不语。
风掠过铁轨，他大吃一惊。
“我真的还没有准备好……”他低声说。
身为江湖上赫赫有名的刀客，他从不轻言退却。
```

变为:

```txt
张三停在废弃的车站前。
他望着远方沉思不语。
风掠过铁轨，他大吃一惊。
“我真的还没有准备好……”他低声说。
身为江湖上赫赫有名的刀客，他从不轻言退却。
婉儿站在废弃的车站边。
她望着近方沉思不语。
风掠过铁轨，她小吃一惊。
“他真的还有没准备好……”她高声说。
身为江湖上赫赫没名的刀客，她从不轻言退却。
```

### 修复方法

> 具体网站在渲染时是如何处理伪重复内容仍有待深入分析

根据页面结构分析, 每个章节包含一个 `eFW` 字段。

当该字段值为 `1` 时, 章节正文会插入一段结构相似但细节略有变动的**伪内容块**, 通常紧随原文后追加, 形成 "重复但扰动" 的双段结构。

因此, 采用了以下**截断策略**进行初步修复:

#### 策略说明

* 检查章节的 `eFW` 字段是否为 `1`
* 若为真, 则对正文内容进行处理
  * 去除空白字符 (如空格、换行符)
  * 截取前半部分字符作为原始正文
* 该策略假设原始内容在前, 伪内容在后
