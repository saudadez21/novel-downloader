## 1. 克隆项目

```bash
git clone https://github.com/BowenZ217/novel-downloader.git
cd novel-downloader
````

---

## 2. 安装开发环境依赖

使用 `pip` 安装项目及开发、可选扩展依赖:

```bash
pip install -e .[dev,font-recovery]
```

---

## 3. 安装 pre-commit 钩子

本项目使用 [pre-commit](https://pre-commit.com/) 自动检查代码风格、提交信息等。
首次开发请执行:

```bash
pre-commit install
```

此后每次提交前将自动触发检查。

---

## 4. 提交规范

采用 [Conventional Commits](https://www.conventionalcommits.org/) 规范进行提交。格式如下:

```text
<type>(<scope>): <description>
```

### 常用类型:

* `feat`: 新功能
* `fix`: 修复 bug
* `docs`: 文档变更
* `style`: 格式调整 (不影响逻辑)
* `refactor`: 代码重构 (非功能/非修复)
* `test`: 添加或修改测试
* `chore`: 杂项任务 (依赖更新、构建脚本等)

### 示例:

```bash
git commit -m "feat(cli): add clean command for cache/logs"
git commit -m "fix(qidian): correct VIP chapter decryption logic"
```

---

## 5. 版本管理和日志自动化

```bash
cz bump
```

它会自动更新版本号、生成 `CHANGELOG.md` 并创建 Git tag。
