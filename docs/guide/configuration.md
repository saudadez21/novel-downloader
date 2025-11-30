## 配置

`novel-downloader` 的行为由 `settings.toml` 控制。

本章节介绍如何创建、修改和使用配置文件。

### 1. 初始化配置文件

在任意工作目录下, 通过命令生成默认配置文件:

```bash
novel-cli config init
```

若已存在同名文件并需覆盖:

```bash
novel-cli config init --force
```

生成内容包括:

* `settings.toml`: 核心配置文件

---

### 2. 编辑 `settings.toml`

基础结构如下 (站点名按需替换 `<site_name>`):

```toml
[sites.<site_name>]
book_ids = [
  "123456",
  "234567"
]
login_required = false
```

最少配置只需为目标站点填写 `book_ids`:

```toml
[sites.linovelib]
book_ids = ["1234"]
```

随后即可通过 CLI 启动下载:

```bash
novel-cli download --site linovelib
```

> **说明**:
>
> 若 CLI 同时传入了 Book ID, 例如 `novel-cli download --site linovelib 5555`,
> 则 **命令行参数会覆盖配置文件中的 `book_ids`**。

---

### 3. 登录与 Cookie 配置

部分站点需要登录才能访问全部内容, 可按以下方式配置。

#### Cookie 缓存机制

程序会将登录后获取的 Cookie 自动缓存在运行目录下:

```bash
./novel_cache/<site_name>/*.cookies
```

如果遇到登录异常、Cookie 失效, 或不希望继续使用缓存内容, 可以直接删除对应的 `.cookies` 文件, 程序会在下次访问时尝试重新登录或提示输入 Cookie。

#### 3.1 使用账号密码登录

适用于: ESJ Zone、百合会等支持表单登录的站点。

```toml
[sites.<site_name>]
login_required = true
username = "your_username"
password = "your_password"
```

也可不写入配置, CLI 会在需要时提示输入。

---

#### 3.2 使用 Cookie 登录

适用于需要复杂登录逻辑 (如验证码、扫码登录) 的站点。

步骤:

1. 先在浏览器登录目标站点
2. 打开开发者工具 (`F12` / `CTRL + SHITF + I`)
3. 从网络请求中复制完整 Cookie 字符串
4. 写入配置:

```toml
[sites.<site_name>]
login_required = true
cookie = "完整的 Cookie 字符串"
```

> 当前 Cookie 方式不支持自动续期; 过期后请重新复制。

更多说明见: [复制 Cookies](./copy-cookies.md)

### 4. 配置文件查找顺序

CLI 每次运行时会按以下优先级查找配置 (高 -> 低):

(1) **命令行参数指定的文件**

```bash
novel-cli download --config path/to/settings.toml
```

(2) **当前目录下的 `./settings.toml`**

若存在多个匹配项, 上级优先级配置会覆盖下级。
