# Contributing to novel-downloader

感谢你对 **novel-downloader** 感兴趣并愿意贡献！

---

## 目录

- [Contributing to novel-downloader](#contributing-to-novel-downloader)
  - [目录](#目录)
  - [可贡献的方向](#可贡献的方向)
  - [开始之前](#开始之前)
  - [开发环境设置](#开发环境设置)
    - [1. 克隆项目](#1-克隆项目)
    - [2. 安装开发依赖](#2-安装开发依赖)
    - [3. 安装 pre-commit 钩子](#3-安装-pre-commit-钩子)
  - [代码风格与静态检查](#代码风格与静态检查)
  - [提交规范](#提交规范)
    - [常用类型](#常用类型)
    - [示例](#示例)
    - [保持单一职责](#保持单一职责)
    - [提交标题格式](#提交标题格式)
    - [提交信息描述](#提交信息描述)
  - [Pull Request 流程](#pull-request-流程)
    - [1. Fork 仓库并新建分支](#1-fork-仓库并新建分支)
    - [2. 保持分支最新](#2-保持分支最新)
    - [3. 本地检查与测试](#3-本地检查与测试)
    - [4. 提交并推送到你的 Fork 仓库](#4-提交并推送到你的-fork-仓库)
    - [5. 在 GitHub 创建 Pull Request (PR)](#5-在-github-创建-pull-request-pr)
    - [6. Review 与合并](#6-review-与合并)
  - [文档与社区贡献](#文档与社区贡献)
  - [报告 Bug / 提建议](#报告-bug--提建议)
  - [责任与许可](#责任与许可)

---

## 可贡献的方向

你可以从以下方面参与项目:

* 新功能 / 功能增强
* 修复 Bug / 兼容性问题
* 文档改进 / 示例补充
* 支持新站点解析插件
* 文本处理器 / 导出器 插件
* 自动化、CI、性能优化
* 社区推广、Issue 管理、问题答疑

如果不确定方向是否合适，欢迎先开 issue 讨论。

---

## 开始之前

在动手之前，请确保:

1. 仓库已 Fork 并 Clone
2. 使用最新主分支 (或对应开发分支)
3. 阅读本项目的 `README.md`
4. 安装好开发依赖
5. 若贡献涉及外部站点解析或接口变动，请先在 issue 中简要讨论可行性

---

## 开发环境设置

### 1. 克隆项目

```bash
git clone https://github.com/saudadez21/novel-downloader.git
cd novel-downloader
```

### 2. 安装开发依赖

使用 `pip install -e` 以 "可编辑模式" 安装项目与开发依赖:

```bash
pip install -e .[dev,all]
```

项目中可能有额外依赖，请查看 `pyproject.toml`。

### 3. 安装 pre-commit 钩子

项目使用 [pre-commit](https://pre-commit.com/) 管理代码风格、提交信息等自动化检查。

首次开发请执行:

```bash
pre-commit install
```

此后每次提交前将自动运行格式与静态检查。

如需手动执行所有钩子:

```bash
pre-commit run --all-files
```

---

## 代码风格与静态检查

项目采用以下工具进行统一规范:

| 工具       | 功能                         | 配置位置          |
| --------- | ---------------------------- | ---------------- |
| **ruff**  | Lint / import 排序 / 简化检查 | `pyproject.toml` |
| **mypy**  | 静态类型检查                  | `pyproject.toml` |

主要配置如下:

```toml
[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "B", "C4", "I", "UP", "SIM"]

[tool.mypy]
python_version = "3.12"
ignore_missing_imports = true
strict = true
```

提交前可执行以下命令以确保通过检查:

```bash
pre-commit run --all-files
```

> 建议: 本地检查通过后再提交，可避免 CI 失败。

---

## 提交规范

项目采用 [Conventional Commits](https://www.conventionalcommits.org/) 规范。

提交信息格式如下:

```
<type>(<scope>): <description>
```

### 常用类型

| 类型        | 含义                         |
| ---------- | ---------------------------- |
| `feat`     | 新功能                        |
| `fix`      | 修复 Bug                      |
| `docs`     | 文档修改                      |
| `style`    | 格式调整 (不影响逻辑)          |
| `refactor` | 代码重构 (非功能性)            |
| `test`     | 测试相关改动                   |
| `chore`    | 杂项任务 (依赖更新、构建脚本等) |

### 示例

```bash
git commit -m "feat(cli): add clean command for cache/logs"
git commit -m "fix(qidian): correct VIP chapter decryption logic"
```

> 提交信息将用于自动生成变更日志与版本发布记录。

### 保持单一职责

每次提交应只包含一个逻辑单元，避免在一次提交中混合多个功能或修改。

小而清晰的提交能帮助维护者快速理解、审查与回滚。

### 提交标题格式

提交标题应遵循以下格式:

```
<type>(<scope>): <description>
```

其中:

* `<type>` 表示更改类型 (如 feat、fix、docs 等)
* `<scope>` 表示影响的范围 (可选，如 cli、core、qidian)
* `<description>` 为简要说明，建议使用英文动词开头

示例:

```
feat(cli): add clean command for cache/logs
fix(qidian): correct VIP chapter decryption logic
docs(readme): update installation instructions
```

### 提交信息描述

提交正文 (可选) 应说明以下三点:

1. **做了什么 (What)**: 修改或新增内容
2. **为什么要做 (Why)**: 背景、动机或修复原因
3. **可能的副作用 (Impact)**: 潜在影响或注意事项

> 示例:
>
> 修复分页解析时丢失章节标题的问题。
>
> 原因: 部分站点目录页存在空白标签导致索引偏移。
>
> 影响: 需要重新生成目录缓存。

---

## Pull Request 流程

### 1. Fork 仓库并新建分支

推荐使用语义化命名:

```bash
git checkout -b feature/ciweimao-support
```

### 2. 保持分支最新

请基于最新的主分支 (或开发分支) 进行开发。

若分支过期，请使用 `git rebase` 或 `git merge` 同步更新。

### 3. 本地检查与测试

在提交前，请运行格式化与静态检查:

```bash
pre-commit run --all-files
```

> 建议: 确保本地检查通过后再提交，以减少 CI 重试。

### 4. 提交并推送到你的 Fork 仓库

请确保提交信息符合 [Conventional Commits](#提交规范)

本地验证无误后推送:

```bash
git push origin feature/ciweimao-support
```

### 5. 在 GitHub 创建 Pull Request (PR)

* 在标题中简要说明改动内容
* 在描述中阐述动机、实现思路与潜在影响
* 如关联 issue，请在描述中注明 (例如: `Closes #42`)

### 6. Review 与合并

* 维护者会进行代码审查 (Review)
* 仅在 CI 全部通过后才会合并
* 若 PR 较大，请提前沟通或拆分为多个小 PR

---

## 文档与社区贡献

除了代码，你也可以通过以下方式参与:

* 完善 `README.md` 或 `docs/` 文档
* 增加 CLI / Web 使用示例
* 修正拼写或语法错误
* 回答 issue 或补充 FAQ
* 优化测试覆盖率

---

## 报告 Bug / 提建议

若你发现 Bug 或有功能建议，请按以下格式开 issue:

* 标题简洁明了
* 描述复现步骤 / 输入输出 / 错误信息
* 提供运行环境 (Python 版本、系统、设置等)
* 若建议可行，欢迎附上思路或示例代码

---

## 责任与许可

* 通过 PR 或 issue 提交的内容视为你授权 **遵守本项目所用的开源协议**
* 你应保证你的贡献是原创或已具备合法授权
* 维护者有权拒绝、修改或合并任何提交

---

感谢你的贡献！
