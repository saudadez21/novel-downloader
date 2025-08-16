## 站点支持

### 目录

- [站点支持](#站点支持)
  - [目录](#目录)
  - [表格说明](#表格说明)
  - [根据关键词搜索](#根据关键词搜索)
  - [一般小说](#一般小说)
    - [使用示例](#使用示例)
    - [Book ID 说明](#book-id-说明)
  - [同人小说](#同人小说)
    - [使用示例](#使用示例-1)
    - [Book ID 说明](#book-id-说明-1)
  - [轻小说](#轻小说)
    - [使用示例](#使用示例-2)
    - [Book ID 说明](#book-id-说明-2)
  - [其它小说](#其它小说)
    - [使用示例](#使用示例-3)
    - [Book ID 说明](#book-id-说明-3)
  - [配置文件设置](#配置文件设置)
  - [Cookie 与登录](#cookie-与登录)
  - [注意事项](#注意事项)

---

### 表格说明

* **站点名称**: 支持的小说网站, 点击可跳转官网
* **站点标识符**: 用于命令行 `--site` 参数或配置文件识别站点
* **支持分卷**: 是否能够识别并抓取小说的分卷结构
* **支持图片**: 是否支持抓取章节内插图并嵌入 EPUB 导出文件
* **支持登录**: 部分站点提供书架或 VIP 阅读功能, 需账号登录
* **支持搜索**：是否支持通过关键词搜索站点中的小说

> ⚠️ 表示该功能尚未在本库中实现

---

### 根据关键词搜索

```bash
# 根据关键词搜索
novel-cli search 关键词
```

---

### 一般小说

| 站点名称                                                     | 站点标识符 | 支持分卷 | 支持图片 | 支持登录 | 支持搜索 | 支持语言 |
| ----------------------------------------------------------- | --------- | ------- | ------- | ------- | ------- | ------- |
| [起点中文网](https://www.qidian.com)                         | qidian    | ✅     | ❌     | ✅     | ⚠️     | 简      |
| [和图书](https://www.hetushu.com/index.php)                  | hetushu   | ✅     | ❌     | ❌     | ✅     | 简 / 繁 |
| [笔趣阁](http://www.b520.cc)                                 | biquge    | ❌     | ❌     | ⚠️     | ✅     | 简      |
| [铅笔小说](https://www.23qb.net), [备用](https://www.23qb.com/) | qianbi | ✅     | ❌     | ⚠️     | ✅     | 简      |
| [得奇小说网](https://www.deqixs.com/)                         | deqixs   | ❌     | ❌     | ❌     | ✅     | 简      |
| [飘天文学网](https://www.piaotia.com/)                        | piaotia  | ❌     | ❌     | ⚠️     | ✅     | 简      |
| [小说屋](http://www.xiaoshuoge.info/)                        | xiaoshuowu | ❌     | ❌     | ⚠️     | ✅     | 简      |
| [精品小说网](https://www.jpxs123.com/)                        | jpxs123  | ❌     | ❌     | ❌     | ✅     | 简      |
| [天天看小说](https://www.ttkan.co/)                          | ttkan     | ❌     | ❌     | ❌     | ✅     | 简 / 繁 |
| [精彩小说](https://biquyuedu.com/)                           | biquyuedu | ❌     | ❌     | ⚠️     | ❌     | 简      |
| [书海阁小说网](https://www.shuhaige.net/)                     | shuhaige | ❌     | ❌     | ⚠️     | ✅     | 简      |
| [爱下电子书](https://ixdzs8.com/)                             | ixdzs8   | ❌     | ❌     | ⚠️     | ✅     | 简      |
| [小说路上](https://m.xs63b.com/)                              | xs63b    | ❌     | ❌     | ⚠️     | ✅     | 简      |
| [大熊猫文学网](https://www.dxmwx.org/)                        | dxmwx    | ❌     | ❌     | ❌     | ✅     | 简 / 繁 |
| [一笔阁](https://www.yibige.org/)                            | yibige    | ❌     | ❌     | ⚠️     | ⚠️     | 简 / 繁 |
| [小说虎](https://www.xshbook.com/)                           | xshbook   | ❌     | ❌     | ⚠️     | ✅     | 简      |
| [25中文网](https://www.i25zw.com/)                           | i25zw     | ❌     | ❌     | ❌     | ✅     | 简      |
| [全本小说网](https://quanben5.com/)                          | quanben5  | ❌     | ❌     | ❌     | ✅     | 简 / 繁 |
| [乐文小说网](https://www.lewenn.net/)                        | lewenn    | ❌     | ❌     | ⚠️     | ⚠️     | 简      |
| [名著阅读](https://b.guidaye.com/)                           | guidaye   | ❌     | ❌     | ❌     | ⚠️     | 简      |

#### 使用示例

```bash
# 下载起点中文网的小说
novel-cli download --site qidian 1234567890

# 下载笔趣阁的小说
novel-cli download --site biquge 1_2345

# 下载铅笔小说
novel-cli download --site qianbi 12345

# 下载天天看小说
novel-cli download --site ttkan bookname-authorname
```

#### Book ID 说明

Book ID 通常来源于小说详情页 URL 中的路径段, 各资源站点的对应关系如下:

* **起点中文网 (qidian)**
  * 示例 URL:
    * 书籍页面: `https://www.qidian.com/book/1010868264/` -> Book ID: `1010868264`
    * 章节页面: `https://www.qidian.com/chapter/1010868264/405976997/` -> Chapter ID: `405976997`
  * 登录要求:
    * 该站点需提供有效的 Cookie 才能访问订阅章节。
  * 其它:
    * 当保存时遇到重复内容, 请确保 `settings.toml` 中该站点 (`[sites.qidian]`) 的 `use_truncation` 为 `true`。

* **和图书 (hetushu)**
  * 示例 URL:
    * 书籍页面: `https://www.hetushu.com/book/5763/index.html` -> Book ID: `5763`
    * 章节页面: `https://www.hetushu.com/book/5763/4327466.html` -> Chapter ID: `4327466`

* **笔趣阁 (biquge)**
  * 示例 URL:
    * 书籍页面: `http://www.b520.cc/8_8187/` -> Book ID: `8_8187`
    * 章节页面: `http://www.b520.cc/8_8187/3899831.html` -> Chapter ID: `3899831`

* **铅笔小说 (qianbi)**
  * 示例 URL:
    * 书籍页面: `https://www.23qb.net/book/12282/` -> Book ID: `12282`
    * 章节页面: `https://www.23qb.net/book/12282/7908999.html` -> Chapter ID: `7908999`

* **得奇小说网 (deqixs)**
  * 示例 URL:
    * 书籍页面: `https://www.deqixs.com/xiaoshuo/2026/` -> Book ID: `2026`
    * 章节页面: `https://www.deqixs.com/xiaoshuo/2026/1969933.html` -> Chapter ID: `1969933`
  * 注意事项:
    * 该站点直接提供 txt 下载。
  * 缺点:
    * 每章节分页过多, 每页内容较少, 推荐适当降低请求间隔

* **飘天文学网 (piaotia)**
  * 示例 URL:
    * 书籍页面: `https://www.piaotia.com/bookinfo/13/12345.html` -> Book ID: `13-12345`
    * 章节页面: `https://www.piaotia.com/html/13/12345/114514.html` -> Chapter ID: `114514`

* **小说屋 (xiaoshuowu)**
  * 示例 URL:
    * 书籍页面: `http://www.xiaoshuoge.info/html/987/987654/` -> Book ID: `987-987654`
    * 章节页面: `http://www.xiaoshuoge.info/html/987/987654/123456789.html` -> Chapter ID: `123456789`

* **精品小说网 (jpxs123)**
  * 示例 URL:
    * 书籍页面: `https://www.jpxs123.com/xh/zhetian.html` -> Book ID: `xh-zhetian`
    * 章节页面: `https://www.jpxs123.com/xh/zhetian/1.html` -> Chapter ID: `1`
  * 注意事项:
    * 该站点直接提供 txt 下载。

* **书海阁小说网 (shuhaige)**
  * 示例 URL:
    * 书籍页面: `https://www.shuhaige.net/199178/` -> Book ID: `199178`
    * 章节页面: `https://www.shuhaige.net/199178/86580492.html` -> Chapter ID: `86580492`

* **爱下电子书 (ixdzs8)**
  * 示例 URL:
    * 书籍页面: `https://ixdzs8.com/read/38804/` -> Book ID: `38804`
    * 章节页面: `https://ixdzs8.com/read/38804/p1.html` -> Chapter ID: `p1`

* **小说路上 (xs63b)**
  * 示例 URL:
    * 书籍页面: `https://m.xs63b.com/xuanhuan/aoshijiuzhongtian/` -> Book ID: `xuanhuan-aoshijiuzhongtian`
    * 章节页面: `https://m.xs63b.com/xuanhuan/aoshijiuzhongtian/8748062.html` -> Chapter ID: `8748062`
  * 注意事项:
    * 桌面端页面部分章节缺页, 移动端正常

* **大熊猫文学网 (dxmwx)**
  * 示例 URL:
    * 书籍页面: `https://www.dxmwx.org/book/55598.html` -> Book ID: `55598`
    * 章节页面: `https://www.dxmwx.org/read/55598_47170737.html` -> Chapter ID: `47170737`

* **一笔阁 (yibige)**
  * 示例 URL:
    * 书籍页面: `https://www.yibige.org/6238/` -> Book ID: `6238`
    * 章节页面: `https://www.yibige.org/6238/1.html` -> Chapter ID: `1`

* **小说虎 (xshbook)**
  * 示例 URL:
    * 书籍页面: `https://www.xshbook.com/95139/95139418/` -> Book ID: `95139-95139418`
    * 章节页面: `https://www.xshbook.com/95139/95139418/407988281.html` -> Chapter ID: `407988281`

* **25中文网 (i25zw)**
  * 示例 URL:
    * 书籍页面: `https://www.i25zw.com/book/64371.html` -> Book ID: `64371`
    * 章节页面: `https://www.i25zw.com/64371/153149757.html` -> Chapter ID: `153149757`

* **全本小说网 (quanben5)**
  * 示例 URL:
    * 书籍页面: `https://quanben5.com/n/doushentianxia/` -> Book ID: `doushentianxia`
    * 章节页面: `https://quanben5.com/n/doushentianxia/13685.html` -> Chapter ID: `13685`

* **天天看小說 (ttkan)**
  * 示例 URL:
    * 书籍页面: `https://www.ttkan.co/novel/chapters/bookname-authorname` -> Book ID: `bookname-authorname`
    * 章节页面: `https://www.wa01.com/novel/pagea/bookname-authorname_1.html` -> Chapter ID: `1`

* **精彩小说 (biquyuedu)**
  * 示例 URL:
    * 书籍页面: `https://biquyuedu.com/novel/GDr1I1.html` -> Book ID: `GDr1I1`
    * 章节页面: `https://biquyuedu.com/novel/GDr1I1/1.html` -> Chapter ID: `1`

* **乐文小说网 (lewenn)**
  * 示例 URL:
    * 书籍页面: `https://www.lewenn.net/lw1/` -> Book ID: `lw1`
    * 章节页面: `https://www.lewenn.net/lw1/30038546.html` -> Chapter ID: `30038546`
  * 其它:
    * 该站点的搜索结果是 `3A小说网` 的...

* **名著阅读 (guidaye)**
  * 示例 URL:
    * 书籍页面: `https://b.guidaye.com/kongbu/654/` -> Book ID: `kongbu-654`
    * 章节页面: `https://b.guidaye.com/kongbu/654/170737.html` -> Chapter ID: `170737`

---

### 同人小说

| 站点名称                                                     | 站点标识符 | 支持分卷 | 支持图片 | 支持登录 | 支持搜索 | 支持语言 |
| ----------------------------------------------------------- | --------- | ------- | ------- | ------- | ------- | ------- |
| [同人圈](https://www.tongrenquan.org/)                      | tongrenquan | ❌     | ❌     | ❌     | ✅     | 简      |
| [全本同人小说](https://www.qbtr.cc/)                         | qbtr        | ❌     | ❌     | ❌     | ✅     | 简      |

#### 使用示例

```bash
# 下载 全本同人小说 小说
novel-cli download --site qbtr 9876
```

#### Book ID 说明

* **同人圈 (tongrenquan)**
  * 示例 URL:
    * 书籍页面: `https://www.tongrenquan.org/tongren/7548.html` -> Book ID: `7548`
    * 章节页面: `https://www.tongrenquan.org/tongren/7548/1.html` -> Chapter ID: `1`

* **全本同人小说 (qbtr)**
  * 示例 URL:
    * 书籍页面: `https://www.qbtr.cc/tongren/8978.html` -> Book ID: `tongren-8978`
    * 章节页面: `https://www.qbtr.cc/tongren/8978/1.html` -> Chapter ID: `1`
  * 注意事项:
    * 该站点直接提供 txt 下载。

---

### 轻小说

| 站点名称                                                     | 站点标识符 | 支持分卷 | 支持图片 | 支持登录 | 支持搜索 | 支持语言 |
| ----------------------------------------------------------- | --------- | ------- | ------- | ------- | ------- | ------- |
| [SF轻小说](https://m.sfacg.com)                              | sfacg      | ✅     | ✅     | ✅     | ⚠️     | 简      |
| [哔哩轻小说](https://www.linovelib.com/)                     | linovelib  | ✅     | ✅     | ⚠️     | ⚠️     | 简      |
| [ESJ Zone](https://www.esjzone.cc)                           | esjzone   | ✅     | ✅     | ✅     | ✅     | 简      |
| [神凑轻小说](https://www.shencou.com/)                        | shencou   | ✅     | ✅     | ⚠️     | ⚠️     | 简      |
| [无限轻小说](https://www.8novel.com/)                         | 8novel    | ✅     | ✅     | ⚠️     | ✅     | 繁      |

#### 使用示例

```bash
# 下载SF轻小说
novel-cli download --site sfacg 456123

# 下载 哔哩轻小说
novel-cli download --site linovelib 1234

# 下载 ESJ Zone 小说
novel-cli download --site esjzone 1234567890
```

#### Book ID 说明

* **SF 轻小说 (sfacg)**
  * 示例 URL:
    * 书籍页面: `https://m.sfacg.com/b/456123/` -> Book ID: `456123`
    * 章节页面: `https://m.sfacg.com/c/5417665/` -> Chapter ID: `5417665`
  * 登录要求:
    * 该站点需提供有效的 Cookie 才能访问订阅章节。

* **哔哩轻小说 (linovelib)**
  * 示例 URL:
    * 书籍页面: `https://www.linovelib.com/novel/1234.html` -> Book ID: `1234`
    * 章节页面: `https://www.linovelib.com/novel/1234/47800.html` -> Chapter ID: `47800`
  * 注意事项:
    * 该站点对于频繁请求有访问限制, 若请求间隔过短, 可能触发风控机制, 导致账号或设备被封禁或限制访问。

* **无限轻小说 (8novel)**
  * 示例 URL:
    * 书籍页面: `https://www.8novel.com/novelbooks/3365/` -> Book ID: `3365`
    * 章节页面: `https://article.8novel.com/read/3365/?106235` -> Chapter ID: `106235`

* **ESJ Zone (esjzone)**
  * 示例 URL:
    * 书籍页面: `https://www.esjzone.cc/detail/1660702902.html` -> Book ID: `1660702902`
    * 章节页面: `https://www.esjzone.cc/forum/1660702902/294593.html` -> Chapter ID: `294593`
  * 注意事项:
    * 若未完成登录验证, 部分小说页面会自动重定向至「論壇」页面, 导致内容加载失败。

* **神凑轻小说 (shencou)**
  * 示例 URL:
    * 书籍页面: `https://www.shencou.com/read/3/3540/index.html` -> Book ID: `3-3540`
    * 章节页面: `https://www.shencou.com/read/3/3540/156328.html` -> Chapter ID: `156328`
  * 目录访问:
    * 先打开详细页面 (如 `https://www.shencou.com/books/read_3540.html`), 再点击 "小说目录" 查看
  * 该站点存在以下问题:
    * 图片资源可能无法正常加载或失效
    * 目录页中仍保留了一些已删除章节的重复条目, 却未同步删除

---

### 其它小说

<details>
<summary>点击展开</summary>

| 站点名称                                                     | 站点标识符 | 支持分卷 | 支持图片 | 支持登录 | 支持搜索 | 支持语言 |
| ----------------------------------------------------------- | --------- | ------- | ------- | ------- | ------- | ------- |
| [百合会](https://www.yamibo.com/site/novel)                  | yamibo     | ✅     | ❌     | ✅     | ⚠️     | 简      |
| [3A电子书](http://www.aaatxt.com/)                           | aaatxt     | ❌     | ❌     | ⚠️     | ✅     | 简      |
| [西瓜书屋](https://www.xiguashuwu.com/)                      | xiguashuwu | ❌     | ❌     | ⚠️     | ✅     | 简      |

#### 使用示例

```bash
# 下载 百合会 小说
novel-cli download --site yamibo 123456
```

#### Book ID 说明

* **百合会 (yamibo)**
  * 示例 URL:
    * 书籍页面: `https://www.yamibo.com/novel/262117` -> Book ID: `262117`
    * 章节页面: `https://www.yamibo.com/novel/view-chapter?id=38772952` -> Chapter ID: `38772952`

* **3A电子书 (aaatxt)**
  * 示例 URL:
    * 书籍页面: `http://www.aaatxt.com/shu/24514.html` -> Book ID: `24514`
    * 章节页面: `http://www.aaatxt.com/yuedu/24514_1.html` -> Chapter ID: `24514_1`
  * 注意事项:
    * 该站点直接提供 txt 下载。

* **西瓜书屋 (xiguashuwu)**
  * 示例 URL:
    * 书籍页面: `https://www.xiguashuwu.com/book/1234/iszip/1/` -> Book ID: `1234`
    * 章节页面: `https://www.xiguashuwu.com/book/1234/482.html` -> Chapter ID: `482`

</details>

---

### 配置文件设置

可在 `settings.toml` 中添加对应站点的书籍 ID 和登录要求:

```toml
[sites.<site_name>]
book_ids = [
  "0000000000",
  "0000000000"
]
login_required = false  # 或 true
# 如果需要登录:
# username = "yourusername"
# password = "yourpassword"
```

配置示例 (下载 linovelib 的书籍):

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

> 使用命令行参数指定站点时, 参数中的 Book ID 会覆盖配置文件中的相应条目

---

### Cookie 与登录

若需提供 Cookie, 可在浏览器登录后, 通过开发者工具 (F12) 复制完整的 Cookie 字符串 (详见 [复制 Cookies](./copy-cookies.md))

当前 Session 登录方式的 Cookie 尚不支持自动续期, 每次运行前需手动更新。未来版本将考虑优化此流程。

也可以使用库内脚本通过浏览器进行登录:

```bash
# 通用登录脚本
python ./scripts/login_scripts/login.py qidian

# 专用于 ESJ Zone 的登录
python ./scripts/login_scripts/esjzone_login.py -u username -p password
```

脚本依赖 Playwright, 需先安装并初始化:

```bash
pip install playwright
playwright install
```

对于 ESJ Zone 和 百合会, 如需通过登录模式获取内容, 可在 `settings.toml` 中取消注释并填写对应账户信息, 或在运行时根据提示输入。示例如下:

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

- 若站点结构更新或章节数据抓取异常, 欢迎提 Issue 或提交 PR
- 登录支持受限于站点接口策略, 部分功能需人工 Cookie 配置或账号绑定
- 请合理设置请求频率, 避免触发风控或 IP 限制
