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

字体显示顺序通常被 CSS 人为打乱, 结合 HTML 标签、属性与样式渲染可恢复原始内容。示例策略包括:

* `font-size: 0`: 该元素不可见, 应跳过；
* `scaleX(-1)`: 镜像翻转, 对内容无影响, 仅作为重建参考；
* `::before` / `::after`: 在元素前后插入特定字符（如 `content: '遇'`）；
* `content: attr(...)`: 插入指定属性值；
* `order`: 用于重排段落或字符顺序, 需结合样式解析还原。

### 2. 字体文件加密

每章节使用两种加密字体:

* `randomFont_str`: 每章节唯一, 字体编码动态变更；
* `fixedFontWoff2_url`: 请求时从字体 "池" 中随机分配一份字体文件, 可能会在多个章节间复用。

页面 CSS 示例:

```css
font-family: LIIBFYOT, HTEMPCHB, 'SourceHanSansSC-Regular', 'SourceHanSansCN-Regular', ...
```

其中 `LIIBFYOT` 和 `HTEMPCHB` 为加密字体名称。由于真实字符并未直接展示, 需要通过以下手段还原真实内容。

#### 字体还原思路与映射建立

**初期阶段**

* 使用类似字形的公开字体 (如 `SourceHanSans`) 进行模型微调；
* 基于章节中的可见字符构建图像样本；
* 利用 OCR (光学字符识别) 进行逐字识别 (单字图像, 无上下文)；
* 若识别结果合理, 则可初步还原正文。

**自动构建字体映射**

* 根据实际观察, 大多数章节在发布时间 **约一个月后** 退回为 "纯文本加密" 形式, 仅需解密正文即可获取明文 HTML。
* 在此状态下, 若作者未修改就可以精确还原整章内容, 进一步与历史的加密版本进行比对, 从而建立 "字符形状 -> 字符" 之间的稳定映射关系。
* 随着时间积累, 此映射数据集将逐渐完善, 可以进一步微调模型

**识别增强与误差控制**

* 当前识别流程基于逐字图像生成与无上下文识别, 可能存在少量误差
* 可考虑以 "多字联动识别" 为改进方向, 提高上下文信息对字符识别的约束力
* 当前实现因复杂度未进一步深入

如有更优的实现方式或改进建议, 欢迎通过 Issue 提出或进行补充。

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
