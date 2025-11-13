# 起点小说 App 端分析笔记

创建日期: 2025/06/17

**快速跳转:**

* [一、起点客户端请求逻辑](#一起点客户端请求逻辑)
* [二、`*.qd` 文件结构与内容解析](#二qd-文件结构与内容解析)

## 一、起点客户端请求逻辑

### 1. Header 字段

字段:
- `borgus`
- `cecelia`
- `cookie`
  - `ywguid`
  - `appId`
  - ...
  - `QDInfo`
- `gorgon`
- `ibex`
- `qdinfo`
- `qdsign`
- `tstamp`

其中每次请求改变的值有:
- `borgus`
- `cecelia`
- `cookie`
  - `QDInfo`
- `ibex`
- `qdinfo`
- `qdsign`
- `tstamp`

具体暂时不分析, 可能有用的参考资料:
- [iOS逆向记录](https://blog.csdn.net/weixin_44110940/article/details/141091917)
  - 没有详细过程
- [起点 App 字段加密破解_java](https://www.cnblogs.com/HugJun/p/13503215.html)
  - 2020-08-14
  - Java 版本
  - 包含: `QDInfo`, `QDSign`, `AegisSign`
- [Android逆向入门: 某点中文app网络请求参数分析](https://www.jianshu.com/p/025bd308e857)
  - 2020-08-05
  - 包含: `QDInfo`, `QDSign`, `AegisSign`
  - [备用连接](https://www.52pojie.cn/thread-1239814-1-1.html)
- [QiDianHook](https://github.com/rwz657026189/QiDianHook)
  - 2019-01-03
  - 没试过
- [appspiderHook](https://github.com/madking177/appspiderHook)
  - 2023-12-11
  - 包含一些 hook 函数
- [frida复现某app算法](https://www.wangan.com/p/11v71355c0c48670)
  - 2023-01-11
  - 含过程
- [某应用sign签名算法还原](https://bbs.kanxue.com/thread-271070.htm)
  - 2022-1-7
  - 含过程
  - 包含: `QDSign`
- [起点QDSign AegisSign逆向](https://www.jianshu.com/p/58ec69e04983)
  - 2022-01-12
- [起点中文网安卓APP超详细算法分析过程](https://bbs.125.la/forum.php?mod=viewthread&tid=14053235)
  - 2017-8-8

注: 经过分析, 这些 header 字段应该主要是 `com.qidian.QDReader.component.util.FockUtil` 的 `addRetrofitH` 函数添加的

### 2. 主要接口一览

#### 2.1 获取书籍基础信息

* **功能**: 查询某本书的详情。

* **URL**

  ```
  GET https://druidv6.if.qidian.com/argus/api/v3/bookdetail/lookfor
  ```

* **Query 参数**:

  | 字段        | 类型  | 必选 | 含义             |
  | --------- | --- | -- | -------------- |
  | bookId    | int | 是  | 起点书籍唯一 ID      |
  | isOutBook | int | 否  | 是否为外部导入的书 (0/1) |

* **示例 param**:

  ```json
  {
    "bookId": 1234567,
    "isOutBook": 0,
  }
  ```

#### 2.2 获取未购买章节列表

* **功能**: 拉取当前用户未购买章节及章节卡信息。

* **URL**

  ```
  POST https://druidv6.if.qidian.com/argus/api/v2/subscription/getunboughtchapterlist
  ```

* **Body 参数**:

  | 字段        | 类型  | 必选 | 含义            |
  | --------- | --- | -- | ------------- |
  | bookId    | int | 是  | 书籍 ID         |
  | pageSize  | int | 是  | 每页大小, 默认 99999 |
  | pageIndex | int | 是  | 页码, 从 1 开始     |

* **示例 Body**:

  ```json
  {
    "bookId": 1234567,
    "pageSize": 99999,
    "pageIndex": 1
  }
  ```

#### 2.3 获取已购买章节 ID 列表

* **功能**: 获取用户已购买的所有章节 ID, 便于本地校验缓存。

* **URL**

  ```
  GET https://druidv6.if.qidian.com/argus/api/v3/chapterlist/chapterlist
  ```

* **Query 参数**:

  | 字段               | 类型     | 必选 | 含义                         |
  | ---------------- | ------ | -- | -------------------------- |
  | bookId           | int    | 是  | 书籍 ID                      |
  | timeStamp        | long   | 是  | 毫秒时间戳                      |
  | requestSource    | int    | 是  | 来源标识, 0=App 等         |
  | md5Signature     | string | 是  | MD5 |
  | extendchapterIds | string | 否  | 扩展查询章节 ID 列表         |

* **`md5Signature` 计算说明**

  将本地已存在的章节 ID 与对应的卷 ID 按阅读顺序用竖线拼接, 得到形如:

  ```
  cid1|vcode1|cid2|vcode2|...|cidN|vcodeN
  ```

  对该字符串取 `MD5`, 结果即为 `md5Signature`。

* **示例 param**:

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

* **功能**: 获取主线章节后面附带的「彩蛋」章节列表。

* **URL**

  ```
  GET https://druidv6.if.qidian.com/argus/api/v1/midpage/book/chapters
  ```

* **Query 参数**: `bookId`

* **示例 param**:

  ```json
  {
    "bookId": 1234567,
  }
  ```

* **示例返回**:

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

* **字段说明**

  * `MidpageList` 中 `UpdateTime` 为 UTC 毫秒。
  * 可据此在本地拼接阅读顺序。

#### 2.5 获取彩蛋章节内容

* **功能**: 获取「彩蛋」章节内容。

* **URL**

  ```
  GET https://druidv6.if.qidian.com/argus/api/v3/midpage/pageinfo
  ```

* **Query 参数**:

  | 字段               | 类型     | 必选 | 含义                         |
  | ---------------- | ------ | -- | -------------------------- |
  | bookId           | int    | 是  | 书籍 ID                      |
  | chapterId        | int   | 是  | 章节 ID                      |
  | needAdv    | int    | 是  | 默认 0         |

* **示例 param**:

  ```json
  {
    "bookId": 1234567,
    "chapterId": 12345678,
    "needAdv": 0,
  }
  ```

#### 2.6 下载章节内容

* **VIP 章节下载**

  * **URL**

    ```
    POST https://druidv6.if.qidian.com/argus/api/v4/bookcontent/getvipcontent
    ```
  * **Body**:

    | 字段       | 含义         |
    | -------- | ---------- |
    | b        | bookId     |
    | c        | chapterId  |
    | ui       | 不确定 |
    | b-string | 加密包标识      |

  * **示例 Body**:

    ```json
    {
        "b-string": "",
        "b": 1234567,
        "c": 555555,
        "ui": 0,
    }
    ```

* **安全下载**

  * **URL**

    ```
    GET https://druidv6.if.qidian.com/argus/api/v2/bookcontent/safegetcontent
    ```
  * **Query**: `bookId`, `chapterId`

  * **示例 param**:

    ```json
    {
        "bookId": 1234567,
        "chapterId": 555555,
    }
    ```

* **批量下载**

  * **URL**

    ```
    POST https://druidv6.if.qidian.com/argus/newapi/v1/bookcontent/getcontentbatch
    ```

  * **Body**:

    ```json
    {
      "b":1234567,
      "c":"555,222,333,444,666,888",
      "useImei":0
    }
    ```

  * **返回**包含 `DownloadUrl`、`Key`、`Md5`、`Size`, 需后续 GET COS 链接下载 ZIP, 然后解包。
  * 注意: `DownloadUrl` 是加密状态需要使用 `Fock` 的 `unlock` 进行解密

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

* 获取 `book_id = 123456`, 宽度为 `300px` 的 WebP 封面:

  `https://bookcover.yuewen.com/qdbimg/349573/123456/300.webp`

* 获取同一书籍的 JPEG 封面:

  `https://bookcover.yuewen.com/qdbimg/349573/123456/300`

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

<details>
<summary>输出示例如下 (点击展开)</summary>

```bash
{'bookmark': [],
 'chapter': [(-10000,
              '版权信息',
              0,
              None,
              0,
              1619200000000,
              0,
              '100',
              0,
              0,
              0,
              '0.0',
              None,
              None,
              None,
              None,
              0,
              -1,
              0,
              0,
              0,
              None,
              None,
              0,
              0),
             (111111111,
              '第一章 某章节标题',
              0,
              None,
              0,
              1619300000000,
              2345,                 # 内容长度
              '300',
              0,
              1000,
              0,
              '0.0',
              None,
              None,
              None,
              None,
              0,
              1619300000000,
              0,
              0,
              0,
              None,
              None,
              0,
              0)],
 'chapterExtraInfo': [],
 'new_markline': [],
 'sqlite_sequence': [],
 'volume': [('300', '第一节 示例小节标题'), ('301', '第二节 示例小节标题')]}
```
</details>

---

### 3. `{chap_id}.qd` 内容解析

> 声明: 本文为笔者首次尝试进行 Android 应用的逆向分析, 相关方法和思路均基于个人现阶段理解, 主要目的在于探索学习。部分手段可能存在更优或更规范的实现方式, 欢迎指正与交流。

#### 所用工具与依赖

用于分析和提取章节 `.qd` 文件内容, 涉及以下工具与库:

##### 逆向分析工具

- [`jadx`](https://github.com/skylot/jadx/releases): 用于反编译 APK, 提取 Java 层逻辑
- [`Ghidra`](https://github.com/NationalSecurityAgency/ghidra/releases): 静态分析原生库 (如 `.so` 文件)
- [`IDA Pro`](https://hex-rays.com/ida-pro/): 反汇编工具, 用于静态分析本地代码
- [`Android Platform Tools (adb)`](https://developer.android.com/tools/releases/platform-tools): 用于连接调试设备
- [`Frida`](https://github.com/frida/frida): 动态插桩与函数 Hook, 辅助定位或调用加密逻辑

##### Python 依赖

- `frida==16.7.19` 与 `frida-tools==13.7.1`
  - 版本 17.x 及以上目前暂时存在 Java 环境问题, 需要手动处理
  - 相关讨论见: [Java is not defiend](https://github.com/frida/frida/issues/3473)
- `pycryptodome`
  - 加解密算法库

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
- `x86`
- `x86_64`
- `arm64-v8a`

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

- `起点读书`
- `com.qidian.QDReader`

#### 3.3 获取原生日志

为便于后续排查信息, 这里全量导出 `logcat` 日志:

```sh
adb logcat > logs.txt
```

后续配合关键字筛查

#### 3.4 使用 Frida Hook 日志函数

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

<details>
<summary>核心解密函数 `H(long, ChapterItem)` (点击展开)</summary>

```java
public static ChapterContentItem H(long j10, ChapterItem chapterItem) throws Throwable {
    long j11;
    byte[] bArr;
    JSONObject jSONObject;
    String strEncode;
    long jCurrentTimeMillis = System.currentTimeMillis();
    ChapterContentItem chapterContentItem = new ChapterContentItem();
    String strF = F(j10, chapterItem);
    File file = new File(strF);
    d dVarW = W(file, chapterItem);
    if (dVarW == null) {
        h0("OKR_chapter_vip_null", String.valueOf(j10), String.valueOf(chapterItem.ChapterId), String.valueOf(-20076), "chapter data is null", "");
        chapterContentItem.setErrorCode(-20076);
        return chapterContentItem;
    }
    byte[][] bArr2 = dVarW.f18975search;
    if (bArr2 == null || bArr2.length < 2) {
        g0("OKR_chapter_vip_empty", j10, chapterItem, dVarW);
        chapterContentItem.setErrorCode(-20076);
        return chapterContentItem;
    }
    byte[] bArr3 = bArr2[0];
    byte[] bArr4 = bArr2[1];
    byte[] bArr5 = bArr2[2];
    byte[] bArr6 = bArr2[3];
    byte[] bArr7 = bArr2[4];
    long J = J(bArr3);
    if (J != 0 && J < vi.judian.e().f()) {
        chapterContentItem.setErrorCode(-20067);
        return chapterContentItem;
    }
    byte[] bArrX = x(bArr4, j10, chapterItem.ChapterId);
    if (bArrX == null) {
        if (file.exists()) {
            String strM = com.qidian.common.lib.util.m.m(file);
            strEncode = !TextUtils.isEmpty(strM) ? URLEncoder.encode(strM) : "";
        } else {
            strEncode = "file_not_found_" + strF;
        }
        d5.cihai.p(new AutoTrackerItem.Builder().setPn("OKR_chapter_vip_error").setDt("1103").setPdid(String.valueOf(j10)).setDid(String.valueOf(chapterItem.ChapterId)).setPdt(String.valueOf(strEncode.length())).setEx1(String.valueOf(QDUserManager.getInstance().k())).setEx2(QDUserManager.getInstance().s()).setEx3(QDUserManager.getInstance().t()).setEx4(we.d.I().d()).setEx5(strEncode).setAbtest("true").setKeyword("v2").buildCol());
        chapterContentItem.setErrorCode(-20068);
        return chapterContentItem;
    }
    String strW = w(bArrX);
    JSONObject jSONObjectQ = Q(strW);
    if (jSONObjectQ != null) {
        strW = jSONObjectQ.optString("content");
        int iOptInt = jSONObjectQ.optInt("type");
        int iOptInt2 = jSONObjectQ.optInt("code");
        String strOptString = jSONObjectQ.optString("msg");
        j11 = jCurrentTimeMillis;
        bArr = bArr7;
        e0.f18516search.a(j10, chapterItem.ChapterId, new e0.search(jSONObjectQ.optLong("idExpire"), jSONObjectQ.optInt("wt")));
        if (iOptInt2 != 0) {
            chapterContentItem.setErrorCode(iOptInt2);
            chapterContentItem.setErrorMessage(strOptString);
            return chapterContentItem;
        }
        if (TextUtils.isEmpty(strW)) {
            chapterContentItem.setErrorCode(-20088);
            return chapterContentItem;
        }
        String str = j10 + "_" + chapterItem.ChapterId;
        if (iOptInt == LockType.FOCK.getType()) {
            String strValueOf = String.valueOf(chapterItem.ChapterId);
            FockUtil fockUtil = FockUtil.INSTANCE;
            boolean zIsHasKey = fockUtil.isHasKey();
            Fock.FockResult fockResultUnlock = fockUtil.unlock(strW, strValueOf, str);
            if (fockResultUnlock.status == Fock.FockResult.STATUS_EMPTY_USER_KEY) {
                Fock.setup(we.d.X());
                fockResultUnlock = fockUtil.unlock(strW, strValueOf, str);
            }
            Fock.FockResult fockResult = fockResultUnlock;
            Logger.e("FockUtil: chapter_id:" + chapterItem.ChapterId + ",result:" + fockResult.status);
            if (fockResult.status != 0) {
                fockUtil.report(j10, chapterItem, fockResult, zIsHasKey);
            }
            int i10 = fockResult.status;
            if (i10 != 0) {
                if (i10 == -2) {
                    chapterContentItem.setErrorCode(-20079);
                    d5.cihai.p(new AutoTrackerItem.Builder().setPn("OKR_LoadChapterFailed_qimeiChanged").setEx1(String.valueOf(j10)).setEx2(String.valueOf(chapterItem.ChapterId)).buildCol());
                    return chapterContentItem;
                }
                if (i10 == Fock.FockResult.STATUS_EMPTY_USER_KEY) {
                    chapterContentItem.setErrorCode(-20082);
                    return chapterContentItem;
                }
                chapterContentItem.setErrorCode(-20080);
                return chapterContentItem;
            }
            strW = new String(fockResult.data, StandardCharsets.UTF_8);
        } else if (iOptInt != LockType.DEFAULT.getType()) {
            chapterContentItem.setErrorCode(-20081);
            return chapterContentItem;
        }
    } else {
        j11 = jCurrentTimeMillis;
        bArr = bArr7;
    }
    String str2 = strW;
    ArrayList<BlockInfo> arrayList = null;
    if (bArr5 != null) {
        try {
            jSONObject = new JSONObject(w(bArr5));
        } catch (Exception e10) {
            e10.printStackTrace();
        }
    } else {
        jSONObject = null;
    }
    chapterContentItem.setChapterContent(str2);
    chapterContentItem.setOriginalChapterContent(str2);
    chapterContentItem.setAuthorContent(jSONObject);
    if (bArr != null) {
        try {
            String strW2 = w(bArr);
            if (strW2 != null) {
                arrayList = (ArrayList) new Gson().j(strW2, new b().getType());
            }
        } catch (Exception e11) {
            e11.printStackTrace();
        }
        chapterContentItem.setBlockInfos(arrayList);
    }
    if (we.d.k0()) {
        StringBuffer stringBuffer = new StringBuffer();
        stringBuffer.append("Vip章节 内容读取 chapterId:");
        stringBuffer.append(chapterItem.ChapterId);
        stringBuffer.append(" chapterName:");
        stringBuffer.append(chapterItem.ChapterName);
        stringBuffer.append(" 读取, 耗时:");
        stringBuffer.append(System.currentTimeMillis() - j11);
        stringBuffer.append("毫秒");
        Logger.d("QDReader", stringBuffer.toString());
    }
    return chapterContentItem;
}
```
</details>

解密流程可概括为:

1. **文件分段读取**: 使用 `W(file, ...)` 按小端格式读取 5 段数据

   ```
   [len0][part0][len1][part1]...[len4][part4]
   ```

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

<details>
<summary>Java_a_b_b 实现片段 (点击展开)</summary>

```c
jobject __fastcall Java_a_b_b(
        JNIEnv *env,
        jobject clazz,
        jlong bookIdLong,
        jlong chapterIdLong,
        jbyteArray dataArray,
        jlong userIdLong,
        jstring imei)
{
  char *bookIdCStr; // x19
  char *chapterIdCStr; // x21
  const char *userIdCStr; // x23
  _OWORD *secBuffer1; // x27
  _OWORD *secBuffer2; // x28
  _OWORD *sha2KeyBufArea; // x0
  const char *sha2KeyCStr; // x25
  jclass clsAB_1; // x0
  void *clsAB_ref1; // x26
  const char *imeiCStr; // x24
  char *ptrAfterFirstConcat; // x24
  char *ptrAfterChapterConcat; // x0
  struct _jmethodID *mid_s; // x24
  jobject jSha1Key1; // x26
  const char *sha1Key1CStr; // x24
  jstring jSec2Str; // x24
  struct _jmethodID *mid_m; // x26
  jstring jUserIdJStr; // x0
  void *clsAB_ref2; // x1
  jobject jSha1Key2; // x22
  const char *sha1Key2CStr; // x24
  jstring jSha2KeyJStr; // x26
  struct _jmethodID *mid_d; // x22
  jobject intermediateData1; // x27
  jobject finalData; // x22
  jstring jSec1Str; // [xsp+0h] [xbp-30h]
  jstring jSha1Key1FinalStr; // [xsp+0h] [xbp-30h]
  const char *imeiCStrRef; // [xsp+8h] [xbp-28h]
  jclass clsAB_3; // [xsp+10h] [xbp-20h]
  jclass clsAB_2; // [xsp+18h] [xbp-18h]
  void *jUserIdJStrRef; // [xsp+18h] [xbp-18h]

  bookIdCStr = (char *)malloc(0x40u);
  *(_OWORD *)bookIdCStr = 0u;
  *((_OWORD *)bookIdCStr + 1) = 0u;
  *((_OWORD *)bookIdCStr + 2) = 0u;
  *((_OWORD *)bookIdCStr + 3) = 0u;
  sub_1230((__int64)bookIdCStr, 64LL, (__int64)"%lld", bookIdLong);

  chapterIdCStr = (char *)malloc(0x40u);
  *(_OWORD *)chapterIdCStr = 0u;
  *((_OWORD *)chapterIdCStr + 1) = 0u;
  *((_OWORD *)chapterIdCStr + 2) = 0u;
  *((_OWORD *)chapterIdCStr + 3) = 0u;
  sub_1230((__int64)chapterIdCStr, 64LL, (__int64)"%lld", chapterIdLong);

  userIdCStr = (const char *)malloc(0x40u);
  *(_OWORD *)userIdCStr = 0u;
  *((_OWORD *)userIdCStr + 1) = 0u;
  *((_OWORD *)userIdCStr + 2) = 0u;
  *((_OWORD *)userIdCStr + 3) = 0u;
  sub_1230((__int64)userIdCStr, 64LL, (__int64)"%lld", userIdLong);

  secBuffer1 = malloc(0xFFu);
  *secBuffer1 = 0u;
  secBuffer1[1] = 0u;
  secBuffer1[2] = 0u;
  secBuffer1[3] = 0u;
  secBuffer1[4] = 0u;
  secBuffer1[5] = 0u;
  secBuffer1[6] = 0u;
  secBuffer1[7] = 0u;
  secBuffer1[8] = 0u;
  secBuffer1[9] = 0u;
  secBuffer1[10] = 0u;
  secBuffer1[11] = 0u;
  secBuffer1[12] = 0u;
  secBuffer1[13] = 0u;
  secBuffer1[14] = 0u;
  *(_OWORD *)((char *)secBuffer1 + 239) = 0u;

  secBuffer2 = malloc(0xFFu);
  *secBuffer2 = 0u;
  secBuffer2[1] = 0u;
  secBuffer2[2] = 0u;
  secBuffer2[3] = 0u;
  secBuffer2[4] = 0u;
  secBuffer2[5] = 0u;
  secBuffer2[6] = 0u;
  secBuffer2[7] = 0u;
  secBuffer2[8] = 0u;
  secBuffer2[9] = 0u;
  secBuffer2[10] = 0u;
  secBuffer2[11] = 0u;
  secBuffer2[12] = 0u;
  secBuffer2[13] = 0u;
  secBuffer2[14] = 0u;
  *(_OWORD *)((char *)secBuffer2 + 239) = 0u;

  sha2KeyBufArea = malloc(0xFFu);
  *sha2KeyBufArea = 0u;
  sha2KeyBufArea[1] = 0u;
  sha2KeyBufArea[2] = 0u;
  sha2KeyBufArea[3] = 0u;
  sha2KeyBufArea[4] = 0u;
  sha2KeyBufArea[5] = 0u;
  sha2KeyBufArea[6] = 0u;
  sha2KeyBufArea[7] = 0u;
  sha2KeyBufArea[8] = 0u;
  sha2KeyBufArea[9] = 0u;
  sha2KeyBufArea[10] = 0u;
  sha2KeyBufArea[11] = 0u;
  sha2KeyBufArea[12] = 0u;
  sha2KeyBufArea[13] = 0u;
  sha2KeyBufArea[14] = 0u;
  *(_OWORD *)((char *)sha2KeyBufArea + 239) = 0u;

  sha2KeyCStr = (const char *)sha2KeyBufArea;

  clsAB_1 = (*env)->FindClass(env, "a/b");
  if ( !clsAB_1 )
    return 0LL;
  clsAB_ref1 = clsAB_1;

  clsAB_2 = (*env)->FindClass(env, "a/b");
  if ( !clsAB_2 )
    return 0LL;

  clsAB_3 = (*env)->FindClass(env, "a/b");
  if ( !clsAB_3 )
    return 0LL;

  __android_log_print(3, "QDReader_Jni", "JNI:0");
  imeiCStr = (*env)->GetStringUTFChars(env, imei, 0LL);
  __android_log_print(
    3,
    "QDReader_Jni",
    "bookid: %s,chapterid: %s,userid: %s,imei: %s",
    bookIdCStr,
    chapterIdCStr,
    userIdCStr,
    imeiCStr);
  __android_log_print(3, "QDReader_Jni", "JNI:1");

  __strcpy_chk(secBuffer1, userIdCStr, 255LL);
  imeiCStrRef = imeiCStr;
  ptrAfterFirstConcat = (char *)__strcat_chk(secBuffer1, imeiCStr, 255LL);
  ptrAfterChapterConcat = strcat(ptrAfterFirstConcat, chapterIdCStr);
  strcpy(&ptrAfterFirstConcat[strlen(ptrAfterChapterConcat)], "2EEE1433A152E84B3756301D8FA3E69A");
  __android_log_print(3, "QDReader_Jni", "JNI:2");

  jSec1Str = (*env)->NewStringUTF(env, secBuffer1);
  __android_log_print(3, "QDReader_Jni", "JNI:3");

  mid_s = (*env)->GetStaticMethodID(env, clsAB_ref1, "s", "(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;");
  __android_log_print(3, "QDReader_Jni", "JNI:4");
  if ( !mid_s )
    return 0LL;
  __android_log_print(3, "QDReader_Jni", "sha1id:%d", mid_s);
  __android_log_print(3, "QDReader_Jni", "JNI:5");

  jSha1Key1 = (*env)->CallStaticObjectMethod(env, clsAB_ref1, mid_s, imei, jSec1Str);
  (*env)->ReleaseStringUTFChars(env, jSec1Str, (const char *)secBuffer1);
  __android_log_print(3, "QDReader_Jni", "JNI:6");

  sha1Key1CStr = (*env)->GetStringUTFChars(env, jSha1Key1, 0LL);
  __android_log_print(3, "QDReader_Jni", "sha1key1 = %s", sha1Key1CStr);
  __android_log_print(3, "QDReader_Jni", "JNI:7");

  if ( strlen(sha1Key1CStr) >= 0x18uLL )
  {
    memset(gShaKeyBuf, 0, sizeof(gShaKeyBuf));
    strncpy(gShaKeyBuf, sha1Key1CStr, 0x18u);
  }
  __android_log_print(3, "QDReader_Jni", "JNI:8 sha1key2:%s sha1key1:%s", gShaKeyBuf, sha1Key1CStr);
  (*env)->ReleaseStringUTFChars(env, jSha1Key1, sha1Key1CStr);

  jSha1Key1FinalStr = (*env)->NewStringUTF(env, gShaKeyBuf);
  __android_log_print(3, "QDReader_Jni", "JNI:9");

  __strcpy_chk(secBuffer2, gShaKeyBuf, 255LL);
  __strcat_chk(secBuffer2, imeiCStrRef, 255LL);
  __android_log_print(3, "QDReader_Jni", "JNI:10");

  jSec2Str = (*env)->NewStringUTF(env, secBuffer2);
  __android_log_print(3, "QDReader_Jni", "JNI:11");

  mid_m = (*env)->GetStaticMethodID(env, clsAB_2, "m", "(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;");
  __android_log_print(3, "QDReader_Jni", "JNI:12");
  if ( !mid_m )
    return 0LL;
  __android_log_print(3, "QDReader_Jni", "JNI:13");

  jUserIdJStr = (*env)->NewStringUTF(env, userIdCStr);
  clsAB_ref2 = clsAB_2;
  jUserIdJStrRef = jUserIdJStr;
  jSha1Key2 = (*env)->CallStaticObjectMethod(env, clsAB_ref2, mid_m);
  (*env)->ReleaseStringUTFChars(env, jSec2Str, (const char *)secBuffer2);
  __android_log_print(3, "QDReader_Jni", "JNI:14");

  sha1Key2CStr = (*env)->GetStringUTFChars(env, jSha1Key2, 0LL);
  __android_log_print(3, "QDReader_Jni", "JNI:15");

  if ( strlen(sha1Key2CStr) < 0x19uLL )
  {
    __strcpy_chk(sha2KeyCStr, sha1Key2CStr, 255LL);
  }
  else
  {
    sha2KeyCStr = gShaKeyBuf;
    memset(gShaKeyBuf, 0, sizeof(gShaKeyBuf));
    strncpy(gShaKeyBuf, sha1Key2CStr, 0x18u);
  }
  (*env)->ReleaseStringUTFChars(env, jSha1Key2, sha1Key2CStr);
  __android_log_print(3, "QDReader_Jni", "JNI:16");

  jSha2KeyJStr = (*env)->NewStringUTF(env, sha2KeyCStr);
  __android_log_print(3, "QDReader_Jni", "JNI:17");

  mid_d = (*env)->GetStaticMethodID(env, clsAB_3, "d", "([BLjava/lang/String;)[B");
  __android_log_print(3, "QDReader_Jni", "JNI:18");
  if ( !mid_d )
    return 0LL;
  __android_log_print(3, "QDReader_Jni", "JNI:19");

  intermediateData1 = (*env)->CallStaticObjectMethod(env, clsAB_3, mid_d, dataArray, jSha2KeyJStr);
  __android_log_print(3, "QDReader_Jni", "JNI:20");

  finalData = (*env)->CallStaticObjectMethod(env, clsAB_3, mid_d, intermediateData1, jSha1Key1FinalStr);
  __android_log_print(3, "QDReader_Jni", "JNI:21");

  (*env)->ReleaseStringUTFChars(env, imei, imeiCStrRef);
  __android_log_print(3, "QDReader_Jni", "JNI:22 %s", gShaKeyBuf);
  __android_log_print(3, "QDReader_Jni", "JNI:23");

  (*env)->ReleaseStringUTFChars(env, jSha2KeyJStr, sha2KeyCStr);
  __android_log_print(3, "QDReader_Jni", "JNI:24");

  (*env)->ReleaseStringUTFChars(env, jUserIdJStrRef, userIdCStr);
  __android_log_print(3, "QDReader_Jni", "JNI:25");

  free(bookIdCStr);
  __android_log_print(3, "QDReader_Jni", "JNI:26");

  free(chapterIdCStr);
  __android_log_print(3, "QDReader_Jni", "JNI:27");

  return finalData;
}
```

`package a`:

```java
package a;

import android.content.Context;
import android.util.Base64;
import bf.cihai;
import com.qidian.QDReader.autotracker.bean.AutoTrackerItem;
import com.qidian.common.lib.Logger;
import com.qidian.common.lib.util.q0;
import java.security.NoSuchAlgorithmException;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

public class b {
    private static final String CHARSET_ASCII = "ascii";
    private static final String MAC_SHA1_NAME = "HmacSHA1";

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

    public static native void c(Context context);

    public static byte[] d(byte[] bArr, String str) {
        try {
            return cihai.search(bArr, str);
        } catch (Exception e10) {
            Logger.exception(e10);
            return null;
        }
    }

    private static String encryptToSHA1(String str, String str2) throws Exception {
        SecretKeySpec secretKeySpec = new SecretKeySpec(str.getBytes(CHARSET_ASCII), MAC_SHA1_NAME);
        Mac mac = Mac.getInstance(MAC_SHA1_NAME);
        mac.init(secretKeySpec);
        return new String(Base64.encode(mac.doFinal(str2.getBytes(CHARSET_ASCII)), 0));
    }

    public static String m(String str, String str2) {
        String str3;
        try {
            str3 = bf.a.judian(str, str2);
        } catch (NoSuchAlgorithmException e10) {
            e = e10;
            str3 = null;
        }
        try {
            if (str3.length() != 24) {
                d5.cihai.p(new AutoTrackerItem.Builder().setPn("OKR_b_m").setEx1(String.valueOf(str3.length())).setEx2(str + "/" + str2 + "/" + str3).buildCol());
            }
        } catch (NoSuchAlgorithmException e11) {
            e = e11;
            Logger.exception(e);
            return str3;
        }
        return str3;
    }

    public static String s(String str, String str2) {
        String str3;
        try {
            str3 = encryptToSHA1(str, str2);
            try {
                if (str3.length() >= 24) {
                    return str3;
                }
                d5.cihai.p(new AutoTrackerItem.Builder().setPn("OKR_b_s").setEx1(String.valueOf(str3.length())).setEx2(str + "/" + str2 + "/" + str3).buildCol());
                return q0.m(str3, 24, (char) 0);
            } catch (Exception e10) {
                e = e10;
                Logger.exception(e);
                return str3;
            }
        } catch (Exception e11) {
            e = e11;
            str3 = null;
        }
    }
}
```

`q0.m`:

```java
public static String m(String str, int i10, char c10) {
    StringBuilder sb = new StringBuilder();
    sb.append(str);
    int length = i10 - str.length();
    for (int i11 = 0; i11 < length; i11++) {
        sb.append(c10);
    }
    return sb.toString();
}
```

`package bf`:

```java
package bf;

import com.qidian.QDReader.qmethod.pandoraex.monitor.c;
import com.qidian.common.lib.Logger;
import java.nio.charset.StandardCharsets;
import javax.crypto.Cipher;
import javax.crypto.spec.IvParameterSpec;
import javax.crypto.spec.SecretKeySpec;

public class cihai {

    /* renamed from: search, reason: collision with root package name */
    private static final String f1806search = "bf.cihai";

    public static String cihai(String str, String str2) throws Exception {
        IvParameterSpec ivParameterSpec = new IvParameterSpec(new byte[8]);
        byte[] bytes = str2.getBytes("UTF-8");
        if (bytes.length == 16) {
            byte[] bArr = new byte[24];
            System.arraycopy(bytes, 0, bArr, 0, 16);
            System.arraycopy(bytes, 0, bArr, 16, 8);
            bytes = bArr;
        }
        SecretKeySpec secretKeySpec = new SecretKeySpec(bytes, "DESede");
        Cipher cipher = Cipher.getInstance("DESede/CBC/PKCS5Padding");
        if (cipher == null) {
            return "";
        }
        cipher.init(1, secretKeySpec, ivParameterSpec);
        return search.judian(c.search(cipher, str.getBytes()));
    }

    public static String judian(byte[] bArr, String str) throws Exception {
        IvParameterSpec ivParameterSpec = new IvParameterSpec("01234567".getBytes(StandardCharsets.UTF_8));
        byte[] bytes = str.getBytes("UTF-8");
        if (bytes.length == 16) {
            byte[] bArr2 = new byte[24];
            System.arraycopy(bytes, 0, bArr2, 0, 16);
            System.arraycopy(bytes, 0, bArr2, 16, 8);
            bytes = bArr2;
        }
        SecretKeySpec secretKeySpec = new SecretKeySpec(bytes, "DESede");
        Cipher cipher = Cipher.getInstance("DESede/CBC/PKCS5Padding");
        if (cipher == null) {
            return "";
        }
        cipher.init(1, secretKeySpec, ivParameterSpec);
        return search.judian(c.search(cipher, bArr));
    }

    public static byte[] search(byte[] bArr, String str) throws Exception {
        if (bArr != null && str != null) {
            IvParameterSpec ivParameterSpec = new IvParameterSpec(new byte[8]);
            byte[] bytes = str.getBytes("UTF-8");
            if (bytes != null && bytes.length >= 1) {
                if (bytes.length == 16) {
                    byte[] bArr2 = new byte[24];
                    System.arraycopy(bytes, 0, bArr2, 0, 16);
                    System.arraycopy(bytes, 0, bArr2, 16, 8);
                    bytes = bArr2;
                }
                Cipher cipher = Cipher.getInstance("DESede/CBC/PKCS5Padding");
                if (cipher == null) {
                    Logger.e(f1806search, "cipher is null");
                    return null;
                }
                cipher.init(2, new SecretKeySpec(bytes, "DESede"), ivParameterSpec);
                try {
                    return c.search(cipher, bArr);
                } catch (Exception e10) {
                    e10.printStackTrace();
                    int length = bArr.length;
                    Logger.e(f1806search, "decryptDES失败：" + str + "," + length);
                    return null;
                }
            }
            Logger.e(f1806search, "keyBytes is illegal");
        }
        return null;
    }
}
```

```java
package bf;

import com.tencent.qcloud.core.util.IOUtils;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;

public class a {

    /* renamed from: search, reason: collision with root package name */
    private static char[] f1805search = {'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '+', IOUtils.DIR_SEPARATOR_UNIX};

    public static String a(String str) throws Exception {
        byte[] digest = MessageDigest.getInstance("MD5").digest(str.getBytes("UTF-8"));
        StringBuilder sb = new StringBuilder(digest.length * 2);
        for (byte b10 : digest) {
            int i10 = b10 & 255;
            if (i10 < 16) {
                sb.append("0");
            }
            sb.append(Integer.toHexString(i10));
        }
        return sb.toString();
    }

    private static byte[] b(byte[] bArr) throws NoSuchAlgorithmException {
        MessageDigest messageDigest = MessageDigest.getInstance("MD5");
        messageDigest.update(bArr);
        return messageDigest.digest();
    }

    private static byte[] cihai(byte[] bArr, byte[] bArr2) throws NoSuchAlgorithmException {
        byte[] bArr3 = new byte[64];
        byte[] bArr4 = new byte[64];
        for (int i10 = 0; i10 < 64; i10++) {
            bArr3[i10] = 54;
            bArr4[i10] = 92;
        }
        byte[] bArr5 = new byte[64];
        if (bArr.length > 64) {
            bArr = b(bArr);
        }
        for (int i11 = 0; i11 < bArr.length; i11++) {
            bArr5[i11] = bArr[i11];
        }
        if (bArr.length < 64) {
            for (int length = bArr.length; length < 64; length++) {
                bArr5[length] = 0;
            }
        }
        byte[] bArr6 = new byte[64];
        for (int i12 = 0; i12 < 64; i12++) {
            bArr6[i12] = (byte) (bArr5[i12] ^ bArr3[i12]);
        }
        byte[] bArr7 = new byte[bArr2.length + 64];
        for (int i13 = 0; i13 < 64; i13++) {
            bArr7[i13] = bArr6[i13];
        }
        for (int i14 = 0; i14 < bArr2.length; i14++) {
            bArr7[i14 + 64] = bArr2[i14];
        }
        byte[] b10 = b(bArr7);
        byte[] bArr8 = new byte[64];
        for (int i15 = 0; i15 < 64; i15++) {
            bArr8[i15] = (byte) (bArr5[i15] ^ bArr4[i15]);
        }
        byte[] bArr9 = new byte[b10.length + 64];
        for (int i16 = 0; i16 < 64; i16++) {
            bArr9[i16] = bArr8[i16];
        }
        for (int i17 = 0; i17 < b10.length; i17++) {
            bArr9[i17 + 64] = b10[i17];
        }
        return b(bArr9);
    }

    public static String judian(String str, String str2) throws NoSuchAlgorithmException {
        return search(cihai(str.getBytes(), str2.getBytes()));
    }

    public static String search(byte[] bArr) {
        StringBuffer stringBuffer = new StringBuffer();
        int length = bArr.length;
        int i10 = 0;
        while (true) {
            if (i10 >= length) {
                break;
            }
            int i11 = i10 + 1;
            int i12 = bArr[i10] & 255;
            if (i11 == length) {
                stringBuffer.append(f1805search[i12 >>> 2]);
                stringBuffer.append(f1805search[(i12 & 3) << 4]);
                stringBuffer.append("==");
                break;
            }
            int i13 = i11 + 1;
            int i14 = bArr[i11] & 255;
            if (i13 == length) {
                stringBuffer.append(f1805search[i12 >>> 2]);
                stringBuffer.append(f1805search[((i12 & 3) << 4) | ((i14 & 240) >>> 4)]);
                stringBuffer.append(f1805search[(i14 & 15) << 2]);
                stringBuffer.append("=");
                break;
            }
            int i15 = i13 + 1;
            int i16 = bArr[i13] & 255;
            stringBuffer.append(f1805search[i12 >>> 2]);
            stringBuffer.append(f1805search[((i12 & 3) << 4) | ((i14 & 240) >>> 4)]);
            stringBuffer.append(f1805search[((i14 & 15) << 2) | ((i16 & 192) >>> 6)]);
            stringBuffer.append(f1805search[i16 & 63]);
            i10 = i15;
        }
        return stringBuffer.toString();
    }
}
```

`package com.qidian.QDReader.qmethod.pandoraex.monitor`:

```java
package com.qidian.QDReader.qmethod.pandoraex.monitor;

import j$.util.concurrent.ConcurrentHashMap;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import javax.crypto.BadPaddingException;
import javax.crypto.Cipher;
import javax.crypto.IllegalBlockSizeException;

public class c {

    /* renamed from: search, reason: collision with root package name */
    private static ConcurrentHashMap<String, byte[]> f26010search = new ConcurrentHashMap<>();

    public static void a(byte[] bArr, byte[] bArr2) {
        f26010search.put(judian(bArr), bArr2);
    }

    public static byte[] cihai(byte[] bArr) {
        byte[] bArr2 = null;
        while (bArr != null) {
            bArr = f26010search.get(judian(bArr));
            if (bArr != null) {
                bArr2 = bArr;
            }
        }
        return bArr2;
    }

    public static String judian(byte[] bArr) {
        try {
            byte[] digest = MessageDigest.getInstance("MD5").digest(bArr);
            StringBuilder sb = new StringBuilder();
            for (byte b10 : digest) {
                sb.append(String.format("%02x", Byte.valueOf(b10)));
            }
            return sb.toString();
        } catch (NoSuchAlgorithmException e10) {
            throw new RuntimeException("MD5 algorithm is not available", e10);
        }
    }

    public static byte[] search(Cipher cipher, byte[] bArr) throws IllegalBlockSizeException, BadPaddingException {
        byte[] doFinal = cipher.doFinal(bArr);
        if (com.qidian.QDReader.qmethod.pandoraex.core.ext.netcap.g.a()) {
            a(doFinal, bArr);
        }
        return doFinal;
    }
}
```

</details>

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

> 注意: 执行此 Hook 前, 需先在手机端启动 App 并打开任意一个 VIP 章节, 以确保目标类和方法 (如 `Fock` 等) 已加载并初始化, 否则 Hook 将无法生效。

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

---

##### 3.5.4 批量解密与导出实现

基于前述各模块, 可整合为一个完整的批量解密脚本。

该脚本支持对指定目录下的 `.qd` 文件进行批量处理, 并将解析结果导出为对应的 `.json` 文件, 便于后续分析与使用。

**主要功能**

* **批量扫描**: 遍历指定目录下的所有 `.qd` 文件
* **逐一解密**: 依次调用 `decrypt()`, 对每个章节文件进行双重解密与 Frida 解锁
* **结果导出**: 将每个章节的解密内容保存为对应的 `{chapter_id}.json`

**运行前准备**

1. **配置解密参数**

   * `USER_ID`、`BOOK_ID`、`IMEI`: 作为解密过程中 HMAC 和 3DES 的密钥输入
   * `DEVICE_ADDRESS`: Frida 远程调试端口或设备标识
2. **修改连接方式**

   * 默认使用:

     ```python
     device = frida.get_device_manager().add_remote_device(f"127.0.0.1:{ADB_FORWARD_PORT}")
     ```
   * 可替换为 IP 直连或 USB:

     ```python
     device = frida.get_device("<your.device.ip.address>")
     ```
3. **命令行参数**
   脚本支持通过命令行覆盖上述全局变量:

   ```bash
   python qd_decrypt.py --user-id 123456 --book-id 654321 --imei 8675309
   ```

**默认目录结构**

* **输入目录**: `./data/{user_id}/{book_id}/`, 存放待解密的 `.qd` 文件
* **输出目录**: `./output/{user_id}/{book_id}/`, 生成对应的 `.json` 文件

<details>
<summary>`qd_decrypt.py` (点击展开)</summary>

```python
import argparse
import hashlib
import hmac
import json
import sys
from base64 import b64encode
from io import BytesIO
from pathlib import Path
from typing import Any

import frida
from Crypto.Cipher import DES3
from Crypto.Util.Padding import unpad
from tqdm import tqdm


# --------------------------------------------------
# Static constants
# --------------------------------------------------
TARGET_APP     = "起点读书"
HOOK_JS_FILE   = "hook_fock.js"
CONFIG_PATH    = Path.cwd() / "config.json"
_SECRET_SUFFIX  = "2EEE1433A152E84B3756301D8FA3E69A"

# Globals filled in at runtime
ADB_FORWARD_PORT = "12345"
DEVICE_ADDRESS: str = ""
USER_ID: str = ""
BOOK_ID: str = ""
IMEI: str = ""
DATA_DIR: Path
OUT_DIR: Path


# --------------------------------------------------
# Load configuration from config.json
# --------------------------------------------------
def load_config() -> None:
    global DEVICE_ADDRESS, USER_ID, BOOK_ID, IMEI
    try:
        raw = CONFIG_PATH.read_text(encoding="utf-8")
        cfg = json.loads(raw)
    except Exception:
        cfg = {}

    DEVICE_ADDRESS = DEVICE_ADDRESS or cfg.get("adb_port") or ""
    USER_ID        = USER_ID or cfg.get("user_id") or ""
    BOOK_ID        = BOOK_ID or cfg.get("book_id") or ""
    IMEI           = IMEI or cfg.get("imei") or ""


# --------------------------------------------------
# Argument Parsing
# --------------------------------------------------
def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments for user/date/book/imei.
    """
    p = argparse.ArgumentParser(
        description="Decrypt Qidian .qd files into JSON chapters"
    )
    p.add_argument("-u", "--user-id",
                        default=USER_ID,
                        help="USER ID (default: %(default)s)")
    p.add_argument("-b", "--book-id",
                        default=BOOK_ID,
                        help="Book ID (default: %(default)s)")
    p.add_argument("-i", "--imei",
                        default=IMEI,
                        help="Device IMEI (default: %(default)s)")
    return p.parse_args()


def update_globals(args) -> None:
    """
    Update globals from parsed args, rebuild DATA_DIR and OUT_DIR,
    and ensure OUT_DIR exists.
    """
    global USER_ID, BOOK_ID, IMEI, DATA_DIR, OUT_DIR

    USER_ID  = args.user_id
    BOOK_ID  = args.book_id
    IMEI     = args.imei

    DATA_DIR = Path.cwd() / "data"   / USER_ID / BOOK_ID
    OUT_DIR  = Path.cwd() / "output" / USER_ID / BOOK_ID
    OUT_DIR.mkdir(parents=True, exist_ok=True)


def check_globals() -> bool:
    """
    Ensure that DEVICE_ADDRESS, USER_ID, BOOK_ID, IMEI
    are all non-empty; report and return False otherwise.
    """
    missing = []
    for name in ("DEVICE_ADDRESS", "USER_ID", "BOOK_ID", "IMEI"):
        if not globals().get(name):
            missing.append(name)
    if missing:
        print(f"[ERROR] Missing required parameters: {', '.join(missing)}", file=sys.stderr)
        return False
    return True


# --------------------------------------------------
# Crypto Helpers
# --------------------------------------------------
def sha1_hmac(key: str, data: str) -> str:
    digest = hmac.new(key.encode(), data.encode(), hashlib.sha1).digest()
    return b64encode(digest).decode()[:24]


def md5_hmac(key: str, data: str) -> str:
    digest = hmac.new(key.encode(), data.encode(), hashlib.md5).digest()
    return b64encode(digest).decode()[:24]


def des3_decrypt(data: bytes, secret: str) -> bytes:
    """3DES/CBC decrypt with zero IV and PKCS#7 unpad."""
    cipher = DES3.new(secret.encode(), DES3.MODE_CBC, b'\x00' * 8)
    decrypted = cipher.decrypt(data)
    return unpad(decrypted, block_size=8)


# --------------------------------------------------
# Decryption Logic
# --------------------------------------------------
def decrypt_content(
    cid: str,
    chunk1: bytes,
    uid: str,
    imei: str,
) -> str:
    """
    Double-decrypt chunk1 with keys derived via HMACs,
    strip padding/extras, return UTF-8 string.
    """
    sec1 = sha1_hmac(imei, uid + imei + cid + _SECRET_SUFFIX)
    sec2 = md5_hmac(uid, sec1 + imei)

    step1 = des3_decrypt(chunk1, sec2)
    step2 = des3_decrypt(step1, sec1)
    return step2.decode("utf-8", errors="ignore")


def decrypt(
    path: Path,
    book_id: str,
    uid: str,
    imei: str,
    script
) -> dict[str, Any]:
    """
    Read a .qd file (five chunks) and decrypt chunk1 (and
    potentially unlock further with Frida for content_type==1).
    """
    cid = path.stem
    with path.open('rb') as f:
        buf = BytesIO(f.read())

    def read_chunk() -> bytes:
        raw = buf.read(4)
        if len(raw) < 4:
            raise IOError("Incomplete file, cannot read length")
        length = int.from_bytes(raw, byteorder='little')
        return buf.read(length)

    chunk0 = read_chunk()
    chunk1 = read_chunk()
    chunk2 = read_chunk()
    chunk3 = read_chunk()
    chunk4 = read_chunk()

    text_1 = decrypt_content(cid, chunk1, uid, imei)
    try:
        data_obj = json.loads(text_1 or "{}")
    except Exception:
        data_obj = {}

    content        = data_obj.get("content", "") or data_obj.get("Content", "")
    content_type   = data_obj.get("type", 0)
    block_infos    = data_obj.get("Blocks", [])
    author_content = data_obj.get("AuthorComments", {})
    resources      = data_obj.get("Resources", [])

    # for type==1, use Frida unlock, then re-parse chunk2/4:
    if content_type == 1:
        try:
            raw = script.exports_sync.unlock(
                content, cid, f"{book_id}_{cid}"
            )
            # decoded = json.loads(raw)
            content = raw.get("content", "")
        except Exception:
            pass

        try:
            author_content = json.loads(
                chunk2.decode('utf-8', errors='ignore')
            )
        except Exception:
            author_content = {}

        try:
            block_infos = json.loads(
                chunk4.decode('utf-8', errors='ignore')
            )
        except Exception:
            block_infos = []

    return {
        "content":         content,
        "type":            content_type,
        "author_comments": author_content,
        "blocks":          block_infos,
        "resources":       resources,
    }


# --------------------------------------------------
# Main
# --------------------------------------------------
def main() -> None:
    load_config()
    args = parse_args()
    update_globals(args)
    if not check_globals():
        sys.exit(1)

    # device  = frida.get_device(DEVICE_ADDRESS)
    device = frida.get_device_manager().add_remote_device(f"127.0.0.1:{ADB_FORWARD_PORT}")
    session = device.attach(TARGET_APP)
    with open(HOOK_JS_FILE, "r", encoding="utf-8") as f:
        jscode = f.read()
    script = session.create_script(jscode)
    script.load()

    print("[*] Script loaded. Starting decryption...")

    files = list(DATA_DIR.glob("*.qd"))

    for file_path in tqdm(files, desc="Decrypting files", unit="file"):
        out_path = OUT_DIR / f"{file_path.stem}.json"
        try:
            obj = decrypt(file_path, BOOK_ID, USER_ID, IMEI, script)
        except Exception as e:
            obj = {"error": str(e)}
        with out_path.open('w', encoding='utf-8') as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
```
</details>

##### 3.5.5 解密数据导出为 HTML

本脚本基于 `qd_decrypt.py` 的 JSON 输出, 自动生成带目录和章节导航的静态 HTML 页面 (EPUB 同理, 在此不作展示)。

**主要功能**

* **元数据加载**: 读取 `-10000.json` 中的书籍信息 (书名、作者、状态、总章节数、字数、简介、标签)
* **章节列表构建**: 从 SQLite 数据库 (`{book_id}.qd`) 提取章节 (`volume`、`chapter` 表), 并筛选现有 JSON 文件
* **HTML 渲染**

  * **章节页面**: 依次渲染每个章节内容, 插入段落与内嵌图片, 并生成上下章导航
  * **目录页面**: 生成全书 TOC, 包括卷名与章节列表, 并渲染元数据头部
* **资源下载**: 自动下载并本地化图片到 `images/{book_id}/`, 更新 HTML 中的 `<img>` 路径

**运行前准备**

1. **配置参数**

   * `USER_ID`、`BOOK_ID`: 确定数据来源和输出目标
2. **命令行参数**

   ```bash
   python export2html.py --user-id 123456 --book-id 654321
   ```

**默认目录结构**

* **输入目录**: `./output/{user_id}/{book_id}/` (`qd_decrypt.py` 生成的 JSON)
* **输出目录**: `./chapter_html/{user_id}/{book_id}/` (生成的 `c{chapter_id}.html`)
* **图片目录**: `./images/{book_id}/` (下载的封面/插图资源)

执行完成后, `chapter_html/{user_id}/{book_id}/` 下包含所有章节页面和根目录 `/{book_id}.html`, 可直接用浏览器打开。

<details>
<summary>`export2html.py` (点击展开)</summary>

```python
import argparse
import html
import json
import os
import random
import sqlite3
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests
from tqdm import tqdm


# --------------------------------------------------
# Static constants
# --------------------------------------------------
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/134.0.0.0 Safari/537.36"
)
DEFAULT_HEADERS = {
    "Accept-Encoding": "gzip",
    "Connection": "Keep-Alive",
    "Referer": "https://www.qidian.com/",
    "User-Agent": DEFAULT_USER_AGENT,
}

CONFIG_PATH = Path.cwd() / "config.json"

# Globals filled in at runtime
USER_ID: str = ""
BOOK_ID: str = ""
DATA_DIR: Path
OUT_DIR: Path
IMG_DIR: Path

SESSION: requests.Session


# -------------------------------------------------------------------
# HTML Templates
# -------------------------------------------------------------------
CHAPTER_CSS_TEMPLATE = '''
:root {
  --max-width: 800px;
  --spacing: 1rem;
  --color-bg: #fff;
  --color-text: #333;
  --color-primary: #0070f3;
  --color-muted: #666;
  --color-border: #eaeaea;
  --font-sans: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
}
@media (prefers-color-scheme: dark) {
  :root {
    --color-bg: #121212;
    --color-text: #e4e4e4;
    --color-muted: #aaa;
    --color-border: #333;
  }
}
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}
body {
  max-width: var(--max-width);
  margin: calc(var(--spacing) * 2) auto;
  padding: var(--spacing);
  background: var(--color-bg);
  color: var(--color-text);
  font-family: var(--font-sans);
  line-height: 1.7;
}
.chapter-nav {
  display: flex;
  justify-content: center;
  gap: var(--spacing);
  padding: var(--spacing);
  background: var(--color-border);
  border-radius: 8px;
  position: sticky;
  top: var(--spacing);
  z-index: 100;
}
.chapter-nav a {
  color: var(--color-primary);
  text-decoration: none;
  font-weight: 500;
}
.chapter-nav a:hover {
  text-decoration: underline;
}
h1 {
  margin-top: var(--spacing);
  font-size: 2rem;
  text-align: center;
}
img, video {
  max-width: 100%;
  height: auto;
  display: block;
  margin: var(--spacing) auto;
  border-radius: 4px;
}
hr {
  border: none;
  border-top: 1px solid var(--color-border);
  margin: calc(var(--spacing) * 2) 0;
}
.author-comments {
  background: var(--color-border);
  padding: var(--spacing);
  border-left: 4px solid var(--color-muted);
  border-radius: 4px;
}
.author-comments p:first-child {
  font-weight: 600;
  margin-bottom: .5rem;
}
/* Scroll buttons */
.scroll-btns {
  position: fixed;
  bottom: var(--spacing);
  right: var(--spacing);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  z-index: 200;
}
.scroll-btns button {
  width: 2.5rem;
  height: 2.5rem;
  border: none;
  border-radius: 50%;
  background: var(--color-primary);
  color: #fff;
  font-size: 1.2rem;
  cursor: pointer;
  box-shadow: 0 2px 6px rgba(0,0,0,0.2);
  transition: background 0.2s;
}
.scroll-btns button:hover {
  background: var(--color-muted);
}
'''

CHAPTER_JS_TEMPLATE = '''
(() => {
  document.addEventListener('keydown', (e) => {
    if (['ArrowLeft','ArrowRight'].includes(e.key)) {
      const role = e.key === 'ArrowLeft' ? 'prev' : 'next';
      const link = document.querySelector(`.chapter-nav a[data-role="${role}"]`);
      if (link) window.location.href = link.href;
    }
  });
  // scroll buttons
  document.getElementById('scroll-top')?.addEventListener('click', () =>
    window.scrollTo({ top: 0, behavior: 'smooth' })
  );
  document.getElementById('scroll-bottom')?.addEventListener('click', () =>
    window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' })
  );
})();
'''

CHAPTER_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>{css}</style>
</head>
<body>
  <nav class="chapter-nav" id="nav-top">{nav_top}</nav>
  <main>
    <h1>{title}</h1>
    {body}
    {author_comments}
  </main>
  <nav class="chapter-nav" id="nav-bottom">{nav_bottom}</nav>
  <!-- Scroll to Top/Bottom Buttons -->
  <div class="scroll-btns">
    <button id="scroll-top" aria-label="Scroll to top">↑</button>
    <button id="scroll-bottom" aria-label="Scroll to bottom">↓</button>
  </div>
  <script>{js}</script>
</body>
</html>'''

INDEX_CSS_TEMPLATE = '''
:root {
  --max-width: 800px;
  --spacing: 1rem;
  --color-bg: #fff;
  --color-text: #333;
  --color-primary: #0070f3;
  --color-muted: #666;
  --color-border: #eaeaea;
  --font-sans: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
}
@media (prefers-color-scheme: dark) {
  :root {
    --color-bg: #121212;
    --color-text: #e4e4e4;
    --color-muted: #aaa;
    --color-border: #333;
  }
}
*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}
body {
  background: var(--color-bg);
  color: var(--color-text);
  font-family: var(--font-sans);
  max-width: var(--max-width);
  margin: calc(var(--spacing) * 2) auto;
  padding: var(--spacing);
}
/* Header grid: Title + Meta badges */
header {
  display: grid;
  grid-template-columns: 1fr auto;
  align-items: center;
  gap: var(--spacing);
  border-bottom: 1px solid var(--color-border);
  padding-bottom: var(--spacing);
  margin-bottom: calc(var(--spacing) * 2);
}
header h1 {
  font-size: 2.5rem;
  line-height: 1.2;
}
.meta-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}
.meta-item {
  background: var(--color-border);
  padding: 0.3rem 0.6rem;
  border-radius: 4px;
  font-size: 0.85rem;
  color: var(--color-muted);
}
.meta-item strong {
  color: var(--color-text);
}
/* Volume sections */
.volume-section {
  margin-bottom: calc(var(--spacing) * 2);
}
.volume-section h2 {
  font-size: 1.75rem;
  margin-bottom: 0.5rem;
  border-bottom: 2px solid var(--color-primary);
  padding-bottom: 0.25rem;
  color: var(--color-primary);
}
/* TOC grid of chapter links */
.toc ul {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: var(--spacing);
  list-style: none;
  margin: 0;
  padding: 0;
}
.toc a {
  display: block;
  padding: 0.5rem 0.75rem;
  border-radius: 4px;
  text-decoration: none;
  color: var(--color-text);
  transition: background 0.2s, color 0.2s;
}
.toc a:hover,
.toc a:focus {
  background: var(--color-border);
  color: var(--color-primary);
}
/* Scroll buttons for TOC */
.scroll-btns {
  position: fixed;
  bottom: var(--spacing);
  right: var(--spacing);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  z-index: 200;
}
.scroll-btns button {
  width: 2.5rem;
  height: 2.5rem;
  border: none;
  border-radius: 50%;
  background: var(--color-primary);
  color: #fff;
  font-size: 1.2rem;
  cursor: pointer;
  box-shadow: 0 2px 6px rgba(0,0,0,0.2);
  transition: background 0.2s;
}
.scroll-btns button:hover {
  background: var(--color-muted);
}
'''

INDEX_JS_TEMPLATE = """
// Scroll button handlers
document.getElementById('scroll-top')?.addEventListener('click', () =>
    window.scrollTo({ top: 0, behavior: 'smooth' })
);
document.getElementById('scroll-bottom')?.addEventListener('click', () =>
    window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' })
);
"""

INDEX_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>TOC - {BookName}</title>
  <style>{css}</style>
</head>
<body>
  <header>
    <h1>{BookName}</h1>
    <div class="meta-list">
      <div class="meta-item"><strong>Author:</strong> {Author}</div>
      <div class="meta-item"><strong>Status:</strong> {BookStatus}</div>
      <div class="meta-item"><strong>Chapters:</strong> {TotalChapterCount}</div>
      <div class="meta-item"><strong>Words:</strong> {WordsCnt}</div>
    </div>
  </header>
  <section class="description">
    <p>{Description}</p>
    <p><em>Tags:</em> {Tags}</p>
  </section>
  <main class="toc">
    {toc}
  </main>
  <!-- Scroll to Top/Bottom Buttons -->
  <div class="scroll-btns">
    <button id="scroll-top" aria-label="Scroll to top">↑</button>
    <button id="scroll-bottom" aria-label="Scroll to bottom">↓</button>
  </div>
  <script>{js}</script>
</body>
</html>'''


# --------------------------------------------------
# I/O & Config
# --------------------------------------------------
def load_config() -> None:
    global USER_ID, BOOK_ID
    try:
        cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        cfg = {}
    USER_ID = USER_ID or cfg.get("user_id") or ""
    BOOK_ID = BOOK_ID or cfg.get("book_id") or ""


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Generate HTML chapters and midpages for a given user/book/date."
    )
    p.add_argument("-u", "--user-id",  default=USER_ID,   help="USER_ID for fetching data")
    p.add_argument("-b", "--book-id",  default=BOOK_ID,   help="BOOK_ID for this export")
    return p.parse_args()


def update_globals(args: argparse.Namespace) -> None:
    global USER_ID, BOOK_ID, DATA_DIR, OUT_DIR, IMG_DIR, SESSION
    USER_ID, BOOK_ID = args.user_id.strip(), args.book_id.strip()
    base = Path.cwd()
    DATA_DIR    = base / "output"       / USER_ID / BOOK_ID
    OUT_DIR     = base / "chapter_html" / USER_ID / BOOK_ID
    IMG_DIR     = base / "images"       / BOOK_ID
    for d in (DATA_DIR, OUT_DIR, IMG_DIR):
        d.mkdir(parents=True, exist_ok=True)

    SESSION = requests.Session()
    SESSION.headers.update(DEFAULT_HEADERS)


def check_globals() -> bool:
    missing = [n for n in ("USER_ID","BOOK_ID") if not globals().get(n)]
    if missing:
        print(f"[ERROR] Missing parameters: {', '.join(missing)}", file=sys.stderr)
        return False
    return True


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


# --------------------------------------------------
# Download & image helpers
# --------------------------------------------------
def jitter_sleep(
    base: float,
    add_spread: float = 0.0,
    mul_spread: float = 1.0,
    *,
    max_sleep: float | None = None,
) -> None:
    if base < 0 or add_spread < 0 or mul_spread < 1.0:
        return

    multiplicative_jitter = random.uniform(1.0, mul_spread)
    additive_jitter = random.uniform(0, add_spread)
    duration = base * multiplicative_jitter + additive_jitter

    if max_sleep is not None:
        duration = min(duration, max_sleep)

    time.sleep(duration)


def fetch_image(
    url: str,
    target_dir: Path,
) -> Path:
    parsed = urlparse(url)
    fn = Path(parsed.path).name or "unnamed"
    dest = target_dir / fn
    if dest.exists():
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    resp = SESSION.get(url, timeout=10)
    resp.raise_for_status()
    dest.write_bytes(resp.content)
    jitter_sleep(1.0, add_spread=0.5)
    return dest

# -------------------------------------------------------------------
# HTML conversion helpers
# -------------------------------------------------------------------
def wrap_paragraphs(text: str) -> list[str]:
    return [
        f"<p>{html.escape(line.strip())}</p>"
        for line in text.splitlines()
        if line.strip()
    ]


def extract_image_map(cid: str, blocks: list[dict[str, Any]]) -> dict[int, list[str]]:
    img_map: dict[int, list[str]] = defaultdict(list[str])
    for blk in blocks:
        if blk.get("Type") == "image" and blk.get("Url"):
            idx = max(blk.get("Attach", 1) - 1, 0)
            url = blk["Url"]
            try:
                local = fetch_image(url, IMG_DIR / f"c{cid}")
                src = os.path.relpath(local, start=OUT_DIR).replace(os.sep, "/")
            except Exception:
                src = url
            img_map[idx].append(f'<p><img src="{html.escape(src, quote=True)}"/></p>')
    return img_map


# --------------------------------------------------
# HTML builders
# --------------------------------------------------
def build_nav_links(items: list[dict[str, Any]], idx: int) -> tuple[str, str]:
    def mk(item: dict[str, Any], role: str) -> str:
        eid, name = item["id"], item["name"]
        label = html.escape(name)
        if role == "prev":
            label = f"« {label}"
        elif role == "next":
            label = f"{label} »"
        return f'<a href="c{eid}.html" data-role="{role}">{label}</a>'

    prev_link = mk(items[idx - 1], "prev") if idx > 0 else ""
    toc_link  = f'<a href="../{BOOK_ID}.html">TOC</a>'
    next_link = mk(items[idx + 1], "next") if idx < len(items) - 1 else ""
    nav = " | ".join(filter(None, [prev_link, toc_link, next_link]))
    return nav, nav


def build_chapter_html(
    cid: str,
    data: dict[str, Any],
    title: str,
    nav_top: str,
    nav_bottom: str
) -> str:
    content = data.get("Content", "") or data.get("content", "")
    blocks  = data.get("Blocks", [])  or data.get("blocks", [])
    paras   = wrap_paragraphs(content)
    img_map = extract_image_map(cid, blocks)

    body_parts: list[str] = []
    for i, p in enumerate(paras):
        body_parts.append(p)
        body_parts.extend(img_map.get(i, []))
    body = "\n".join(body_parts)

    raw = data.get("author_comments", {}).get("AuthorComments", "").strip()
    if raw:
        comment_html = "\n".join(wrap_paragraphs(raw))
        author_comments = (
            "<hr/>\n<div class=\"author-comments\">\n"
            "<p>Author's Notes</p>\n"
            f"{comment_html}\n</div>"
        )
    else:
        author_comments = ""

    return CHAPTER_TEMPLATE.format(
        title=html.escape(title),
        nav_top=nav_top,
        body=body,
        nav_bottom=nav_bottom,
        author_comments=author_comments,
        css=CHAPTER_CSS_TEMPLATE,
        js=CHAPTER_JS_TEMPLATE,
    )


def build_toc_html(
    volumes: list[tuple[str, str]],
    items: list[dict[str, Any]],
    meta: dict[str, Any],
    book_id: str
) -> str:
    toc_lines: list[str] = []
    for vcode, vname in volumes:
        toc_lines.append(f'<div class="volume-section"><h2>{html.escape(vname)}</h2><ul>')
        for it in items:
            if it["vol"] == int(vcode):
                toc_lines.append(
                    f'<li><a href="{book_id}/c{it["id"]}.html">'
                    f'{html.escape(it["name"])}</a></li>'
                )
        toc_lines.append('</ul></div>')

    return INDEX_TEMPLATE.format(
        BookName=meta["BookName"],
        Author=meta["Author"],
        BookStatus=meta["BookStatus"],
        Description=meta["Description"],
        Tags=meta["Tags"],
        TotalChapterCount=meta["TotalChapterCount"],
        WordsCnt=meta["WordsCnt"],
        toc="\n".join(toc_lines),
        css=INDEX_CSS_TEMPLATE,
        js=INDEX_JS_TEMPLATE,
    )


# --------------------------------------------------
# Data loading
# --------------------------------------------------
def load_metadata(meta_path: Path) -> dict[str, Any]:
    raw = load_json(meta_path).get("content", {})
    return {
        "BookName": raw.get("BookName", ""),
        "Author": raw.get("Author", ""),
        "BookStatus": raw.get("BookStatus", ""),
        "Description": raw.get("Description", "").replace("\n", " "),
        "Tags": ", ".join(t.get("Name", "") for t in raw.get("Tags", [])),
        "TotalChapterCount": raw.get("TotalChapterCount", 0),
        "WordsCnt": raw.get("WordsCnt", 0),
    }


def load_volumes(db_path: Path) -> list[tuple[str, str]]:
    conn = sqlite3.connect(str(db_path))
    cur  = conn.cursor()
    cur.execute("SELECT VolumeCode, VolumeName FROM volume")
    vols = cur.fetchall()
    conn.close()
    return sorted(vols, key=lambda x: int(x[0]))


def load_all_items(
    db_path: Path,
) -> list[dict[str, Any]]:
    conn = sqlite3.connect(str(db_path))
    cur  = conn.cursor()
    cur.execute("SELECT ChapterId, ChapterName, VolumeCode, ShowOrder FROM chapter")
    rows = cur.fetchall()
    conn.close()

    available = {p.stem for p in DATA_DIR.glob("*.json") if p.stem != "-10000"}
    items: list[dict[str, Any]] = []

    for cid, name, vcode, order in rows:
        scid = str(cid)
        if scid not in available:
            continue
        items.append({
            "id": scid, "name": name,
            "vol": int(vcode), "order": order,
        })
    items.sort(key=lambda x: (x["vol"], x["order"]))
    return items


# --------------------------------------------------
# Main
# --------------------------------------------------
def main() -> None:
    load_config()
    args = parse_args()
    update_globals(args)
    if not check_globals():
        sys.exit(1)

    # 1) metadata
    meta      = load_metadata(DATA_DIR / "-10000.json")
    info_path = Path.cwd() / "data" / USER_ID / f"{BOOK_ID}.qd"
    volumes   = load_volumes(info_path)
    all_items = load_all_items(info_path)

    # 2) render chapters
    for idx, item in enumerate(tqdm(all_items, desc="Processing items")):
        eid, name = item["id"], item["name"]
        nav_top, nav_bottom = build_nav_links(all_items, idx)

        jpath = DATA_DIR / f"{eid}.json"
        if not jpath.exists():
            tqdm.write(f"[skip] Missing chapter JSON: {eid}.json")
            continue
        data    = load_json(jpath)
        html_out= build_chapter_html(eid, data, name, nav_top, nav_bottom)

        out_file = OUT_DIR / f"c{eid}.html"
        out_file.write_text(html_out, encoding="utf-8")

    # 3) build and save TOC
    toc_html = build_toc_html(volumes, all_items, meta, BOOK_ID)
    toc_path = OUT_DIR.parent / f"{BOOK_ID}.html"
    toc_path.write_text(toc_html, encoding="utf-8")


if __name__ == "__main__":
    main()
```

</details>
