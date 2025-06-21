## 站点支持

表格说明:

- **站点名称**: 支持的小说网站, 点击可跳转官网
- **站点标识符**: 用于命令行 `--site` 参数或配置文件识别站点
- **支持分卷**: 是否能够识别并抓取小说的分卷结构
- **支持图片**: 是否支持抓取章节内插图并嵌入 EPUB 导出文件
- **支持登录**: 部分站点提供书架或 VIP 阅读功能, 需账号登录

| 站点名称                                                     | 站点标识符 | 支持分卷 | 支持图片 | 支持登录 |
| ------------------------------------------------------------ | ---------- | -------- | -------- | -------- |
| [起点中文网](https://www.qidian.com)                         | qidian     | ✅        | ❌        | ✅        |
| [笔趣阁](http://www.b520.cc)                                 | biquge     | ❌        | ❌        | ❌        |
| [铅笔小说](https://www.23qb.net), [备用](https://www.23qb.com/) | qianbi   | ✅        | ❌        | ❌        |
| [SF轻小说](https://m.sfacg.com)                              | sfacg      | ✅        | ✅        | ✅        |
| [ESJ Zone](https://www.esjzone.cc)                           | esjzone    | ✅        | ✅        | ✅        |
| [百合会](https://www.yamibo.com/site/novel)                  | yamibo     | ✅        | ❌        | ✅        |
| [哔哩轻小说](https://www.linovelib.com/)                     | linovelib   | ✅        | ✅        | ❌        |

使用示例:

```bash
# 下载起点中文网的小说
novel-cli download --site qidian 1234567890

# 下载笔趣阁的小说
novel-cli download --site biquge 1_2345

# 下载铅笔小说
novel-cli download --site qianbi 12345

# 下载SF轻小说
novel-cli download --site sfacg 456123

# 下载 ESJ Zone 小说
novel-cli download --site esjzone 1234567890

# 下载 百合会 小说
novel-cli download --site yamibo 123456

# 下载 哔哩轻小说
novel-cli download --site yamibo 1234
```

---

### Book ID 说明

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

  该站点无需额外认证即可获取小说内容。

* **铅笔小说 (qianbi)**

  示例 URL:

    - 书籍页面: `https://www.23qb.net/book/12282/` -> Book ID: `12282`
    - 章节页面: `https://www.23qb.net/book/12282/7908999.html` -> Chapter ID: `7908999`

* **SF 轻小说 (sfacg)**

  示例 URL:

    - 书籍页面: `https://m.sfacg.com/b/456123/` -> Book ID: `456123`
    - 章节页面: `https://m.sfacg.com/c/5417665/` -> Chapter ID: `5417665`

  该站点需提供有效的 Cookie 才能访问订阅章节。

* **ESJ Zone (esjzone)**

  示例 URL:

    - 书籍页面: `https://www.esjzone.cc/detail/1660702902.html` -> Book ID: `1660702902`
    - 章节页面: `https://www.esjzone.cc/forum/1660702902/294593.html` -> Chapter ID: `294593`

  **注意**: 若未完成登录验证, 部分小说页面会自动重定向至「論壇」页面, 导致内容加载失败。

* **百合会 (yamibo)**

  示例 URL:

    - 书籍页面: `https://www.yamibo.com/novel/262117` -> Book ID: `262117`
    - 章节页面: `https://www.yamibo.com/novel/view-chapter?id=38772952` -> Chapter ID: `38772952`

* **哔哩轻小说 (linovelib)**

  示例 URL:

    - 书籍页面: `https://www.linovelib.com/novel/1234.html` -> Book ID: `1234`
    - 章节页面: `https://www.linovelib.com/novel/1234/47800.html` -> Chapter ID: `47800`

  该站点对于频繁请求有访问限制, 若请求间隔过短, 可能触发风控机制, 导致账号或设备被封禁或限制访问。

---

若需提供 Cookie, 可在浏览器登录后, 通过开发者工具 (F12) 复制完整的 Cookie 字符串 (详见 [复制 Cookies](./copy-cookies.md))

当前 Session 登录方式的 Cookie 尚不支持自动续期, 每次运行前需手动更新。未来版本将考虑优化此流程。

对于 ESJ Zone 和 百合会, 如需通过登录模式获取内容, 可在 `settings.toml` 中取消注释并填写对应账户信息, 或在运行时根据提示输入。示例如下:

```toml
[sites.<site_name>]
book_ids = [
  "0000000000",
  "0000000000"
]
mode = "session"
login_required = true
username = "yourusername"     # 登录账户
password = "yourpassword"     # 登录密码
```

---

### 注意事项

- 若站点结构更新或章节数据抓取异常, 欢迎提 Issue 或提交 PR
- 登录支持受限于站点接口策略, 部分功能需人工 Cookie 配置或账号绑定
