## 站点支持

### 目录

- [站点支持](#站点支持)
  - [目录](#目录)
  - [表格说明](#表格说明)
  - [根据关键词搜索](#根据关键词搜索)
  - [一般小说](#一般小说)
    - [使用示例](#使用示例)
    - [Book ID 说明](#book-id-说明)
  - [轻小说](#轻小说)
    - [使用示例](#使用示例-1)
  - [Book ID 说明](#book-id-说明-1)
  - [其它小说](#其它小说)
    - [使用示例](#使用示例-2)
    - [Book ID 说明](#book-id-说明-2)
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

| 站点名称                                                     | 站点标识符 | 支持分卷 | 支持图片 | 支持登录 | 支持搜索 |
| ------------------------------------------------------------ | ---------- | -------- | -------- | -------- | ---- |
| [起点中文网](https://www.qidian.com)                         | qidian     | ✅        | ❌        | ✅        | ⚠️   |
| [笔趣阁](http://www.b520.cc)                                 | biquge     | ❌        | ❌        | ⚠️        | ✅    |
| [铅笔小说](https://www.23qb.net), [备用](https://www.23qb.com/) | qianbi   | ✅        | ❌        | ⚠️        | ✅    |
| [飘天文学网](https://www.piaotia.com/)                        | piaotia   | ❌        | ❌        | ⚠️        | ✅    |
| [小说屋](http://www.xiaoshuoge.info/)                        | xiaoshuowu | ❌        | ❌        | ⚠️        | ✅    |
| [天天看小说](https://www.ttkan.co/)                           | ttkan     | ❌        | ❌        | ❌        | ✅    |
| [精彩小说](https://biquyuedu.com/)                           | biquyuedu  | ❌        | ❌        | ⚠️        | ❌    |
| [25中文网](https://www.i25zw.com/)                           | i25zw     | ❌        | ❌        | ❌        | ✅    |

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

  示例 URL:

    - 书籍页面: `https://www.qidian.com/book/1010868264/` -> Book ID: `1010868264`
    - 章节页面: `https://www.qidian.com/chapter/1010868264/405976997/` -> Chapter ID: `405976997`

  该站点需提供有效的 Cookie 才能访问订阅章节。

  当保存时遇到重复内容, 请确保 `settings.toml` 中该站点 (`[sites.qidian]`) 的 `use_truncation` 为 `true`。

* **笔趣阁 (biquge)**

  示例 URL:

    - 书籍页面: `http://www.b520.cc/8_8187/` -> Book ID: `8_8187`
    - 章节页面: `http://www.b520.cc/8_8187/3899831.html` -> Chapter ID: `3899831`

* **铅笔小说 (qianbi)**

  示例 URL:

    - 书籍页面: `https://www.23qb.net/book/12282/` -> Book ID: `12282`
    - 章节页面: `https://www.23qb.net/book/12282/7908999.html` -> Chapter ID: `7908999`

* **飘天文学网 (piaotia)**

  示例 URL:

    - 书籍页面: `https://www.piaotia.com/bookinfo/13/12345.html` -> Book ID: `13-12345`
    - 章节页面: `https://www.piaotia.com/html/13/12345/114514.html` -> Chapter ID: `114514`

* **小说屋 (xiaoshuowu)**

  示例 URL:

    - 书籍页面: `http://www.xiaoshuoge.info/html/987/987654/` -> Book ID: `987-987654`
    - 章节页面: `http://www.xiaoshuoge.info/html/987/987654/123456789.html` -> Chapter ID: `123456789`

* **25中文网 (i25zw)**

  示例 URL:

    - 书籍页面: `https://www.i25zw.com/book/64371.html` -> Book ID: `64371`
    - 章节页面: `https://www.i25zw.com/64371/153149757.html` -> Chapter ID: `153149757`

* **天天看小說 (ttkan)**

  示例 URL:

    - 书籍页面: `https://www.ttkan.co/novel/chapters/bookname-authorname` -> Book ID: `bookname-authorname`
    - 章节页面: `https://www.wa01.com/novel/pagea/bookname-authorname_1.html` -> Chapter ID: `1`

* **精彩小说 (biquyuedu)**

  示例 URL:

    - 书籍页面: `https://biquyuedu.com/novel/GDr1I1.html` -> Book ID: `GDr1I1`
    - 章节页面: `https://biquyuedu.com/novel/GDr1I1/1.html` -> Chapter ID: `1`

---

### 轻小说

| 站点名称                                                     | 站点标识符 | 支持分卷 | 支持图片 | 支持登录 | 支持搜索 |
| ------------------------------------------------------------ | ---------- | -------- | -------- | -------- | ---- |
| [SF轻小说](https://m.sfacg.com)                              | sfacg      | ✅        | ✅        | ✅        | ⚠️   |
| [哔哩轻小说](https://www.linovelib.com/)                     | linovelib   | ✅        | ✅        | ⚠️        | ⚠️   |
| [ESJ Zone](https://www.esjzone.cc)                           | esjzone    | ✅        | ✅        | ✅        | ✅    |

#### 使用示例

```bash
# 下载SF轻小说
novel-cli download --site sfacg 456123

# 下载 哔哩轻小说
novel-cli download --site linovelib 1234

# 下载 ESJ Zone 小说
novel-cli download --site esjzone 1234567890
```

---

### Book ID 说明

* **SF 轻小说 (sfacg)**

  示例 URL:

    - 书籍页面: `https://m.sfacg.com/b/456123/` -> Book ID: `456123`
    - 章节页面: `https://m.sfacg.com/c/5417665/` -> Chapter ID: `5417665`

  该站点需提供有效的 Cookie 才能访问订阅章节。

* **哔哩轻小说 (linovelib)**

  示例 URL:

    - 书籍页面: `https://www.linovelib.com/novel/1234.html` -> Book ID: `1234`
    - 章节页面: `https://www.linovelib.com/novel/1234/47800.html` -> Chapter ID: `47800`

  该站点对于频繁请求有访问限制, 若请求间隔过短, 可能触发风控机制, 导致账号或设备被封禁或限制访问。

* **ESJ Zone (esjzone)**

  示例 URL:

    - 书籍页面: `https://www.esjzone.cc/detail/1660702902.html` -> Book ID: `1660702902`
    - 章节页面: `https://www.esjzone.cc/forum/1660702902/294593.html` -> Chapter ID: `294593`

  **注意**: 若未完成登录验证, 部分小说页面会自动重定向至「論壇」页面, 导致内容加载失败。

---

### 其它小说

<details>
<summary>点击展开</summary>

| 站点名称                                                     | 站点标识符 | 支持分卷 | 支持图片 | 支持登录 | 支持搜索 |
| ------------------------------------------------------------ | ---------- | -------- | -------- | -------- | ---- |
| [百合会](https://www.yamibo.com/site/novel)                  | yamibo     | ✅        | ❌        | ✅        | ⚠️   |

#### 使用示例

```bash
# 下载 百合会 小说
novel-cli download --site yamibo 123456
```

#### Book ID 说明

* **百合会 (yamibo)**

  示例 URL:

    - 书籍页面: `https://www.yamibo.com/novel/262117` -> Book ID: `262117`
    - 章节页面: `https://www.yamibo.com/novel/view-chapter?id=38772952` -> Chapter ID: `38772952`

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
