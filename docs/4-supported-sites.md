## 站点支持

### 目录

- [站点支持](#站点支持)
  - [目录](#目录)
  - [关键词搜索（Search）](#关键词搜索search)
  - [表格说明](#表格说明)
  - [支持站点总览](#支持站点总览)
    - [主流原创 / 正版文学平台](#主流原创--正版文学平台)
    - [轻小说 / 二次元向平台](#轻小说--二次元向平台)
    - [综合书库 / 文库与名著](#综合书库--文库与名著)
    - [类笔趣阁 / 第三方转载站](#类笔趣阁--第三方转载站)
    - [同人](#同人)
    - [限制级](#限制级)
    - [已归档站点](#已归档站点)
  - [站点详解与 Book ID 规则](#站点详解与-book-id-规则)
    - [主流原创 / 正版文学平台](#主流原创--正版文学平台-1)
    - [轻小说 / 二次元向平台](#轻小说--二次元向平台-1)
    - [综合书库 / 文库与名著](#综合书库--文库与名著-1)
    - [类笔趣阁 / 第三方转载站](#类笔趣阁--第三方转载站-1)
    - [同人](#同人-1)
    - [限制级](#限制级-1)
    - [已归档站点](#已归档站点-1)
  - [配置文件](#配置文件)
  - [Cookie 与登录](#cookie-与登录)
    - [在配置中保存账号信息](#在配置中保存账号信息)
  - [注意事项](#注意事项)

---

### 关键词搜索（Search）

```bash
# 根据关键词搜索 (默认全站点)
novel-cli search 关键词

# 指定站点
novel-cli search --site b520 三体
```

---

### 表格说明

* **站点名称**: 支持的小说网站
* **站点标识符**: CLI `--site` 与配置文件使用的短名称
* **支持分卷**: 可识别并抓取分卷结构
* **支持图片**: 可抓取章节插图并嵌入 EPUB
* **支持登录**: 站点需要登录 (如书架/VIP/订阅)
* **支持搜索**: 可通过关键词检索该站点
* **支持语言**: 站点主要语言 (简/繁)

> 图例: ✅ 已支持; ❌ 不支持; ⚠️ 尚未在本库实现

---

### 支持站点总览

**使用示例**

```bash
novel-cli download https://www.hetushu.com/book/5763/index.html
novel-cli download https://www.23qb.com/book/12282/

novel-cli download --site qidian 1010868264
novel-cli download --site n23qb 12282
novel-cli download --site ttkan shengxu-chendong
```

#### 主流原创 / 正版文学平台

> 官方原创或具备正版渠道的平台

| 站点名称                                                     | 站点标识符 | 支持分卷 | 支持图片 | 支持登录 | 支持搜索 | 支持语言 |
| ----------------------------------------------------------- | --------- | ------- | ------- | ------- | ------- | ------- |
| [起点中文网](https://www.qidian.com)                         | qidian    | ✅     | ❌     | ✅     | ✅     | 简      |
| [QQ阅读](https://book.qq.com/)                               | qqbook    | ❌     | ❌     | ✅     | ⚠️     | 简      |

#### 轻小说 / 二次元向平台

> 专注轻小说、幻想、异世界、恋爱等题材的网站

| 站点名称                                                     | 站点标识符 | 支持分卷 | 支持图片 | 支持登录 | 支持搜索 | 支持语言 |
| ----------------------------------------------------------- | --------- | ------- | ------- | ------- | ------- | ------- |
| [次元姬](https://www.ciyuanji.com/)                          | ciyuanji  | ✅     | ✅     | ✅     | ✅     | 简      |
| [SF轻小说](https://m.sfacg.com)                              | sfacg      | ✅     | ✅     | ✅     | ⚠️     | 简      |
| [轻之文库](https://www.linovel.net/)                         | linovel    | ✅     | ✅     | ⚠️     | ✅     | 简      |
| [三七轻小说](https://www.37yq.com/)                          | n37yq      | ✅     | ✅     | ⚠️     | ✅     | 简      |
| [哔哩轻小说](https://www.linovelib.com/)                     | linovelib  | ✅     | ✅     | ⚠️     | ⚠️     | 简      |
| [ESJ Zone](https://www.esjzone.cc)                           | esjzone   | ✅     | ✅     | ✅     | ✅     | 简      |
| [神凑轻小说](https://www.shencou.com/)                        | shencou   | ✅     | ✅     | ⚠️     | ⚠️     | 简      |
| [轻小说百科](https://lnovel.org/)                             | lnovel    | ✅     | ✅     | ⚠️     | ⚠️     | 简 / 繁 |
| [无限轻小说](https://www.8novel.com/)                         | n8novel   | ✅     | ✅     | ⚠️     | ✅     | 繁      |

#### 综合书库 / 文库与名著

> 综合阅读与名著文库类站点

| 站点名称                                                     | 站点标识符 | 支持分卷 | 支持图片 | 支持登录 | 支持搜索 | 支持语言 |
| ----------------------------------------------------------- | --------- | ------- | ------- | ------- | ------- | ------- |
| [有度中文网](https://www.yodu.org/)                          | yodu      | ✅     | ⚠️     | ⚠️     | ✅     | 简      |
| [名著阅读](https://b.guidaye.com/)                           | guidaye   | ❌     | ❌     | ❌     | ⚠️     | 简      |
| [鲲弩小说](https://www.kunnu.com/)                           | kunnu     | ✅     | ❌     | ❌     | ❌     | 简      |
| [西方奇幻小说网](https://www.westnovel.com/)                 | westnovel | ❌     | ❌     | ❌     | ⚠️     | 简     |
| [西方奇幻小说网子站点](https://www.westnovel.com/)        | westnovel_sub | ❌     | ❌     | ❌     | ⚠️     | 简     |

#### 类笔趣阁 / 第三方转载站

> 以转载/聚合为主的民间小说站

| 站点名称                                                     | 站点标识符 | 支持分卷 | 支持图片 | 支持登录 | 支持搜索 | 支持语言 |
| ----------------------------------------------------------- | --------- | ------- | ------- | ------- | ------- | ------- |
| [和图书](https://www.hetushu.com/index.php)                  | hetushu   | ✅     | ❌     | ❌     | ✅     | 简 / 繁 |
| [铅笔小说](https://www.23qb.com)                             | n23qb     | ✅     | ❌     | ⚠️     | ✅     | 简      |
| [飘天文学网](https://www.piaotia.com/)                        | piaotia  | ❌     | ❌     | ⚠️     | ✅     | 简      |
| [新吾爱文学](https://www.71ge.com/)                           | n71ge    | ❌     | ❌     | ⚠️     | ✅     | 简      |
| [精品小说网](https://www.jpxs123.com/)                        | jpxs123  | ❌     | ❌     | ❌     | ✅     | 简      |
| [天天看小说](https://www.ttkan.co/)                          | ttkan     | ❌     | ❌     | ❌     | ✅     | 简 / 繁 |
| [爱下电子书](https://ixdzs8.com/)                             | ixdzs8   | ❌     | ❌     | ⚠️     | ✅     | 简      |
| [大熊猫文学网](https://www.dxmwx.org/)                        | dxmwx    | ❌     | ❌     | ❌     | ✅     | 简 / 繁 |
| [25中文网](https://www.i25zw.com/)                           | i25zw     | ❌     | ❌     | ❌     | ✅     | 简      |
| [69阅读](https://www.69yue.top/index.html)                   | n69yue    | ❌     | ❌     | ⚠️     | ✅     | 简      |
| [101看书](https://101kanshu.com/)                           | n101kanshu | ❌     | ❌     | ⚠️     | ✅     | 繁      |
| [老幺小说网](https://www.laoyaoxs.org/)                     | laoyaoxs  | ❌     | ❌     | ❌     | ✅     | 简      |
| [全本小说网](https://quanben5.com/)                          | quanben5  | ❌     | ❌     | ❌     | ✅     | 简 / 繁 |
| [书林文学](http://shu111.com)                                | shu111    | ❌     | ❌     | ⚠️     | ❌     | 简      |
| [笔趣阁](http://www.b520.cc)                                 | b520      | ❌     | ❌     | ⚠️     | ✅     | 简      |
| [书海阁小说网](https://www.shuhaige.net/)                     | shuhaige | ❌     | ❌     | ⚠️     | ✅     | 简      |
| [小说虎](https://www.xshbook.com/)                           | xshbook   | ❌     | ❌     | ⚠️     | ✅     | 简      |
| [顶点小说网](https://www.23ddw.net/)                         | n23ddw    | ❌     | ❌     | ❌     | ✅     | 简      |
| [一笔阁](https://www.yibige.org/)                            | yibige    | ❌     | ❌     | ⚠️     | ⚠️     | 简 / 繁 |
| [乐文小说网](https://www.lewenn.net/)                        | lewenn    | ❌     | ❌     | ⚠️     | ❌     | 简      |
| [笔趣读](https://www.blqudu.cc/)                             | blqudu    | ❌     | ❌     | ⚠️     | ❌     | 简      |
| [追书网](https://www.mangg.com/) (com)                       | mangg_com | ❌     | ❌     | ⚠️     | ❌     | 简      |
| [追书网](https://www.mangg.net/) (net)                       | mangg_net | ❌     | ❌     | ❌     | ✅     | 简      |
| [笔趣阁](https://www.fsshu.com/)                             | fsshu    | ❌     | ❌     | ⚠️     | ✅     | 简      |
| [笔趣阁](https://www.biquge5.com/)                           | biquge5  | ❌     | ❌     | ⚠️     | ✅     | 简      |
| [笔趣阁小说网](https://www.biquguo.com/)                      | biquguo  | ❌     | ❌     | ⚠️     | ✅     | 简      |
| [思路客](https://www.ciluke.com/)                            | ciluke   | ❌     | ❌     | ⚠️     | ✅     | 简      |
| [八一中文网](https://www.ktshu.cc/)                           | ktshu    | ❌     | ❌     | ⚠️     | ✅     | 简      |
| [37阅读网](https://www.37yue.com/)                           | n37yue   | ❌     | ❌     | ⚠️     | ✅     | 简      |
| [笔下文学网](https://www.bxwx9.org/)                          | bxwx9    | ❌     | ❌     | ⚠️     | ✅     | 简      |

#### 同人

> 以同人、百合、纯爱等衍生原创为主

| 站点名称                                                     | 站点标识符 | 支持分卷 | 支持图片 | 支持登录 | 支持搜索 | 支持语言 |
| ----------------------------------------------------------- | --------- | ------- | ------- | ------- | ------- | ------- |
| [百合会](https://www.yamibo.com/site/novel)                  | yamibo     | ✅     | ❌     | ✅     | ⚠️     | 简      |
| [镇魂小说网](https://www.zhenhunxiaoshuo.com/)           | zhenhunxiaoshuo | ❌     | ❌     | ❌     | ⚠️     | 简      |
| [同人圈](https://www.tongrenquan.org/)                      | tongrenquan | ❌     | ❌     | ❌     | ✅     | 简      |
| [同人小说网](https://www.trxs.cc/)                           | trxs        | ❌     | ❌     | ❌     | ✅     | 简      |
| [全本同人小说](https://www.qbtr.cc/)                         | qbtr        | ❌     | ❌     | ❌     | ✅     | 简      |

#### 限制级

| 站点名称                                                     | 站点标识符 | 支持分卷 | 支持图片 | 支持登录 | 支持搜索 | 支持语言 |
| ----------------------------------------------------------- | --------- | ------- | ------- | ------- | ------- | ------- |
| [3A电子书](http://www.aaatxt.com/)                           | aaatxt     | ❌     | ❌     | ⚠️     | ✅     | 简      |
| [西瓜书屋](https://www.xiguashuwu.com/)                      | xiguashuwu | ❌     | ❌     | ⚠️     | ✅     | 简      |

#### 已归档站点

| 站点名称                                                     | 站点标识符 | 支持分卷 | 支持图片 | 支持登录 | 支持搜索 | 支持语言 |
| ----------------------------------------------------------- | --------- | ------- | ------- | ------- | ------- | ------- |
| [笔趣阁](https://www.8tsw.com/)                              | n8tsw     | ❌     | ❌     | ⚠️     | ⚠️     | 简      |
| [精彩小说](https://biquyuedu.com/)                           | biquyuedu | ❌     | ❌     | ⚠️     | ❌     | 简      |
| [得奇小说网](https://www.deqixs.com/)                        | deqixs    | ❌     | ❌     | ❌     | ✅     | 简      |
| [小说屋](http://www.xiaoshuoge.info/)                       | xiaoshuoge | ❌     | ❌     | ⚠️     | ✅     | 简      |
| [小说路上](https://m.xs63b.com/)                              | xs63b    | ❌     | ❌     | ⚠️     | ✅     | 简      |
| [完本神站](https://www.wanbengo.com/)                        | wanbengo  | ❌     | ❌     | ⚠️     | ✅     | 简      |

---

### 站点详解与 Book ID 规则

> **说明**: Book ID 通常来源于小说详情页 URL 的路径段; Chapter ID 来自章节页 URL。
>
> 下文对每个站点给出示例 URL -> 对应 ID以及注意。

#### 主流原创 / 正版文学平台

* **起点中文网 (qidian)**
  * 书籍: `https://www.qidian.com/book/1010868264/` -> Book ID: `1010868264`
  * 章节: `https://www.qidian.com/chapter/1010868264/405976997/` -> Chapter ID: `405976997`
  * 登录: 需要有效 Cookie
  * 其它:
    * 章节存在重复内容时请在 `settings.toml` 中该站点 (`[sites.qidian]`) 的 `use_truncation` 为 `true`。
    * 近月更新章节可能使用字体加密, 可按需开启解密字体 (`decode_font` 参数)

* **QQ 阅读 (qqbook)**
  * 书籍: `https://book.qq.com/book-detail/41089201` -> Book ID: `41089201`
  * 章节: `https://book.qq.com/book-read/41089201/1` -> Chapter ID: `1`
  * 登录: 需要有效 Cookie
  * 其它:
    * VIP 章节解析需要额外安装 [Node.js](https://nodejs.org/en/download)
    * VIP 章节可能使用字体加密, 可按需开启解密字体 (`decode_font` 参数)

#### 轻小说 / 二次元向平台

* **次元姬 (ciyuanji)**
  * 书籍: `https://www.ciyuanji.com/b_d_12030.html` -> Book ID: `12030`
  * 章节: `https://www.ciyuanji.com/chapter/12030_3046684.html` -> Chapter ID: `3046684`
  * 登录: 需要有效 Cookie
  * 其它:
    * 若请求间隔过短, 服务器可能返回上一次请求的页面内容 (缓存或防爬机制导致)
    * 建议在请求之间设置合理的延迟

* **SF 轻小说 (sfacg)**
  * 书籍: `https://m.sfacg.com/b/456123/` -> Book ID: `456123`
  * 章节: `https://m.sfacg.com/c/5417665/` -> Chapter ID: `5417665`
  * 登录: 需提供有效的 Cookie 才能访问订阅章节。
  * 其它:
    * VIP 章节以图片形式返回, 可通过开启 `decode_font` 参数配合 OCR 识别为文本。
    * OCR 识别结果并非完全可靠, 准确率大约在 **80%+**, 可能存在错误或缺字。
    * OCR 运算在 CPU 环境下较为耗时, 解析 VIP 章节速度会明显变慢, 建议在具备 GPU 的环境中运行。

* **轻之文库 (linovel)**
  * 书籍: `https://www.linovel.net/book/101752.html` -> Book ID: `101752`
  * 章节: `https://www.linovel.net/book/101752/16996.html` -> Chapter ID: `101752`
  * 已知问题:
    * 图片资源可能偶尔无法正常加载或失效

* **三七轻小说 (n37yq)**
  * 书籍: `https://www.37yq.com/lightnovel/2362.html` -> Book ID: `2362`
  * 章节: `https://www.37yq.com/lightnovel/2362/92560.html` -> Chapter ID: `92560`

* **哔哩轻小说 (linovelib)**
  * 书籍: `https://www.linovelib.com/novel/1234.html` -> Book ID: `1234`
  * 章节: `https://www.linovelib.com/novel/1234/47800.html` -> Chapter ID: `47800`
  * 风控: 请求过于频繁可能触发限制, 导致封禁或限流 (推荐请求间隔大于 2 秒)

* **无限轻小说 (n8novel)**
  * 书籍: `https://www.8novel.com/novelbooks/3365/` -> Book ID: `3365`
  * 章节: `https://article.8novel.com/read/3365/?106235` -> Chapter ID: `106235`

* **ESJ Zone (esjzone)**
  * 书籍: `https://www.esjzone.cc/detail/1660702902.html` -> Book ID: `1660702902`
  * 章节: `https://www.esjzone.cc/forum/1660702902/294593.html` -> Chapter ID: `294593`
  * 注意:
    * 未完成登录验证时, 部分页面会自动重定向至「論壇」页面导致内容加载失败。
    * 若章节设有访问密码, 请先在网页端输入并解锁后, 再开始下载。

* **神凑轻小说 (shencou)**
  * 书籍: `https://www.shencou.com/read/3/3540/index.html` -> Book ID: `3-3540`
  * 章节: `https://www.shencou.com/read/3/3540/156328.html` -> Chapter ID: `156328`
  * 目录访问:
    * 先打开详细页面 (如 `https://www.shencou.com/books/read_3540.html`), 再点击 "小说目录" 查看
  * 已知问题:
    * 图片资源可能无法正常加载或失效
    * 目录页中仍保留了一些已删除章节的重复条目, 却未同步删除

* **轻小说百科 (lnovel)**
  * 书籍: `https://lnovel.org/books-3638` -> Book ID: `3638`
  * 章节: `https://lnovel.org/chapters-138730` -> Chapter ID: `138730`

#### 综合书库 / 文库与名著

* **和图书 (hetushu)**
  * 书籍: `https://www.hetushu.com/book/5763/index.html` -> Book ID: `5763`
  * 章节: `https://www.hetushu.com/book/5763/4327466.html` -> Chapter ID: `4327466`

* **有度中文网 (yodu)**
  * 书籍: `https://www.yodu.org/book/18862/` -> Book ID: `18862`
  * 章节: `https://www.yodu.org/book/18862/4662939.html` -> Chapter ID: `4662939`
  * 已知问题:
    * 图片资源可能无法加载 (404)

* **名著阅读 (guidaye)**
  * 书籍: `https://b.guidaye.com/kongbu/654/` -> Book ID: `kongbu-654`
  * 章节: `https://b.guidaye.com/kongbu/654/170737.html` -> Chapter ID: `170737`

* **鲲弩小说 (kunnu)**
  * 书籍: `https://www.kunnu.com/guichui/` -> Book ID: `guichui`
  * 章节: `https://www.kunnu.com/guichui/27427.htm` -> Chapter ID: `27427`

* **西方奇幻小说网 (westnovel)**
  * 书籍: `https://www.westnovel.com/ksl/sq/` -> Book ID: `ksl-sq`
  * 章节: `https://www.westnovel.com/ksl/sq/140072.html` -> Chapter ID: `140072`

* **西方奇幻小说网子站点 (westnovel_sub)**
  * 书籍: `https://www.westnovel.com/q/list/725.html` -> Book ID: `q-list-725`
  * 章节: `https://www.westnovel.com/q/showinfo-2-40238-0.html` -> Chapter ID: `2-40238-0`

#### 类笔趣阁 / 第三方转载站

* **铅笔小说 (n23qb)**
  * 书籍: `https://www.23qb.com/book/12282/` -> Book ID: `12282`
  * 章节: `https://www.23qb.com/book/12282/7908999.html` -> Chapter ID: `7908999`

* **飘天文学网 (piaotia)**
  * 书籍: `https://www.piaotia.com/bookinfo/1/1705.html` -> Book ID: `1-1705`
  * 章节: `https://www.piaotia.com/html/1/1705/762992.html` -> Chapter ID: `762992`

* **新吾爱文学 (n71ge)**
  * 书籍: `https://www.71ge.com/65_65536/` -> Book ID: `65_65536`
  * 章节: `https://www.71ge.com/65_65536/1.html` -> Chapter ID: `1`

* **精品小说网 (jpxs123)**
  * 书籍: `https://www.jpxs123.com/xh/zhetian.html` -> Book ID: `xh-zhetian`
  * 章节: `https://www.jpxs123.com/xh/zhetian/1.html` -> Chapter ID: `1`
  * 注意: 该站点直接提供 txt 下载。

* **爱下电子书 (ixdzs8)**
  * 书籍: `https://ixdzs8.com/read/38804/` -> Book ID: `38804`
  * 章节: `https://ixdzs8.com/read/38804/p1.html` -> Chapter ID: `p1`

* **大熊猫文学网 (dxmwx)**
  * 书籍: `https://www.dxmwx.org/book/55598.html` -> Book ID: `55598`
  * 章节: `https://www.dxmwx.org/read/55598_47170737.html` -> Chapter ID: `47170737`

* **25中文网 (i25zw)**
  * 书籍: `https://www.i25zw.com/book/64371.html` -> Book ID: `64371`
  * 章节: `https://www.i25zw.com/64371/153149757.html` -> Chapter ID: `153149757`

* **69阅读 (n69yue)**
  * 书籍: `https://www.69yue.top/articlecategroy/15yu.html` -> Book ID: `15yu`
  * 章节: `https://www.69yue.top/article/15185363014257741.html` -> Chapter ID: `15185363014257741`

* **101看书 (n101kanshu)**
  * 书籍: `https://101kanshu.com/book/7994.html` -> Book ID: `7994`
  * 章节: `https://101kanshu.com/txt/7994/9137080.html` -> Chapter ID: `9137080`

* **老幺小说网 (laoyaoxs)**
  * 书籍: `https://www.laoyaoxs.org/info/7359.html` -> Book ID: `7359`
  * 章节: `https://www.laoyaoxs.org/list/7359/21385.html` -> Chapter ID: `21385`

* **书林文学 (shu111)**
  * 书籍: `http://www.shu111.com/book/282944.html` -> Book ID: `282944`
  * 章节: `http://www.shu111.com/book/282944/96171674.html` -> Chapter ID: `96171674`
  * 注意: 网站加载速度较慢

* **全本小说网 (quanben5)**
  * 书籍: `https://quanben5.com/n/doushentianxia/` -> Book ID: `doushentianxia`
  * 章节: `https://quanben5.com/n/doushentianxia/13685.html` -> Chapter ID: `13685`

* **天天看小說 (ttkan)**
  * 书籍: `https://www.ttkan.co/novel/chapters/shengxu-chendong` -> Book ID: `shengxu-chendong`
  * 章节: `https://www.wa01.com/novel/pagea/shengxu-chendong_1.html` -> Chapter ID: `1`

* **笔趣阁 (b520)**
  * 书籍: `http://www.b520.cc/8_8187/` -> Book ID: `8_8187`
  * 章节: `http://www.b520.cc/8_8187/3899831.html` -> Chapter ID: `3899831`

* **书海阁小说网 (shuhaige)**
  * 书籍: `https://www.shuhaige.net/199178/` -> Book ID: `199178`
  * 章节: `https://www.shuhaige.net/199178/86580492.html` -> Chapter ID: `86580492`

* **小说虎 (xshbook)**
  * 书籍: `https://www.xshbook.com/95139/95139418/` -> Book ID: `95139-95139418`
  * 章节: `https://www.xshbook.com/95139/95139418/407988281.html` -> Chapter ID: `407988281`

* **一笔阁 (yibige)**
  * 书籍: `https://www.yibige.org/6238/` -> Book ID: `6238`
  * 章节: `https://www.yibige.org/6238/1.html` -> Chapter ID: `1`

* **乐文小说网 (lewenn)**
  * 书籍: `https://www.lewenn.net/lw1/` -> Book ID: `lw1`
  * 章节: `https://www.lewenn.net/lw1/30038546.html` -> Chapter ID: `30038546`
  * 其它: 该站点的搜索结果是 `3A小说网` 的...

* **笔趣读 (blqudu)**
  * 书籍: `https://www.blqudu.cc/137_137144/` -> Book ID: `137_137144`
  * 章节: `https://www.biqudv.cc/137_137144/628955328.html` -> Chapter ID: `628955328`
  * 注意: 大部分书籍的最后几章都不完整

* **顶点小说网 (n23ddw)**
  * 书籍: `https://www.23ddw.net/du/80/80892/` -> Book ID: `80-80892`
  * 章节: `https://www.23ddw.net/du/80/80892/13055110.html` -> Chapter ID: `13055110`

* **追书网.com (mangg_com)**
  * 书籍: `https://www.mangg.com/id57715/` -> Book ID: `id57715`
  * 章节: `https://www.mangg.com/id57715/632689.html` -> Chapter ID: `632689`

* **追书网.net (mangg_net)**
  * 书籍: `https://www.mangg.net/id26581/` -> Book ID: `id26581`
  * 章节: `https://www.mangg.net/id26581/1159408.html` -> Chapter ID: `1159408`

* **笔趣阁 (fsshu)**
  * 书籍: `https://www.fsshu.com/biquge/0_139/` -> Book ID: `0_139`
  * 章节: `https://www.fsshu.com/biquge/0_139/c40381.html` -> Chapter ID: `c40381`

* **笔趣阁 (biquge5)**
  * 书籍: `https://www.biquge5.com/9_9194/` -> Book ID: `9_9194`
  * 章节: `https://www.biquge5.com/9_9194/737908.html` -> Chapter ID: `737908`

* **笔趣阁小说网 (biquguo)**
  * 书籍: `https://www.biquguo.com/0/352/` -> Book ID: `0-352`
  * 章节: `https://www.biquguo.com/0/352/377618.html` -> Chapter ID: `377618`

* **思路客 (ciluke)**
  * 书籍: `https://www.ciluke.com/19/19747/` -> Book ID: `19-19747`
  * 章节: `https://www.ciluke.com/19/19747/316194.html` -> Chapter ID: `316194`

* **八一中文网 (ktshu)**
  * 书籍: `https://www.ktshu.cc/book/47244/` -> Book ID: `47244`
  * 章节: `https://www.ktshu.cc/book/47244/418953.html` -> Chapter ID: `418953`

* **37阅读网 (n37yue)**
  * 书籍: `https://www.37yue.com/0/180/` -> Book ID: `0-180`
  * 章节: `https://www.37yue.com/0/180/164267.html` -> Chapter ID: `164267`

* **笔下文学网 (bxwx9)**
  * 书籍: `https://www.bxwx9.org/b/48/48453/` -> Book ID: `48-48453`
  * 章节: `https://www.bxwx9.org/b/48/48453/175908.html` -> Chapter ID: `175908`

#### 同人

* **百合会 (yamibo)**
  * 书籍: `https://www.yamibo.com/novel/262117` -> Book ID: `262117`
  * 章节: `https://www.yamibo.com/novel/view-chapter?id=38772952` -> Chapter ID: `38772952`

* **镇魂小说网 (zhenhunxiaoshuo)**
  * 书籍: `https://www.zhenhunxiaoshuo.com/modaozushi/` -> Book ID: `modaozushi`
  * 章节: `https://www.zhenhunxiaoshuo.com/5419.html` -> Chapter ID: `5419`

* **同人圈 (tongrenquan)**
  * 书籍: `https://www.tongrenquan.org/tongren/7548.html` -> Book ID: `7548`
  * 章节: `https://www.tongrenquan.org/tongren/7548/1.html` -> Chapter ID: `1`

* **同人小说网 (trxs)**
  * 书籍: `https://www.trxs.cc/tongren/6201.html` -> Book ID: `6201`
  * 章节: `https://www.trxs.cc/tongren/6201/1.html` -> Chapter ID: `1`

* **全本同人小说 (qbtr)**
  * 书籍: `https://www.qbtr.cc/tongren/8978.html` -> Book ID: `tongren-8978`
  * 章节: `https://www.qbtr.cc/tongren/8978/1.html` -> Chapter ID: `1`
  * 注意: 该站点直接提供 txt 下载。

#### 限制级

* **3A电子书 (aaatxt)**
  * 书籍: `http://www.aaatxt.com/shu/24514.html` -> Book ID: `24514`
  * 章节: `http://www.aaatxt.com/yuedu/24514_1.html` -> Chapter ID: `24514_1`
  * 注意: 该站点直接提供 txt 下载。

* **西瓜书屋 (xiguashuwu)**
  * 书籍: `https://www.xiguashuwu.com/book/1234/iszip/1/` -> Book ID: `1234`
  * 章节: `https://www.xiguashuwu.com/book/1234/482.html` -> Chapter ID: `482`

#### 已归档站点

* **笔趣阁 (n8tsw)**
  * 书籍: `https://www.8tsw.com/0_1/` -> Book ID: `0_1`
  * 章节: `https://www.8tsw.com/0_1/1.html` -> Chapter ID: `1`

* **精彩小说 (biquyuedu)**
  * 书籍: `https://biquyuedu.com/novel/GDr1I1.html` -> Book ID: `GDr1I1`
  * 章节: `https://biquyuedu.com/novel/GDr1I1/1.html` -> Chapter ID: `1`

* **得奇小说网 (deqixs)**
  * 书籍: `https://www.deqixs.com/xiaoshuo/2026/` -> Book ID: `2026`
  * 章节: `https://www.deqixs.com/xiaoshuo/2026/1969933.html` -> Chapter ID: `1969933`
  * 注意: 该站点直接提供 txt 下载。
  * 缺点: 每章节分页过多, 每页内容较少, 推荐适当降低请求间隔

* **小说屋 (xiaoshuoge)**
  * 书籍: `http://www.xiaoshuoge.info/html/987/987654/` -> Book ID: `987-987654`
  * 章节: `http://www.xiaoshuoge.info/html/987/987654/123456789.html` -> Chapter ID: `123456789`

* **小说路上 (xs63b)**
  * 书籍: `https://m.xs63b.com/xuanhuan/aoshijiuzhongtian/` -> Book ID: `xuanhuan-aoshijiuzhongtian`
  * 章节: `https://m.xs63b.com/xuanhuan/aoshijiuzhongtian/8748062.html` -> Chapter ID: `8748062`
  * 注意: 桌面端页面部分章节缺页, 移动端正常

* **完本神站 (wanbengo)**
  * 书籍: `https://www.wanbengo.com/1/` -> Book ID: `1`
  * 章节: `https://www.wanbengo.com/1/2.html` -> Chapter ID: `2`
  * 归档原因: 页面内容存在严重质量问题, 包括但不限于
    * 乱码过多: 例如 `?j\i~n￠j^i?a` 或多段连续无意义字符, 导致正文可读性极差
    * 结构混乱: HTML 标签嵌套不规范, 正文段落交错混乱
    * 来源异常: 文本中混入大量 HTML 实体, 以及明显来自其他小说网站的段落

---

### 配置文件

在 `settings.toml` 中为目标站点添加书籍 ID 与登录方式:

```toml
# 以站点名为键, <site_name> 请替换为具体站点标识
[sites.<site_name>]
book_ids = [
  "0000000000",
  "0000000000"
]
login_required = false  # 需要登录时改为 true

# 若需要登录, 可按需补充:
# username = "yourusername"
# password = "yourpassword"
```

示例: 下载 linovelib 的书籍

```toml
[sites.linovelib]
book_ids = [
  "1234"
]
login_required = false
```

配合 cli 直接下载:

```bash
novel-cli download --site linovelib
```

> 当命令行中同时传入 Book ID 时, 该 ID 会覆盖 `settings.toml` 中对应站点的 `book_ids` 设置

---

### Cookie 与登录

如需通过 Cookie 登录:
1. 可在浏览器登录后
2. 打开开发者工具 (F12) 复制完整的 Cookie 字符串 (详见 [复制 Cookies](./copy-cookies.md))

当前基于会话的 Cookie 不支持自动续期, 每次运行如果过期需手动更新。后续版本将考虑优化此流程。

也可使用内置脚本在浏览器中完成登录并保存会话:

```bash
# 通用登录脚本
python ./scripts/login_scripts/login.py qidian

# 专用于 ESJ Zone 的登录
python ./scripts/login_scripts/esjzone_login.py -u username -p password
```

脚本依赖 Playwright, 请先安装并初始化浏览器内核:

```bash
pip install playwright
playwright install
```

#### 在配置中保存账号信息

对于 ESJ Zone 和 百合会 等需要登录才能获取内容的站点, 可在 `settings.toml` 中开启登录并填写账号信息 (或在运行时按提示输入):

```toml
[sites.<site_name>]
book_ids = [
  "0000000000",
  "0000000000"
]
login_required = true
username = "yourusername"     # 登录账户
password = "yourpassword"     # 登录密码
```

---

### 注意事项

- **站点结构变更**: 若目标站点页面结构更新或章节抓取异常, 欢迎提 Issue 或提交 PR
- **登录支持范围**: 登录功能受站点策略与接口限制, 部分场景需要手动配置 Cookie 或进行账号绑定
- **请求频率**: 请合理设置抓取间隔, 避免触发风控或导致 IP 限制
