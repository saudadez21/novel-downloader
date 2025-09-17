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

---

### 安装 novel-downloader

(1) 从 PyPI 安装:

```bash
pip install novel-downloader
```

(2) 最新开发版 (从 GitHub 安装)

```bash
# 克隆项目
git clone https://github.com/saudadez21/novel-downloader.git
cd novel-downloader

# 安装为库并生成 CLI
pip install .
```

安装完成后, 会在系统 `PATH` 中生成 `novel-cli` 可执行命令。

---

## 可选功能与依赖说明

### Node.js 解密支持

起点与 QQ 阅读的 VIP 章节解密逻辑基于 JavaScript 实现, 因此需要额外安装 [Node.js](https://nodejs.org/en/download) 来完成解密。

---

### 字体解密 (`decode_font` 参数)

启用解密字体功能时, 需要安装额外依赖 (注意: OCR 准确率大约 98+%):

(1) 安装扩展依赖:

```bash
pip install novel-downloader[font-recovery]
```

(2) 安装 [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) 及其依赖, 请根据 paddlepaddle [文档](https://www.paddlepaddle.org.cn/install/quick?docurl=/documentation/docs/zh/develop/install/pip/windows-pip.html) 选择合适版本 (CPU / GPU 及 CUDA 支持):

**CPU 版本:**

```bash
python -m pip install paddlepaddle==3.1.1 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/
```

**GPU 版本 (根据 CUDA 版本选择对应包):**

```bash
python -m pip install paddlepaddle-gpu==3.1.1 -i https://www.paddlepaddle.org.cn/packages/stable/cu118/
```

(3) 根据 PaddleOCR [文档](https://www.paddleocr.ai/latest/version3.x/installation.html) 安装 PaddleOCR:

```bash
pip install paddleocr
```

**开发环境版本**

```bash
paddleocr==3.2.0
paddlepaddle==3.1.1
```

(4) 编辑 `settings.toml` 配置文件, 开启字体解密功能, 并指定 OCR 模型:

```toml
[general.font_ocr]
decode_font = true  # 是否尝试本地解码混淆字体
batch_size = 32
model_name = "PP-OCRv5_mobile_rec"
```

可选模型参考 [OCR 性能基准](#ocr-性能基准)

---

**常见报错与解决方法**

报错示例 (当 Windows 用户名包含中文时):

```bash
FontOCR initialization failed: (NotFound) Cannot open file
C:\Users\用户名.paddlex\official_models\PP-OCRv5_mobile_rec\inference.json, please confirm whether the file is normal.
[Hint: Expected paddle::inference::IsFileExists(prog_file_) == true, but received paddle::inference::IsFileExists(prog_file_):0 != true:1.]
```

解决方法: 将模型文件移动到不含中文的路径, 并在 `settings.toml` 中指定 `model_dir`:

```toml
[general.font_ocr]
decode_font = true
batch_size = 32
model_name = "PP-OCRv5_mobile_rec"
model_dir = 'D:\pdx_models\PP-OCRv5_mobile_rec'  # 改成实际路径
```

> 模型目录至少需要包含: `inference.pdmodel`, `inference.pdiparams`, `inference.json`

---

### OCR 性能基准

**目标**: 评估处理「单章节」的平均耗时与识别准确率。

> **测试环境**: Intel 12900H; NVIDIA GeForce RTX 3070 (8 GB 显存)
>
> **参数**: `batch_size = 32`
>
> **提示**: 实际使用中请根据 GPU/CPU 可用内存调整 `batch_size`: 过大可能因内存不足 (OOM) 或频繁换页导致崩溃或变慢

#### GPU 设备

| 模型 `model_name`      | 平均单章耗时 (秒) | 准确率      |
| ---------------------- | ---------------- | ---------- |
| `PP-OCRv3_mobile_rec`  | **0.666**        | 98.01%     |
| `PP-OCRv4_mobile_rec`  | 1.040            | 99.14%     |
| `PP-OCRv4_server_rec`  | 1.231            | 99.52%     |
| `PP-OCRv5_mobile_rec`  | 1.111            | 99.91%     |
| `PP-OCRv5_server_rec`  | 1.890            | **99.97%** |

#### CPU 设备

| 模型 `model_name`      | 平均单章耗时 (秒) | 准确率      |
| ---------------------- | ---------------- | ---------- |
| `PP-OCRv3_mobile_rec`  | **1.426**        | 98.01%     |
| `PP-OCRv5_mobile_rec`  | 1.957            | 99.91%     |
| `PP-OCRv4_mobile_rec`  | 4.135            | 99.14%     |
| `PP-OCRv5_server_rec`  | 688.163          | 99.97%     |
| `PP-OCRv4_server_rec`  | 733.195          | 99.52%     |

#### 已知现象 / 注意事项

* 使用 `PP-OCRv5` 时, 偶尔会返回繁体字 (如将简体 "杰" 识别为 "傑"), 并出现个别字符异常 (如 "口" 被识别为 "□")
* 使用 `PP-OCRv3` 时, 偶尔会出现识别为空串 (不返回任何文字) 的情况
* 在 CPU 上, Server 版耗时显著高于 Mobile 版; 若无 GPU, 优先考虑 Mobile 版以平衡速度与精度
