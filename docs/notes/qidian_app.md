---
title: Qidian App Analysis Notes
date: 2025-06-17
---

# 起点小说 App 端分析笔记

创建日期: 2025/06/17

## 一、起点客户端请求逻辑

### 1. Header 字段

字段:

* `borgus`
* `cecelia`
* `cookie`
    * `ywguid`
    * `appId`
    * ...
    * `QDInfo`
* `gorgon`
* `ibex`
* `qdinfo`
* `qdsign`
* `tstamp`

其中每次请求改变的值有:

* `borgus`
* `cecelia`
* `cookie`
    * `QDInfo`
* `ibex`
* `qdinfo`
* `qdsign`
* `tstamp`

具体暂时不分析, 可能有用的参考资料:

* [iOS逆向记录](https://blog.csdn.net/weixin_44110940/article/details/141091917)
    * 没有详细过程
* [起点 App 字段加密破解_java](https://www.cnblogs.com/HugJun/p/13503215.html)
    * 2020-08-14
    * Java 版本
    * 包含: `QDInfo`, `QDSign`, `AegisSign`
* [Android逆向入门: 某点中文app网络请求参数分析](https://www.jianshu.com/p/025bd308e857)
    * 2020-08-05
    * 包含: `QDInfo`, `QDSign`, `AegisSign`
    * [备用连接](https://www.52pojie.cn/thread-1239814-1-1.html)
* [QiDianHook](https://github.com/rwz657026189/QiDianHook)
    * 2019-01-03
    * 没试过
* [appspiderHook](https://github.com/madking177/appspiderHook)
    * 2023-12-11
    * 包含一些 hook 函数
* [frida复现某app算法](https://www.wangan.com/p/11v71355c0c48670)
    * 2023-01-11
    * 含过程
* [某应用sign签名算法还原](https://bbs.kanxue.com/thread-271070.htm)
    * 2022-1-7
    * 含过程
    * 包含: `QDSign`
* [起点QDSign AegisSign逆向](https://www.jianshu.com/p/58ec69e04983)
    * 2022-01-12
* [起点中文网安卓APP超详细算法分析过程](https://bbs.125.la/forum.php?mod=viewthread&tid=14053235)
    * 2017-8-8

注: 经过分析, 这些 header 字段应该主要是 `com.qidian.QDReader.component.util.FockUtil` 的 `addRetrofitH` 函数添加的

### 2. 主要接口一览

#### 2.1 获取书籍基础信息

**功能**: 查询某本书的详情。

**URL**

```
GET https://druidv6.if.qidian.com/argus/api/v3/bookdetail/lookfor
```

**Query 参数**:

| 字段      | 类型  | 必选 | 含义                   |
| --------- | ---- | ---- | ---------------------- |
| bookId    | int  | 是   | 起点书籍唯一 ID         |
| isOutBook | int  | 否   | 是否为外部导入的书 (0/1) |

**示例 param**:

```json
{
    "bookId": 1234567,
    "isOutBook": 0,
}
```

#### 2.2 获取未购买章节列表

**功能**: 拉取当前用户未购买章节及章节卡信息。

**URL**

```
POST https://druidv6.if.qidian.com/argus/api/v2/subscription/getunboughtchapterlist
```

**Body 参数**:

| 字段       | 类型  | 必选 | 含义            |
| --------- | --- | -- | ------------- |
| bookId    | int | 是  | 书籍 ID         |
| pageSize  | int | 是  | 每页大小, 默认 99999 |
| pageIndex | int | 是  | 页码, 从 1 开始     |

**示例 Body**:

```json
{
    "bookId": 1234567,
    "pageSize": 99999,
    "pageIndex": 1
}
```

#### 2.3 获取已购买章节 ID 列表

**功能**: 获取用户已购买的所有章节 ID, 便于本地校验缓存。

**URL**

```
GET https://druidv6.if.qidian.com/argus/api/v3/chapterlist/chapterlist
```

**Query 参数**:

| 字段               | 类型     | 必选 | 含义                         |
| ---------------- | ------ | -- | -------------------------- |
| bookId           | int    | 是  | 书籍 ID                      |
| timeStamp        | long   | 是  | 毫秒时间戳                      |
| requestSource    | int    | 是  | 来源标识, 0=App 等         |
| md5Signature     | string | 是  | MD5 |
| extendchapterIds | string | 否  | 扩展查询章节 ID 列表         |

**`md5Signature` 计算说明**:

将本地已存在的章节 ID 与对应的卷 ID 按阅读顺序用竖线拼接, 得到形如:

```
cid1|vcode1|cid2|vcode2|...|cidN|vcodeN
```

对该字符串取 `MD5`, 结果即为 `md5Signature`。

**示例 param**:

```json
{
    "bookId": 1234567,
    "timeStamp": 1750000000000,
    "requestSource": 0,
    "md5Signature": "5f4dcc3b5aa765d61d8327deb882cf99",
    "extendchapterIds": "2345678,3456789"
}
```

#### 2.4 获取彩蛋章节列表

**功能**: 获取主线章节后面附带的「彩蛋」章节列表。

**URL**

```
GET https://druidv6.if.qidian.com/argus/api/v1/midpage/book/chapters
```

**Query 参数**: `bookId`

**示例 param**:

```json
{
    "bookId": 1234567,
}
```

**示例返回**:

```json
{
    "Data": {
        "Chapters": [
            {
                "ChapterId": 12345678,
                "MidpageList": [
                    {"MidpageId": 8888, "MidpageName":"彩蛋1","UpdateTime":1686868686868},
                    {"MidpageId": 9999, "MidpageName":"彩蛋2","UpdateTime":1686868687878}
                ]
            }
        ]
    }
}
```

**字段说明**

* `MidpageList` 中 `UpdateTime` 为 UTC 毫秒。
* 可据此在本地拼接阅读顺序。

#### 2.5 获取彩蛋章节内容

**功能**: 获取「彩蛋」章节内容。

**URL**

```
GET https://druidv6.if.qidian.com/argus/api/v3/midpage/pageinfo
```

**Query 参数**:

| 字段               | 类型     | 必选 | 含义                         |
| ---------------- | ------ | -- | -------------------------- |
| bookId           | int    | 是  | 书籍 ID                      |
| chapterId        | int   | 是  | 章节 ID                      |
| needAdv    | int    | 是  | 默认 0         |

**示例 param**:

```json
{
    "bookId": 1234567,
    "chapterId": 12345678,
    "needAdv": 0,
}
```

#### 2.6 下载章节内容

##### VIP 章节下载

**URL**

```
POST https://druidv6.if.qidian.com/argus/api/v4/bookcontent/getvipcontent
```

**Body**:

| 字段       | 含义         |
| -------- | ---------- |
| b        | bookId     |
| c        | chapterId  |
| ui       | 不确定 |
| b-string | 加密包标识      |

**示例 Body**:

```json
{
    "b-string": "",
    "b": 1234567,
    "c": 555555,
    "ui": 0,
}
```

##### 安全下载

**URL**

```
GET https://druidv6.if.qidian.com/argus/api/v2/bookcontent/safegetcontent
```

**Query**: `bookId`, `chapterId`

**示例 param**:

```json
{
    "bookId": 1234567,
    "chapterId": 555555,
}
```

##### 批量下载

**URL**

```
POST https://druidv6.if.qidian.com/argus/newapi/v1/bookcontent/getcontentbatch
```

**Body**:

```json
{
    "b":1234567,
    "c":"555,222,333,444,666,888",
    "useImei":0
}
```

**返回**包含 `DownloadUrl`、`Key`、`Md5`、`Size`, 需后续 GET COS 链接下载 ZIP, 然后解包。

注意: `DownloadUrl` 是加密状态需要使用 `Fock` 的 `unlock` 进行解密

<details>
<summary>相关函数 (点击展开)</summary>

```java
// 调用:
unLockContent = qDChapterBatchDownloadLoader.unLockContent(qDChapterBatchDownloadLoader.getBookId(), key, downloadUrl);
```

`qDChapterBatchDownloadLoader.unLockContent`:

```java
public final String unLockContent(long j10, String str, String str2) {
    if (str2 == null || str2.length() == 0) {
        return "";
    }
    String valueOf = String.valueOf(j10);
    String str3 = "BatchChapterCos_" + j10 + "_" + str;
    FockUtil fockUtil = FockUtil.INSTANCE;
    Fock.FockResult unlock = fockUtil.unlock(str2, valueOf, str3);
    if (unlock.status == Fock.FockResult.STATUS_EMPTY_USER_KEY) {
        Fock.setup(we.d.X());
        unlock = fockUtil.unlock(str2, valueOf, str3);
    }
    if (unlock.status != 0) {
        return "";
    }
    byte[] bArr = unlock.data;
    kotlin.jvm.internal.o.d(bArr, "unlockResult.data");
    Charset UTF_8 = StandardCharsets.UTF_8;
    kotlin.jvm.internal.o.d(UTF_8, "UTF_8");
    return new String(bArr, UTF_8);
}
```

</details>

#### 2.7 获取书籍封面

支持两种图片格式: WebP 和 JPEG。

请将以下 URL 中的占位符替换为实际值:

* **`{book_id}`**: 书籍的唯一 ID
* **`{width}`**: 封面宽度, 单位为像素, 可选值: `90`、`150`、`180`、`300`、`600`

**WebP 格式**

```
https://bookcover.yuewen.com/qdbimg/349573/{book_id}/{width}.webp
```

**JPEG 格式**

```
https://bookcover.yuewen.com/qdbimg/349573/{book_id}/{width}
```

##### 使用示例

获取 `book_id = 123456`, 宽度为 `300px` 的 WebP 封面:

```
https://bookcover.yuewen.com/qdbimg/349573/123456/300.webp
```

获取同一书籍的 JPEG 封面:

```
https://bookcover.yuewen.com/qdbimg/349573/123456/300
```

---

## 二、`*.qd` 文件结构与内容解析

### 1. 文件目录结构

`*.qd` 文件主要用于存储起点 App 的本地缓存数据, 安卓端位于以下路径:

```sh
/data/media/0/Android/data/com.qidian.QDReader/files/QDReader/book/{user_id}/
```

或

```sh
/sdcard/Android/data/com.qidian.QDReader/files/QDReader/book/{user_id}/
```

或

```sh
/storage/emulated/0/Android/data/com.qidian.QDReader/files/QDReader/book/{user_id}/
```

该目录结构如下所示:

```sh
{user_id}/
│
├── {book_id}.qd               # 书籍的元信息
│
└── {book_id}/                 # 子目录, 按章节存储内容
    ├── {chap_id}.qd           # 章节的数据文件
    ├── {chap_id}.qd
    └── ...
```

以下分析基于示例代码:

```python
from pathlib import Path
from pprint import pprint

book_id = "123456"
metadata_path = Path.cwd() / "data" / f"{book_id}.qd"
chap_dir = Path.cwd() / "data" / book_id
```

### 2. `{book_id}.qd` 内容解析

#### 2.1 文件标头识别 (Header)

读取前 16 个字节用于识别文件格式:

```python
with open(metadata_path, "rb") as f:
    header = f.read(16)
    print(header)
```

输出:

```bash
b'SQLite format 3\x00'
```

文件为 SQLite 3 格式数据库

#### 2.2 数据库结构查看

通过 SQLite3 库查询数据库中包含的表:

```python
import sqlite3

conn = sqlite3.connect(metadata_path)
query = "SELECT name FROM sqlite_master WHERE type='table';"

cursor = conn.cursor()
cursor.execute(query)
tables = cursor.fetchall()
pprint(tables)

conn.close()
```

输出示例:

```bash
[('chapter',),
 ('volume',),
 ('bookmark',),
 ('sqlite_sequence',),
 ('new_markline',),
 ('chapterExtraInfo',)]
```

#### 2.3 表数据采样

获取各表中前几条数据作为示例:

```python
conn = sqlite3.connect(metadata_path)
cursor = conn.cursor()

table_previews = {}

for (table_name,) in tables:
    cursor.execute(f"SELECT * FROM {table_name} LIMIT 2;")
    rows = cursor.fetchall()
    table_previews[table_name] = rows

conn.close()

pprint(table_previews)
```

---

### 3. `{chap_id}.qd` 内容解析

> 声明: 本文为笔者首次尝试进行 Android 应用的逆向分析, 相关方法和思路均基于个人现阶段理解, 主要目的在于探索学习。部分手段可能存在更优或更规范的实现方式, 欢迎指正与交流。

#### 所用工具与依赖

用于分析和提取章节 `.qd` 文件内容, 涉及以下工具与库:

##### 逆向分析工具

* [`jadx`](https://github.com/skylot/jadx/releases): 用于反编译 APK, 提取 Java 层逻辑
* [`Ghidra`](https://github.com/NationalSecurityAgency/ghidra/releases): 静态分析原生库 (如 `.so` 文件)
* [`IDA Pro`](https://hex-rays.com/ida-pro/): 反汇编工具, 用于静态分析本地代码
* [`Android Platform Tools (adb)`](https://developer.android.com/tools/releases/platform-tools): 用于连接调试设备
* [`Frida`](https://github.com/frida/frida): 动态插桩与函数 Hook, 辅助定位或调用加密逻辑

##### Python 依赖

* `frida==16.7.19` 与 `frida-tools==13.7.1`
    * 版本 17.x 及以上目前暂时存在 Java 环境问题, 需要手动处理
    * 相关讨论见: [Java is not defiend](https://github.com/frida/frida/issues/3473)
* `pycryptodome`
    * 加解密算法库

#### 3.1 ADB 连接设备

通过 ADB 与目标设备建立连接:

```sh
adb connect <device-ip>
```

可使用 `adb devices` 验证连接状态

#### 3.2 配置 `Frida`

##### 检查设备架构

使用以下命令确认设备架构:

```sh
adb shell getprop ro.product.cpu.abi
```

常见返回值包括:

* `x86`
* `x86_64`
* `arm64-v8a`

根据架构与所用 Frida Python 版本, 从 [Frida Releases](https://github.com/frida/frida/releases) 下载对应的 `frida-server`, 例如:

```
frida-server-16.7.19-android-x86.xz
```

##### 安装与授权

解压后将可执行文件推送到设备 (这里解压后重命名为 `frida-server-16.7.19`)

```sh
adb push frida-server-16.7.19 /data/local/tmp/
adb shell "chmod 755 /data/local/tmp/frida-server-16.7.19"
```

启动服务 (需要 `root` 权限):

```sh
adb shell
su
/data/local/tmp/frida-server-16.7.19 &
```

##### 验证连接

在电脑终端使用以下命令列出设备进程, 确认 Frida 服务启动成功:

```sh
frida-ps -U
```

若成功, 可看到设备进程列表, 其中起点对应为:

* `起点读书`
* `com.qidian.QDReader`

#### 3.3 获取原生日志

为便于后续排查信息, 这里全量导出 `logcat` 日志:

```sh
adb logcat > logs.txt
```

后续配合关键字筛查

#### 3.4 使用 Frida Hook 日志函数

> **说明**:
>
> 下述方法仅用于演示如何通过 Hook 日志接口来获取 **App 的原始日志**。
>
> **在后续的实际分析流程中并未使用到该方法**, 这里只是提出一种可选的调试手段, 便于在必要时辅助排查部分流程。

在后续分析中, 通过 `jadx` 反编译发现该应用采用了腾讯开源的 [Mars](https://github.com/Tencent/Mars) 框架中的 `xlog` 模块进行日志输出。

为了捕获应用在加密前输出的原始调试信息, 可使用 Frida 编写脚本, Hook `Xlog` 类中的日志打印方法, 实现实时日志拦截:

<details>
<summary>`hook_xlog.js` (点击展开)</summary>

```js
Java.perform(function () {
    const Xlog = Java.use("com.tencent.mars.xlog.Xlog");

    function hookLog(level, method) {
        if (!Xlog[method]) {
            console.log("Method not found:", method);
            return;
        }

        Xlog[method].overload('java.lang.String', 'java.lang.String', 'java.lang.String', 'int', 'int', 'long', 'long', 'java.lang.String')
            .implementation = function (tag, filename, funcname, line, pid, tid, maintid, msg) {
                const fullMsg = `[${level}][${tag}] ${msg}`;
                console.log(fullMsg);
                return this[method](tag, filename, funcname, line, pid, tid, maintid, msg);
            };
    }

    hookLog("V", "logV");
    hookLog("D", "logD");
    hookLog("I", "logI");
    hookLog("W", "logW");
    hookLog("E", "logE");
});
```
</details>

执行 Hook:

```sh
frida -U -n 起点读书 -l hook_xlog.js
```

#### 3.5 解密逻辑分析

APK 解包后, 可使用 `jadx` 反编译并定位到 `com/qidian/QDReader/component/bll` 包中的核心方法

??? note "核心解密函数 (点击展开)"

    --8<-- "docs/data/qidian_app_func_H.md"

解密流程可概括为:

1. **文件分段读取**: 使用 `W(file, ...)` 按小端格式读取 5 段数据
2. **第一阶段解密**: 将 `part1` 传入 `x(...)` 调用 native 接口 `a.b.b(...)`, 返回 JSON 字符串
3. **JSON 解析**: 提取 `content`、`type`、`code`、`msg` 等字段
4. **VIP 章节二次解密**: `type == FOCK` 时, 调用 `FockUtil.unlock(...)` 解密
5. **附加数据块处理**

##### 3.5.1 `W` 函数 -- 分段读取逻辑

`W` 函数的核心思路是在文件输入流上依次读取 5 段数据, 每段前 4 字节表示该段的长度 (little-endian), 随后读取对应长度的原始字节。

```java
FileInputStream fileInputStream;
byte[] bArr;
byte[] bArr2;
byte[] bArr3;
byte[] bArr4;
byte[] bArr5;
fileInputStream = new FileInputStream(file);
int iR = com.qidian.common.lib.util.m.r(fileInputStream);
bArr2 = new byte[iR];
fileInputStream.read(bArr2, 0, iR);
int iR2 = com.qidian.common.lib.util.m.r(fileInputStream);
bArr3 = new byte[iR2];
fileInputStream.read(bArr3, 0, iR2);
int iR3 = com.qidian.common.lib.util.m.r(fileInputStream);
bArr4 = new byte[iR3];
fileInputStream.read(bArr4, 0, iR3);
int iR4 = com.qidian.common.lib.util.m.r(fileInputStream);
bArr = new byte[iR4];
fileInputStream.read(bArr, 0, iR4);
int iR5 = com.qidian.common.lib.util.m.r(fileInputStream);
bArr5 = new byte[iR5];
fileInputStream.read(bArr5, 0, iR5);
dVar.f18975search = new byte[][]{bArr2, bArr3, bArr4, bArr, bArr5};
```

其中, `com.qidian.common.lib.util.m.r` 用于读取 4 字节长度并转换为 `int`:

```java
public static int r(InputStream inputStream) throws IOException {
    byte[] bArr = new byte[4];
    inputStream.read(bArr);
    ByteBuffer byteBufferWrap = ByteBuffer.wrap(bArr);
    byteBufferWrap.order(ByteOrder.LITTLE_ENDIAN);
    return byteBufferWrap.getInt();
}
```

由此可得文件整体格式:

```
[len0][data0]
[len1][data1]
[len2][data2]
[len3][data3]
[len4][data4]
```

##### Python 等价实现

在 Python 中可用 `BytesIO` 对相同逻辑进行复现:

```python
from io import BytesIO
from pathlib import Path

path = Path("xxx.qd")
with path.open('rb') as f:
    buf = BytesIO(f.read())

def read_chunk():
    # 先读 4 字节 little-endian length
    raw = buf.read(4)
    if len(raw) < 4:
        raise IOError("文件结构不完整")
    length = int.from_bytes(raw, byteorder='little')
    # 再读对应长度
    return buf.read(length)

chunk0 = read_chunk()
chunk1 = read_chunk()
chunk2 = read_chunk()
chunk3 = read_chunk()
chunk4 = read_chunk()
```

##### 3.5.2 `x` 函数 -- Native 解密流程

点击查看 `x` 函数, 发现该方法主要调用本地 JNI 接口完成解密, 例如:

```java
// private static byte[] x(byte[] bArr, long j10, long j11)
// ...
byte[] bArrB2 = a.b.b(j10, j11, bArr, QDUserManager.getInstance().k(), we.d.I().d());
if (bArrB2 != null) {
    return bArrB2;
}
```

在 `a/b.java` 中发现是 native 函数:

```java
public class b {
    static {
        try {
            System.loadLibrary("load-jni");
        } catch (Exception e10) {
            e10.printStackTrace();
        } catch (UnsatisfiedLinkError e11) {
            e11.printStackTrace();
        }
    }

    public static native byte[] b(long j10, long j11, byte[] bArr, long j12, String str);

    // ...
}
```

使用 Ghidra (或 IDA) 对 `libload-jni.so` 进行反汇编分析后. 可快速定位到对应的 native 方法实现 `Java_a_b_b`:

??? note "Java_a_b_b 实现片段 (点击展开)"

    --8<-- "docs/data/qidian_app_func_Java_a_b_b.md"

在函数中意外发现该方法内部大量调用了 `__android_log_print` 打印中间变量 (如解密参数 / 密钥等)。

这使得不需要额外 Hook 函数, 也可以直接通过 logcat 查看解密过程中涉及的关键信息。

于是回头检查之前导出的 `logs.txt`, 使用关键词快速定位到相关日志内容:

```log
06-01 12:00:00.000  1234  4321 D QDReader_Jni: bookid: ****,chapterid: ***,userid: **,imei: ****
...
06-01 12:00:00.000  1234  4321 D QDReader_Jni: sha1id:****
...
06-01 12:00:00.000  1234  4321 D QDReader_Jni: sha1key1 = ****base64-key****
...
06-01 12:00:00.000  1234  4321 D QDReader_Jni: JNI:8 sha1key2:****key2**** sha1key1:****key1****
...
06-01 12:00:00.000  1234  4321 D QDReader_Jni: JNI:22 ****
```

结合日志输出与 Ghidra 中对 `Java_a_b_b` 的分析. 可以还原出等价的 Python 解密逻辑如下:

```python
import hashlib
import hmac
from base64 import b64encode
from Crypto.Cipher import DES3
from Crypto.Util.Padding import unpad

_MAGIC = "2EEE1433A152E84B3756301D8FA3E69A"

def _pad_to_24(s: str) -> str:
    """
    Ensure the given string is exactly 24 characters long.

    :param s: Input string.
    :return: 24-character string.
    """
    if len(s) >= 24:
        return s[:24]
    return s + ("\x00" * (24 - len(s)))

def _hmac_sha1(key: str, data: str) -> str:
    """
    Compute HMAC-SHA1 over `data` using `key`, Base64-encode the result,
    then truncate/pad to 24 characters.

    :param key: ASCII key string.
    :param data: ASCII data string.
    :return: 24-character Base64 HMAC-SHA1 string.
    """
    digest = hmac.new(key.encode(), data.encode(), hashlib.sha1).digest()
    b64 = b64encode(digest).decode()
    return _pad_to_24(b64)

def _hmac_md5(key: str, data: str) -> str:
    """
    Compute HMAC-MD5 over `data` using `key`, Base64-encode the result,
    then truncate/pad to 24 characters.

    :param key: UTF-8 key string.
    :param data: UTF-8 data string.
    :return: 24-character Base64 HMAC-MD5 string.
    """
    digest = hmac.new(key.encode(), data.encode(), hashlib.md5).digest()
    b64 = b64encode(digest).decode()
    return _pad_to_24(b64)

def _des3_decrypt(data: bytes, secret: str) -> bytes:
    """
    Decrypt `data` using 3DES (DES-EDE/CBC/PKCS5Padding) with a zero IV.
    If `secret` is 16 bytes long, its first 8 bytes are appended to make 24.

    :param data: Ciphertext bytes.
    :param secret: Key string (will be .encode('utf-8')).
    :return: Plaintext bytes (PKCS#5 padding removed).
    """
    key_bytes = secret.encode()
    if len(key_bytes) == 16:
        key_bytes += key_bytes[:8]
    cipher = DES3.new(key_bytes, DES3.MODE_CBC, iv=b'\x00' * 8)
    decrypted = cipher.decrypt(data)
    return unpad(decrypted, block_size=8)

def decrypt_content(
    cid: str,
    data: bytes,
    uid: str,
    imei: str,
) -> str:
    """
    Perform the two-stage DES3 decryption matching the native `b(...)`:

      1. sec1 = uid + imei + cid + _MAGIC
      2. sha1_key1 = HMAC-SHA1_Base64(imei, sec1) -> 24 chars
      3. sec2 = sha1_key1 + imei
      4. sha1_key2 = HMAC-MD5_Base64(uid, sec2) -> 24 chars
      5. step1 = DES3_CBC_DECRYPT(data, key=sha1_key2)
      6. step2 = DES3_CBC_DECRYPT(step1,   key=sha1_key1)
      7. UTF-8 decode step2 (ignore errors)

    :param cid: Chapter ID string.
    :param data: Encrypted bytes to decrypt.
    :param uid: User ID string.
    :param imei: Device IMEI string.
    :return: Decrypted plaintext as a UTF-8 string.
    """
    # 1) build the two "sec" buffers and derive two keys
    sec1 = uid + imei + cid + _MAGIC
    sha1_key1 = _hmac_sha1(imei, sec1)
    sec2 = sha1_key1 + imei
    sha1_key2 = _hmac_md5(uid, sec2)

    # 2) two-pass 3DES decryption
    step1 = _des3_decrypt(data, sha1_key2)
    step2 = _des3_decrypt(step1, sha1_key1)

    return step2.decode("utf-8", errors="ignore")  # or "replace"
```

##### 3.5.3 `fockUtil.unlock` 函数

在分析 `unlock` 函数时, 发现这又是一个 native 函数:

<details>
<summary>`com.yuewen.fock` (点击展开)</summary>

```java
package com.yuewen.fock;

public class Fock {
    public static class FockResult {
        public static int STATUS_BAD_DATA = -1;
        public static int STATUS_EMPTY_USER_KEY = -3;
        public static int STATUS_MISSING_KEY_POOL = -2;
        public static int STATUS_SUCCESS;
        public final byte[] data;
        public final int dataSize;
        public final int status;

        public FockResult(int i10, byte[] bArr, int i11) {
            this.status = i10;
            this.data = bArr;
            this.dataSize = i11;
        }
    }

    static {
        System.loadLibrary("fock");
        ignoreBlockPattern = Pattern.compile(ignoreBlockPatternString);
    }

    public static void addKeys(String str, String str2) {
        byte[] bArrDecode = Base64.decode(str, 0);
        ReentrantLock reentrantLock = lock;
        reentrantLock.lock();
        try {
            ak(bArrDecode, bArrDecode.length, str2.getBytes());
            reentrantLock.unlock();
        } catch (Throwable th2) {
            lock.unlock();
            throw th2;
        }
    }
    private static native void ak(byte[] bArr, int i10, byte[] bArr2);

    public static void setup(String str) {
        ReentrantLock reentrantLock = lock;
        reentrantLock.lock();
        try {
            it(str.getBytes(), str.length());
            reentrantLock.unlock();
        } catch (Throwable th2) {
            lock.unlock();
            throw th2;
        }
    }
    private static native int it(byte[] bArr, int i10);

    public static FockResult unlock(String str, String str2, String str3) {
        byte[] bArrDecode = Base64.decode(str, 0);
        ReentrantLock reentrantLock = lock;
        reentrantLock.lock();
        try {
            FockResult fockResultUksf = uksf(bArrDecode, bArrDecode.length, str2.getBytes(), str2.length(), str3.getBytes());
            reentrantLock.unlock();
            return fockResultUksf;
        } catch (Throwable th2) {
            lock.unlock();
            throw th2;
        }
    }
    private static native FockResult uksf(byte[] bArr, int i10, byte[] bArr2, int i11, byte[] bArr3);
}
```
</details>

---

方案 1. 使用 `Frida` 对相关方法进行 Hook

> 说明: 此处演示的 Hook 方法为了方便展示, 假设目标类已在运行时加载完毕。
>
> 如果实际使用, 请确保 App 已进入能触发 Fock 等类初始化的页面, 例如打开任意 VIP 章节, 以确保目标类和方法 (如 `Fock` 等) 已加载并初始化, 否则 Hook 将无法生效。

<details>
<summary>`hook_fock.js` (点击展开)</summary>

```js
rpc.exports = {
    unlock: function (arg1, arg2, arg3) {
        return new Promise(function (resolve, reject) {
            Java.perform(function () {
                try {
                    var TargetClass = Java.use('com.yuewen.fock.Fock');
                    var StringClass = Java.use('java.lang.String');
                    var CharsetClass = Java.use('java.nio.charset.Charset');

                    var result = TargetClass.unlock(arg1, arg2, arg3);
                    var status = result.status.value;

                    var utf8Charset = CharsetClass.forName("UTF-8");
                    var javaStr = StringClass.$new(result.data.value, utf8Charset);
                    var contentStr = javaStr.toString();

                    resolve({
                        status: status,
                        content: contentStr
                    });
                } catch (e) {
                    resolve({
                        status: -999,
                        error: e.toString()
                    });
                }
            });
        });
    }
};
```
</details>

至此即可在 Python 端通过 `Frida RPC` 同步调用 `unlock` 方法, 示例如下

```python
import frida

def test():
    book_id = "1111111111"
    chap_id = "2222222222"
    content = "xxx..." # 需解密的加密内容

    device = frida.get_device("your.device.ip.address")
    # 也可使用 frida.get_usb_device()
    session = device.attach("起点读书")

    with open("hook_fock.js", "r", encoding="utf-8") as f:
        jscode = f.read()

    script = session.create_script(jscode)
    script.load()

    print("[*] Script loaded. Starting unlock tasks...")
    key_1 = chap_id
    key_2 = f"{book_id}_{chap_id}"
    # 同步调用 Frida RPC
    raw = script.exports_sync.unlock(content, key_1, key_2)
    print(raw)

if __name__ == "__main__":
    test()
```

---

方案 2. 逆向并实现

TODO: 暂未完成
