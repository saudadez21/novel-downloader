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

## 额外依赖

> 起点一个月内更新的章节可能有字体加密
>
> 如果开启尝试解密字体功能 (`decode_font` 参数), 需要安装额外库 (注意: 解密字体准确率大约 $99.x%$, 并且 cpu 状态下一章约需要一分钟):
>
> ```bash
> pip install .[font-recovery]
> ```
>
> 如果启用 `use_ocr` 参数, 则需安装 [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) 及相关依赖 (请根据 PaddleOCR [文档](https://paddlepaddle.github.io/PaddleOCR/latest/quick_start.html) 选择合适版本和 CUDA 支持) :
>
> ```bash
> python -m pip install paddlepaddle==3.0.0rc1 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/
> pip install paddleocr
> ```
>
> 当前使用版本示例:
>
> ```bash
> paddleocr==2.10.0
> paddlepaddle==3.0.0rc1
> ```
>
> 如果不启用 OCR (即不使用 `use_ocr` 参数) , 则无需安装 PaddleOCR 及 paddle 相关。

### OCR 速度基准 (随机中文图片, 512 张)

> **测试设备**: NVIDIA GeForce RTX 3070 (8GB 显存)
> **提示**: 实际使用时, 请根据你自己的 GPU/CPU 内存情况调整 `batch_size`, 过大可能会因内存不足导致程序崩溃

| Batch Size | Use GPU | Total Time (s) | Avg Time per Image (ms) |
| ---------- | ------- | -------------- | ----------------------- |
| 1          | Yes     | 5.068          | 9.90                    |
| 1          | No      | 504.857        | 986.05                  |
| 8          | Yes     | 1.278          | 2.50                    |
| 8          | No      | 402.604        | 786.34                  |
| 16         | Yes     | 0.499          | 0.97                    |
| 16         | No      | 115.061        | 224.73                  |
| 32         | Yes     | 0.420          | 0.82                    |
| 32         | No      | 82.648         | 161.42                  |
| 64         | Yes     | 0.597          | 1.17                    |
| 64         | No      | 63.439         | 123.90                  |
| 128        | Yes     | 0.295          | 0.58                    |
| 128        | No      | 50.704         | 99.03                   |
| 256        | Yes     | 0.293          | 0.57                    |
| 256        | No      | 45.108         | 88.10                   |
