## TODO

以下为后续计划与优化方向

### 新增站点支持

* [刺猬猫](https://www.ciweimao.com/)
  * 网页端接口已基本解析完成，但 VIP 章节返回的为图片格式
  * 计划在有空时尝试使用 APP 端接口解决

### 搜索功能增强

* 增强现有搜索机制

  * 在站点内搜索 API 不可用或结果为空时, 允许 fallback 到搜索引擎 (如 Google/Bing)
  * 支持通过搜索引擎语法 (如 `site:example.com <书名>`) 自动发现书籍目录页 URL
  * 可配置搜索引擎类型、最大结果数与缓存策略
  * 在 CLI 中提供交互式选择搜索结果并直接下载

### 广告过滤与章节标题归一化

* Parser 中已对常见第三方网站广告进行基础过滤
* 需要继续排查是否存在遗漏
* 章节名称格式归一化:
  * 方案待设计 (作者习惯差异较大，如「第 1 章 标题」/「标题」/「第一章标题」等不一致格式)
  * 设计正则匹配与中文数字解析方案，提取章号与标题正文
  * 统一输出格式 (如 `第 12 章 标题`), 并在 `CleanerProcessor` 中提供归一化接口

### 已有站点维护

* **sfacg**
  * 可能因 `cookie expired` 导致失效
  * 需要考虑增加过期检测与重新获取机制 (暂未复现)

### EPUB 导出优化

* 当前主要性能瓶颈集中在 `zipfile` 的写入阶段, 以及图片缓存缺失时的重复下载
* 在缓存完整的情况下, `snakeviz` 分析结果显示 95% 以上的耗时集中在 ZIP 文件写入与压缩过程
* 可进一步探索更高效的压缩与写入方式, 例如:
  * 使用内存缓冲区批量写入以减少磁盘 IO
* 排版与样式优化:
  * 目前导出的排版较为基础，整体观感仍有改进空间
  * 需参考优秀 EPUB 样本，重点关注字体层次、段落间距、封面与章节页布局等设计细节

### 对比 OpenCC 与 opencc-python

* 对比 [opencc-python](https://github.com/yichen0831/opencc-python) 与 [OpenCC](https://github.com/BYVoid/OpenCC) 的差异
* 字典更新与维护情况
* 转换性能表现
* 安装方式与兼容性

### Processor 扩展: 翻译支持

计划扩展 `ProcessorProtocol`，新增翻译类处理器，用于在导出流程中对章节内容进行翻译。

#### 在线翻译服务

* [有道翻译](https://www.youdao.com/)
* [有道翻译 API](https://fanyi.youdao.com/openapi/)
* [百度翻译](https://fanyi.baidu.com/mtpe-individual/transText#/)
* [谷歌翻译](https://translate.google.com/)
  * 第三方库: [googletrans](https://github.com/ssut/py-googletrans)
* [Google Cloud Translation](https://cloud.google.com/translate)
* [DeepL](https://www.deepl.com/en/translator)
* [DeepL API](https://www.deepl.com/en/pro-api)
  * Python 库: [deepl](https://github.com/DeepLcom/deepl-python)

#### 大模型 API 翻译

* OpenAI GPT 系列
* Anthropic Claude
* DeepSeek
* Google Gemini
* 支持自定义 prompt 与目标语言

#### 自建 / 本地翻译模型

基于 `HuggingFace` / `Transformers` / `llama.cpp` / `Ollama` / `vLLM` 等框架。

##### 可选模型

* [MarianMT](https://huggingface.co/docs/transformers/en/model_doc/marian)
* [M2M-100](https://huggingface.co/docs/transformers/en/model_doc/m2m_100)
* [NLLB](https://huggingface.co/docs/transformers/en/model_doc/nllb)
* [Sakura](https://huggingface.co/SakuraLLM)
* [ALMA](https://github.com/fe1ixxu/ALMA)
* [aya-expanse-32b](https://huggingface.co/CohereLabs/aya-expanse-32b)
* [Seed-X-7B](https://github.com/ByteDance-Seed/Seed-X-7B)

#### 配置示例

```toml
[[plugins.processors]]
name = "translator.google"
source = "zh"
target = "en"

[[plugins.processors]]
name = "translator.deepl"
api_key = "YOUR_KEY"
source = "en"
target = "fr"

[[plugins.processors]]
name = "translator.hf"
model_path = "/models/Sakura-13B"
system_prompt = "你是一个轻小说翻译模型，可以忠实翻译为简体中文。"
user_prompt = "请翻译成中文：{text}"
```

### 命令行交互

* 整理并精简命令行参数
* 新增章节下载功能
  * CLI 支持通过 `--chapter-id` 参数指定章节 ID, 仅下载该章节并导出为单独 txt 文件
  * 当传入章节 URL 时, 自动解析出 `book_id` 与 `chapter_id`, 并询问是否下载整本或仅该章节
  * 增加相关交互提示与输出信息, 优化体验

### 导出模板支持

* 增加可定制的导出模板 (基于 `Jinja2`)

示例模板:

```jinja2
{{ book_name }}
作者：{{ author }}
状态：{{ serial_status }}  更新：{{ update_time }}
总字数：{{ word_count }}

简介：
{{ summary }}

{% for volume in volumes %}
====== {{ volume.volume_name }} ======

{% if volume.volume_desc %}
{{ volume.volume_desc }}

{% endif %}
{% for ch in volume.chapters %}
======== {{ ch.title }} ========

{{ chapters_content[ch.chapterId] }}

{% endfor %}
{% endfor %}
```

### 数据结构与存储规范化

> 设计原因: 部分站点使用加密字体或 CSS / JS 动态混淆来隐藏正文或排版信息
>
> 将这些资源直接以原始形式保存, 可在本地导出时更准确地还原内容, 减少手动还原误差与字符映射偏差

为支持多类型资源 (图片、字体、CSS 等), 将 `extra.image_positions` 字段迁移至统一的 `extra.resources` 管理结构, 以统一管理章节关联的多类型资源

新结构示例:

```json
{
    "resources": [
        {
            "category": "image",
            "position": 0,
            "type": "url",
            "data": "https://example.com/a.jpg"
        },
        {
            "category": "image",
            "position": 3,
            "type": "base64",
            "data": "iVBORw0KGgo...",
            "mime": "image/jpeg"
        },
        {
            "category": "font",
            "type": "url",
            "data": "https://example.com/font.woff2"
        },
        {
            "category": "font",
            "type": "base64",
            "data": "d09GRgABAAAA...",
            "mime": "font/woff2"
        },
        {
            "category": "css",
            "type": "text",
            "data": "body { color: red; }"
        }
    ]
}
```

| 字段名      | 类型   | 说明                                                       |
| ---------- | ------ | ---------------------------------------------------------- |
| `category` | `str`  | 资源类型, 如 `image` / `font` / `css` / `audio` 等          |
| `position` | `int`  | 用于图片资源, 指示资源在正文中的位置 (1-based, 0 表示章节开头) |
| `type`     | `str`  | 数据类型：`url` / `base64` / `text`                         |
| `data`     | `str`  | 实际内容或引用地址                                          |
| `mime`     | `str`  | MIME 类型, 用于 Base64 或其他二进制资源                      |

同时暂时添加对 `image_positions` 的兼容或自动转换脚本

**需更新模块**

以下模块需适配新的 `resources` 结构:

* `novel_downloader.plugins.base.client`
* `novel_downloader.plugins.common.client`
* `novel_downloader.plugins.sites.esjzone.parser`
* `novel_downloader.plugins.sites.kadokado.parser`
* `novel_downloader.plugins.sites.linovel.parser`
* `novel_downloader.plugins.sites.linovelib.parser`
* `novel_downloader.plugins.sites.lnovel.parser`
* `novel_downloader.plugins.sites.n37yq.parser`
* `novel_downloader.plugins.sites.n8novel.parser`
* `novel_downloader.plugins.sites.novelpia.parser`
* `novel_downloader.plugins.sites.qidian.parser`
* `novel_downloader.plugins.sites.qqbook.parser`
* `novel_downloader.plugins.sites.sfacg.parser`
* `novel_downloader.plugins.sites.shaoniandream.parser`
* `novel_downloader.plugins.sites.shencou.parser`
* `novel_downloader.plugins.sites.syosetu.parser`
* `novel_downloader.plugins.sites.syosetu18.parser`
* `novel_downloader.plugins.sites.wenku8.parser`
* `novel_downloader.plugins.sites.yodu.parser`

**潜在更新模块**

部分底层构建模块可能需要增加对字体与样式资源的支持:

* **`novel_downloader.libs.epub_builder`**
  * `EpubBuilder` 需新增 `add_font` 相关 API
  * 后续可支持在 EPUB 内嵌字体与样式
* **`novel_downloader.libs.html_builder`**
  * `HtmlBuilder` 需新增 `add_font` 接口；
  * 优化生成 HTML 时的字体与css引用逻辑

### 打包与分发

* 计划提供可执行文件打包方案
* 待选工具:
  * `pyinstaller`
  * `nuitka`

---

## 低优先级计划

### 移除 Node.js 依赖

* 目前 QQ 与起点部分章节依赖 JavaScript 解密函数
* 计划尝试使用 Python 重写以避免 `subprocess` 调用
* 若完成，QQ 的 IIFE 内容可参考 [解析笔记](./notes/parse_js_iife.md) 转为纯 Python 版
* 实现复杂、耗时较长，暂时搁置

### 新增搜索相关站点

* 哔哩轻小说
  * 搜索功能依赖两个 cookie: `cf_clearance` 与 `haha`
* 神凑轻小说
  * 搜索功能依赖 `cf_clearance` cookie
* 名著阅读
  * 搜索功能依赖 `cf_clearance` cookie
* 一笔阁
  * 搜索功能依赖 `cf_clearance` cookie

### 其他潜在站点

#### 中文

* [话本小说](https://www.ihuaben.com/)

  * 支持登录

* [米国度](https://www.myrics.com/)

  * 支持登录

* [52书库](https://www.52shuku.net/)

* [努努书坊](https://www.kanunu8.com/)

* [飞卢小说网](https://b.faloo.com/)

  * VIP 章节需登录访问

* [书海小说网](https://www.shuhai.com/)

  * VIP 章节需登录访问

* [连城读书](https://lcread.com/)

  * VIP 章节需登录访问

* [长佩文学](https://www.gongzicp.com/)

  * 所有章节需登录
  * 页面含加密字段 (需解析 `token` / `content`)

* [有毒小说网](https://www.youdubook.com/)

  * 所有章节需登录
  * 页面含加密字段 (需解析 `token` / `content`)

* [独阅读](https://www.cddaoyue.cn/)

  * VIP 章节需登录
  * 页面含加密字段 (需解析 `token` / `content`)

* [寒武纪年原创网](https://www.hanwujinian.com/)

  * VIP 章节需登录
  * 页面含加密字段 (需解析 `token` / `content`)

* [书耽](https://www.shubl.com/)

  * VIP 章节需登录
  * 页面含加密字段 (需解析 `token` / `content`)

* [晋江文学城](https://www.jjwxc.net/)

  * VIP 章节需登录

* [轻之国度](https://www.lightnovel.fun/)

  * 需登录
  * [备用](https://www.lightnovel.us/)

* [息壤中文网](https://www.xrzww.com/)

* [纵横中文网](https://www.zongheng.com/)

* [海棠小说网](https://m.haitangtxt.net/)

  * 需重新排序

* [海棠书屋](https://www.fdhxs.com/)

* [PO18 原创网](https://www.po18.tw/)

  * 需登录

* [半夏小说](https://www.xbanxia.cc/)

* 海棠文化線上文學城

  * [站点 1](https://ebook.longmabook.com/)
  * [站点 2](https://www.longmabookcn.com/)
  * [站点 3](https://ebook.lmbooks.com/)
  * [站点 4](https://www.lmebooks.com/)
  * [站点 5](https://www.haitbook.com/)
  * [站点 6](https://www.htwhbook.com/)
  * [站点 7](https://www.myhtebook.com/)
  * [站点 8](https://www.lovehtbooks.com/)
  * [站点 9](https://www.myhtebooks.com/)
  * [站点 10](https://www.myhtlmebook.com/)
  * [站点 11](https://jp.myhtebook.com/)
  * [站点 12](https://jp.myhtlmebook.com/)
  * [站点 13](https://ebook.urhtbooks.com/)
  * [站点 14](https://www.urhtbooks.com/)
  * [站点 15](https://www.newhtbook.com/)
  * [站点 16](https://www.lvhtebook.com/)
  * [站点 17](https://jp.lvhtebook.com/)
  * [站点 18](https://www.htlvbooks.com/)

* [完本神站](https://www.wanben.info/)

  * 站点的章节内容经常混杂 HTML 文本

* [全职小说网](https://www.quanzhifashi.com/)

  * 部分章节不全或无法访问
  * 部分书籍出现 `索引文件不存在！` 提示

* 笔趣阁

  * [站点 1](https://www.bqu9.cc/)
  * [站点 2](https://www.nibiqu.cc/)
  * [站点 3](https://m.chenkuan.com/)
    * 加载较慢，体验不佳
  * [站点 4](https://www.biquge.tw/)
  * [站点 5](https://www.beqege.cc/)
    * `curl_cffi`

* [笔趣趣](https://www.biququ.com/)

  * `curl_cffi`

* [燃火小说](https://www.ranwen.la/)

  * `curl_cffi`

* [42中文网](https://www.42zw.la/)

  * 部分章节不全或无法访问
  * 部分书籍出现 `索引文件不存在！` 提示

* [文海小说](https://www.zgzl.net/)

  * 加载较慢，体验不佳

* [小说之家](https://xszj.org/)

* [三五中文](https://m.mjyhb.com/)

* [帝书阁](https://www.23dishuge.com/)

* [大众文学](https://m.shauthor.com/)

* [小說之家](https://m.xszj.org/)

* [大灰狼小说聚合网](https://api.langge.cf/)

  * API 风格与当前框架不兼容，需要单独流程

* [99藏书网](https://www.99csw.com/)

  * 需提供 `cf_clearance` Cookie

* [真白萌](https://masiro.me/)

  * 需要登录
  * 需提供 `cf_clearance` Cookie

* [塔读文学](https://www.tadu.com/)

  * 部分章节需通过 APP 阅读

* [七猫中文网](https://www.qimao.com/)

  * 后续章节需 APP 免费阅读

* [得间小说](https://www.idejian.com/)

  * 后续章节需 APP 免费阅读

* [芒果书坊](https://mangguoshufang.com/)

  * 加载较慢，体验不佳

#### 日文

* [カクヨム](https://kakuyomu.jp/)
  * VIP 章节需登录访问
* [Novel Up Plus](https://novelup.plus/)

#### 英文

* [Asian Hobbyist](https://www.asianhobbyist.com/)
* [Asianovel](https://www.asianovel.net/)
* [BabelNovel](https://babelnovel.com/)
* [booknet](https://booknet.com/)
* [Chicken Gege](https://www.chickengege.org/)
* [Chrysanthemum Garden](https://chrysanthemumgarden.com)
* [Creative Novels](https://creativenovels.com)
* [Dreame](https://dreame.com)
* [Dummy Novels](https://dummynovels.com/)
* [Exiled Rebels Scanlations](https://exiledrebelsscanlations.com/)
* [FicFun](https://ficfun.com)
* [Foxaholic](https://foxaholic.com)
* [GoodNovel](https://www.goodnovel.com/)
* [Hosted Novel](https://hostednovel.com/)
* [ISO Translations](https://isotls.com)
* [Light Novels Translations](https://lightnovelstranslations.com)
* [LNMTL](https://lnmtl.com/)
* [MoonQuill](https://moonquill.com)
* [NovelBuddy](https://novelbuddy.com/)
* [Novel Full](https://novelfull.com)
* [Novelhall](https://novelhall.com)
* [Novel Updates](https://novelupdates.com)
* [Penana](https://www.penana.com/home.php)
* [Quotev](https://quotev.com)
* [Ranobes](https://ranobes.net/)
* [Re:Library](https://re-library.com)
* [ReadNovelFull](https://readnovelfull.com)
* [Wuxia & Light Novels](https://www.wuxiabox.com/)
* [Royal Road](https://royalroad.com)
* [Scribble Hub](https://scribblehub.com)
* [Second Life Translations](https://secondlifetranslations.com)
* [Snowy Codex](https://snowycodex.com/)
* [Tapas](https://tapas.io)
* [TapRead](https://tapread.com)
* [Truyen Full](https://truyenfull.vision/)
* [UntamedAlley](https://untamedalley.com/)
* [VipNovel](https://vipnovel.com/)
* [Volare Novels](https://volarenovels.com)
* [Wattpad](https://wattpad.com)
* [Webnovel](https://webnovel.com)
* [WoopRead](https://woopread.com/)
* [Wordrain](https://wordrain69.com)
* [WuxiaCity](https://wuxia.city)
* [WuXiaWorld](https://www.wuxiaworld.com/)
* [NovelBin](https://novelbin.com/)
* [NovelAll](https://allnovel.org/)
* [FreeWebNOVEL](https://freewebnovel.com/home)
* [Gray City](https://graycity.net/)
* [Hiraeth Translation](https://hiraethtranslation.com/)
* [Indowebnovel](https://indowebnovel.id/)
* [Lib Read](https://libread.com/)
* [MEIO Novel](https://meionovels.com/)
* [RiseNovel](https://risenovel.com/)
* [Novels Online](https://novelsonline.org/)
* [Paw Read](https://pawread.com/)
* [Read From Net](https://readfrom.net/)
* [Aakura Novel](https://sakuranovel.id/)
* [WTR-LAB](https://wtr-lab.com/en)
