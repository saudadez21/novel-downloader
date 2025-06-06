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

### Book ID 说明

根据不同站点, Book ID 通常来源于小说详情页 URL 中的路径段:

* 起点中文网 (qidian)

  `https://www.qidian.com/book/1010868264/` -> `1010868264`

  登录需要 Cookies

* 笔趣阁 (biquge)

  `http://www.b520.cc/8_8187/` -> `8_8187`

* 铅笔小说 (qianbi)

  `https://www.23qb.net/book/12282/` -> `12282`

* SF轻小说 (sfacg)

  `https://m.sfacg.com/b/456123/` -> `456123`

  登录需要 Cookies

* ESJ Zone (esjzone)

  `https://www.esjzone.cc/detail/1660702902.html` -> `1660702902`

  **注意**: 若用户未登录账号, 部分小说页面可能无法访问。此时, 浏览器将自动重定向至「論壇」页面, 导致内容加载失败。

* 百合会 (yamibo)

  `https://www.yamibo.com/novel/262117` -> `262117`

* 哔哩轻小说 (linovelib)

  `https://www.linovelib.com/novel/1234.html` -> `1234`

  **注意**: 若请求间隔过短, 可能触发平台限制机制, 导致账号/设备在一段时间内被封禁或限制访问。

如果需要 Cookie, 可以在浏览器登录后, 通过浏览器开发者工具 (F12) 复制完整的 Cookie 字符串, 请参考 [复制 Cookies](./copy-cookies.md)。

p.s. 目前 session 登录方式的 cookie 还不支持自动续期, 可能每次运行前都需要手动重新设置一次 cookie, 后续会考虑优化这一流程

### 注意事项

- 若站点结构更新或章节数据抓取异常, 欢迎提 Issue 或提交 PR
- 登录支持受限于站点接口策略, 部分功能需人工 Cookie 配置或账号绑定
