## 安装

**Python 环境**
为避免包冲突, 建议创建独立环境:
推荐使用 Conda 或 `venv` 创建独立环境, 避免包冲突:
```bash
conda create -n novel-downloader python=3.11 -y
conda activate novel-downloader
```
或
```bash
python -m venv .venv
source .venv/bin/activate
```

项目提供了完整的 Python 包结构 (含 `pyproject.toml`),
可以通过 `pip install .` 或 `pip install git+https://github.com/BowenZ217/novel-downloader.git` 安装为库, 并使用 `novel-cli` CLI 入口。

```bash
# 克隆项目
git clone https://github.com/BowenZ217/novel-downloader.git
cd novel-downloader

# 安装为库并生成 CLI
pip install .
```

安装完成后, 会在系统 `PATH` 中生成 `novel-cli` 可执行命令。
