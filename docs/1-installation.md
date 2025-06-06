## 安装

**Python 环境**
为避免包冲突, 建议创建独立环境

推荐使用 [Conda](https://www.anaconda.com/download/success) 或 `venv` 创建独立环境, 避免包冲突:

```bash
conda create -n novel-downloader python=3.12 -y
conda activate novel-downloader
```

或

```bash
python -m venv .venv
source .venv/bin/activate
```

### 安装 novel-downloader

1. 从 PyPI 安装:

    ```bash
    pip install novel-downloader
    ```

2. 最新开发版 (从 GitHub 安装)

    ```bash
    # 克隆项目
    git clone https://github.com/BowenZ217/novel-downloader.git
    cd novel-downloader

    # 安装为库并生成 CLI
    pip install .
    ```

安装完成后, 会在系统 `PATH` 中生成 `novel-cli` 可执行命令。

如需使用浏览器模式 (即 `mode: browser`), 请确保已安装 Playwright 依赖:

```bash
playwright install
```

## 可选功能及依赖

### 字体解密 (`decode_font` 参数)

起点一个月内更新的章节可能有字体加密

如果开启尝试解密字体功能 (`decode_font` 参数), 需要安装额外库 (注意: 解密字体准确率大约 98+%, 并且 cpu 状态下一章约需要一分钟, GPU 状态下一章约需要 1 秒):

```bash
pip install novel-downloader[font-recovery]
```

如果启用 `use_ocr` 参数, 则需安装 [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) 及相关依赖 (请根据 paddlepaddle [文档](https://www.paddlepaddle.org.cn/install/quick?docurl=/documentation/docs/zh/develop/install/pip/windows-pip.html) 选择合适版本和 CUDA 支持) :

- CPU 版:
    ```bash
    python -m pip install paddlepaddle==3.0.0 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/
    ```

- GPU 版 (请根据 CUDA 版本选用对应 paddlepaddle-gpu):
    ```bash
    python -m pip install paddlepaddle-gpu==3.0.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu118/
    ```

当调用 `novel_downloader.utils.fontocr.ocr_v1` 时需要安装:

```bash
pip install paddleocr
```

当前使用版本示例:

```bash
paddleocr==2.10.0
paddlepaddle==3.0.0
```

> 提示: 仅在启用 `use_ocr` 时才需要上述依赖。

#### OCR 速度基准 (随机中文图片, 512 张)

> **测试设备**: NVIDIA GeForce RTX 3070 (8GB 显存)
>
> **提示**: 实际使用时, 请根据 GPU/CPU 内存情况调整 `batch_size`, 过大可能会因内存不足导致程序崩溃

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
