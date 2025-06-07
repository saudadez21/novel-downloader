## 配置

### 1. 初始化默认配置

```bash
# 创建一个新的工作目录
mkdir novel-folder

# 进入目录
cd novel-folder

# 在当前目录下生成 settings.toml (已存在则跳过)
novel-cli config init

# 如果想强制覆盖
novel-cli config init --force
````

### 2. 编辑生成的 `settings.toml`

```toml
[sites.qidian]
# 小说 ID 列表
book_ids = [
  "1234567890",
  "0987654321"
]
mode = "browser"                   # browser / session
login_required = true              # 是否需要登录才能访问
```

具体定义可参考 [settings.toml 配置说明](./3-settings-schema.md)

### 3. (可选) 注册配置到 CLI

```bash
# 将当前目录下的 settings.toml 设为默认配置
novel-cli config set-config ./settings.toml
```

### 配置文件查找顺序

CLI 启动时会按以下优先级依次查找并加载配置 (越靠前优先级越高):

1. 通过命令行参数 `--config` 明确指定的配置文件
2. 当前工作目录下的 `./settings.toml` 文件
3. 已注册 (全局保存) 的配置文件

> 注: 使用 `novel-cli config init` 会在当前目录生成 `settings.toml` 和 `rules.toml`, 作为默认配置的模板文件, 方便后续编辑与使用。

### 站点信息查找顺序

在解析有效配置后, CLI 将按以下优先级查找站点相关信息 (越靠前优先级越高):

1. `[sites.<sitename>]`
   - 其中 `<sitename>` 对应命令行参数中 `--site sitename` 指定的站点名称
2. `[sites.common]`
   - 通用站点配置, 适用于所有未显式定义的站点项, 作为默认回退方案
