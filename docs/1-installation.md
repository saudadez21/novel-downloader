## 安装

### Python 环境

为避免包冲突, 建议使用虚拟环境:

```bash
python -m venv .venv
source .venv/bin/activate
# Windows: .venv\Scripts\activate
```

---

### 安装 novel-downloader

(1) 从 PyPI 安装

```bash
pip install novel-downloader
```

安装后将提供以下可执行命令:

* `novel-cli`
* `novel-web` (如需使用 Web GUI, 需另行安装其依赖, 见下文)

(2) 安装最新开发版 (GitHub)

```bash
git clone https://github.com/saudadez21/novel-downloader.git
cd novel-downloader
```

如需编译多语言支持:

```bash
pip install babel
pybabel compile -d src/novel_downloader/locales
```

安装:

```bash
pip install .
```

---

## 可选功能与依赖说明

`novel-downloader` 提供多个可选模块，可根据需要选择性安装。

### Web 图形界面 (可选)

Web GUI 基于 `NiceGUI`, 默认不会随主程序安装。

如需使用 Web 图形界面, 请先安装对应可选依赖:

```bash
pip install novel-downloader[web-ui]
```

启动 GUI：

```bash
novel-web
```

若需局域网 / 外网访问 (请自行评估风险):

```bash
novel-web --listen public
```

运行中可按 `CTRL+C` 停止服务。

### 可插拔式 HTTP 后端 (可选)

默认使用 `aiohttp`, 如果需要切换其他后端, 可安装对应依赖。

#### httpx 后端

支持 HTTP/1.1 与 HTTP/2:

```bash
pip install httpx[http2]
```

启用方式 (`settings.toml`):

```toml
[general]
backend = "httpx"
```

#### curl_cffi 后端

支持 `libcurl` 与浏览器仿真 (impersonate):

```bash
pip install curl_cffi
```

启用方式:

```toml
[general]
backend = "curl_cffi"
impersonate = "chrome136"
```

---

### Node.js 解密支持 (部分站点必须)

起点 / QQ 阅读等站点的 VIP 章节解密逻辑基于 JavaScript, 需要安装 Node.js。

下载安装地址:

[Download Node.js](https://nodejs.org/en/download)

安装后可自动用于相关站点的解密流程。

---

### 字体混淆还原与图片章节 OCR (`enable_ocr`)

如需处理「字体混淆章节」或「图片章节 -> 文字」, 需启用 OCR 模块。

OCR 分为两部分:

* 额外 Python 依赖 (`image-utils`)
* PaddleOCR 推理框架 (启用文本识别)

以下为完整安装流程。

(1) 安装扩展依赖

```bash
pip install novel-downloader[image-utils]
```

这将安装:

* pillow
* numpy
* fonttools
* brotli
* 等处理字体与图片的依赖包

(2) 安装 PaddlePaddle (CPU 或 GPU)

请根据你的环境选择 CPU 或 GPU 版本及 CUDA 支持。

官方安装说明: [文档](https://www.paddlepaddle.org.cn/install/quick?docurl=/documentation/docs/zh/develop/install/pip/windows-pip.html)

**CPU 版本:**

```bash
python -m pip install paddlepaddle==3.1.1 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/
```

**GPU 版本 (据 CUDA 版本选择):**

```bash
python -m pip install paddlepaddle-gpu==3.1.1 -i https://www.paddlepaddle.org.cn/packages/stable/cu118/
```

(3) 安装 PaddleOCR

官方安装说明: [文档](https://www.paddleocr.ai/latest/version3.x/installation.html)

```bash
pip install paddleocr
```

**开发测试环境使用版本**:

```bash
paddleocr==3.2.0
paddlepaddle==3.1.1
```

(4) 启用字体混淆还原 (`enable_ocr`)

编辑 `settings.toml`:

```toml
[general.font_ocr]
enable_ocr = true  # 是否尝试本地解码混淆字体
batch_size = 32
model_name = "PP-OCRv5_mobile_rec"
```

---

**OCR 常见错误与处理**

(1) 路径含中文导致模型加载失败 (Windows)

示例报错:

```bash
(NotFound) Cannot open file
C:\Users\用户名.paddlex\official_models\PP-OCRv5_mobile_rec\inference.json, please confirm whether the file is normal.
[Hint: Expected paddle::inference::IsFileExists(prog_file_) == true, but received paddle::inference::IsFileExists(prog_file_):0 != true:1.]
```

解决方法:

1. 将模型目录移动到不含中文的路径
2. 在 `settings.toml` 指定完整路径:

```toml
[general.font_ocr]
enable_ocr = true
batch_size = 32
model_name = "PP-OCRv5_mobile_rec"
model_dir = 'D:\pdx_models\PP-OCRv5_mobile_rec'  # 改成实际路径
```

模型目录通常必须包含:

* `inference.pdmodel`
* `inference.pdiparams`
* `inference.json`

---

### OCR 性能基准 (参考)

**目标**: 评估处理「单章节」的平均耗时与识别准确率。

**测试环境**:

* Intel 12900H
* NVIDIA RTX 3070 (8GB)
* `batch_size = 32`

> 注: 实际请根据设备内存调整 `batch_size`。

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
* CPU 上 server 版耗时极高, 若无 GPU 不建议使用 server 模型
