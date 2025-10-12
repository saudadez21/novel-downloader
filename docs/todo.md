## TODO

以下为后续计划与优化方向

### 新增站点支持

* [刺猬猫](https://www.ciweimao.com/)
  * 网页端接口已基本解析完成，但 VIP 章节返回的为图片格式
  * 计划在有空时尝试使用 APP 端接口解决

### 广告过滤与章节标题归一化

* Parser 中已对常见第三方网站广告进行基础过滤
* 需要继续排查是否存在遗漏
* 章节名称格式归一化方案待设计 (作者习惯差异较大，如「第 1 章 标题」/「标题」/「第一章标题」等不一致格式)

### 已有站点维护

* **sfacg**
  * 可能因 `cookie expired` 导致失效
  * 需要考虑增加过期检测与重新获取机制 (暂未复现)

### EPUB 导出优化

* 目前主要瓶颈在于 `ziplib` 的写入以及图片缓存缺失时的下载
* 在缓存完整的情况下，`snakeviz` 分析结果显示 95% 以上耗时集中在 zip IO
* 可探索更高效的压缩/写入方式
* 排版与样式优化:
  * 目前导出的排版较为基础，整体观感有待提升
  * 不太擅长设计与排版，需要参考一些优秀的 EPUB 样本 (如字体层次、段落间距、封面与章节页布局等)

### CommonExporter 逻辑优化

* 当前导出逻辑在章节遍历、文件生成、资源整合等部分存在一定重复与分支判断，整体结构略显混乱
* 可考虑将通用导出流程抽象为模板方法 (Template Method Pattern)，通过定义可选覆盖的 hook 方法 (如 `_render_*` 系列函数) 实现定制化

### 对比 OpenCC 与 opencc-python

* 对比 [opencc-python](https://github.com/yichen0831/opencc-python) 与 [OpenCC](https://github.com/BYVoid/OpenCC) 的差异
* 字典更新与维护情况
* 转换性能表现
* 安装方式与兼容性

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

* [话本小说](https://www.ihuaben.com/)

  * 支持登录

* [101看书](https://101kanshu.com/)

  * 支持登录
  * 使用加密字体

* [轻之文库](https://www.linovel.net/)

  * 支持登录

* [米国度](https://www.myrics.com/)

  * 支持登录

* [西方奇幻小说网](https://www.westnovel.com/)

* [全职小说网](https://www.quanzhifashi.com/)

  * 支持登录

* [万相书城](https://wxsck.com/)

* [笔仙阁](https://www.bixiange.me/)

* [同人社](https://tongrenshe.cc/)

* [半夏小说](https://www.xbanxia.cc/)

* [小说狂人](https://czbooks.net/)

  * 支持登录

* [飞卢小说网](https://b.faloo.com/)

  * VIP 章节需登录访问

* [番茄小说网](https://fanqienovel.com/)

  * VIP 章节需登录访问
  * 使用加密字体

* [书海小说网](https://www.shuhai.com/)

  * VIP 章节需登录访问

* [若初文学网](https://www.ruochu.com/)

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

* [少年梦](https://www.shaoniandream.com/)

  * VIP 章节需登录
  * 页面含加密字段 (需解析 `token` / `content`)

* [书耽](https://www.shubl.com/)

  * VIP 章节需登录
  * 页面含加密字段 (需解析 `token` / `content`)

* [晋江文学城](https://www.jjwxc.net/)

  * VIP 章节需登录

* [息壤中文网](https://www.xrzww.com/)

* [纵横中文网](https://www.zongheng.com/)

* [海棠小说网](https://m.haitangtxt.net/)

  * 需重新排序

* [爱丽丝书屋](https://www.alicesw.com/)

* [海外书包](https://www.haiwaishubao.com/)

  * 需手动清理 `&esp;`

* [有爱爱](https://www.uaa.com/)

  * 需登录

* [PO18 原创网](https://www.po18.tw/)

  * 需登录

* [大灰狼小说聚合网](https://api.langge.cf/)

  * API 风格与当前框架不兼容，需要单独流程

* [99藏书网](https://www.99csw.com/)

  * 需提供 `cf_clearance` Cookie

* [轻小说文库](https://www.wenku8.net/)

  * 需提供 `cf_clearance` cookie

* [塔读文学](https://www.tadu.com/)

  * 部分章节需通过 APP 阅读

* [七猫中文网](https://www.qimao.com/)

  * 后续章节需 APP 免费阅读

* [得间小说](https://www.idejian.com/)

  * 后续章节需 APP 免费阅读

* [芒果书坊](https://mangguoshufang.com/)

  * 加载较慢，体验不佳

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
