## TODO

以下为后续计划与优化方向

### 新增站点支持

* [刺猬猫](https://www.ciweimao.com/)
  * 网页端接口已基本解析完成，但 VIP 章节返回的为图片格式
  * 计划在有空时尝试使用 APP 端接口解决
* [轻小说文库](https://www.wenku8.net/)
  * 需提供 `cf_clearance` cookie

### 广告过滤与章节标题归一化

* Parser 中已对常见第三方网站广告进行基础过滤
* 需要继续排查是否存在遗漏
* 章节名称格式归一化方案待设计 (作者习惯差异较大，如「第 1 章 标题」/「标题」/「第一章标题」等不一致格式)

### 已有站点维护

* **sfacg**
  * 可能因 `cookie expired` 导致失效
  * 需要考虑增加过期检测与重新获取机制 (暂未复现)

### Parser 优化

* 整理 `wanbengo` 的垃圾信息过滤逻辑
* 检查与优化部分章节的解析逻辑
* 保持兼容性的同时减少冗余处理
* 去除章节标题的 fallback 逻辑:
  * 当前逻辑为 `title = f"第 {chapter_id} 章"`
  * 调整为若缺失标题则交由导出函数使用目录页章节标题

### EPUB 导出优化

* 目前主要瓶颈在于 `ziplib` 的写入以及图片缓存缺失时的下载
* 在缓存完整的情况下，`snakeviz` 分析结果显示 95% 以上耗时集中在 zip IO
* 可探索更高效的压缩/写入方式

### 命令行交互

* 在未输入 sub-command 时提供 TUI 界面，提升可用性
* 整理并精简命令行参数
* 支持 `--export-stage=<stage>` 手动选择导出阶段 (用于覆盖自动推断)

### 导出模板支持

* 增加可定制的导出模板（基于 `Jinja2`）

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

* [次元姬](https://www.ciyuanji.com/)
* [轻之国度](https://www.lightnovel.fun)
* [米国度](https://www.myrics.com/)
* [息壤中文网](https://www.xrzww.com/)
* [有毒小说网](https://www.youdubook.com/)
* [纵横中文网](https://www.zongheng.com/)
* [69书吧](https://www.69shuba.com/)
  * 几乎所有请求都需要 Cloudflare 验证

#### 日文

* [暁](https://www.akatsuki-novels.com/)
* [カクヨム](https://kakuyomu.jp/)
* [Novel Up Plus](https://novelup.plus/)
* [小説家になろう](https://syosetu.com/)
* [ハーメルン](https://syosetu.org/)
* [ラブノベ](https://lovenove.syosetu.com/)
* [ムーンライトノベルズ](https://mnlt.syosetu.com/top/top/)
* [ノクターンノベルズ](https://noc.syosetu.com/top/top/)
* [小説を読もう！](https://yomou.syosetu.com/)

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
