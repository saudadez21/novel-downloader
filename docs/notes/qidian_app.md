# 起点小说 App 端分析笔记

日期: 2025/06/17

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

* **示例 param**:

  ```json
  {
    "bookId": 1234567,
    "timeStamp": 1750000000000,
    "requestSource": 0,
    "md5Signature": "xxxxxxx",
    "extendchapterIds": 1234567
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
    | ui       | userId |
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

---

## 二、`*.qd` 文件结构与内容解析

### 1. 文件目录结构

`*.qd` 文件主要用于存储起点 App 的本地缓存数据, 安卓端位于以下路径:

```sh
/data/media/0/Android/data/com.qidian.QDReader/files/QDReader/book/{user_id}/
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

#### 所用工具与依赖

用于分析和提取章节 `.qd` 文件内容, 涉及以下工具与库:

##### 逆向分析工具

- [`jadx`](https://github.com/skylot/jadx/releases): 用于反编译 APK, 提取 Java 层逻辑
- [`Ghidra`](https://github.com/NationalSecurityAgency/ghidra/releases): 静态分析原生库 (如 `.so` 文件)
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
        stringBuffer.append(" 读取，耗时:");
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

使用 Ghidra 对 `libload-jni.so` 进行反汇编分析后. 可快速定位到对应的 native 方法实现 `Java_a_b_b`:

<details>
<summary>Java_a_b_b 实现片段 (点击展开)</summary>

```c
undefined8
Java_a_b_b(long *param_1,undefined8 param_2,undefined8 param_3,undefined8 param_4,undefined8 param_5
          ,undefined8 param_6,undefined8 param_7,undefined8 param_8)
{
  // ...
  lVar5 = (**(code **)(*param_1 + 0x30))(param_1,&DAT_00100a57);
  if (((lVar5 != 0) && (lVar6 = (**(code **)(*param_1 + 0x30))(param_1,&DAT_00100a57), lVar6 != 0))
     && (lVar7 = (**(code **)(*param_1 + 0x30))(param_1,&DAT_00100a57), lVar7 != 0)) {
    __android_log_print(3,"QDReader_Jni","JNI:0");
    uVar8 = (**(code **)(*param_1 + 0x548))(param_1,param_7,0);
    __android_log_print(3,"QDReader_Jni","bookid: %s,chapterid: %s,userid: %s,imei: %s",__ptr,__src,
                        puVar1,uVar8);
    __android_log_print(3,"QDReader_Jni","JNI:1");
    __strcpy_chk(puVar2,puVar1,0xff);
    pcVar9 = (char *)__strcat_chk(puVar2,uVar8,0xff);
    __s = strcat(pcVar9,__src);
    sVar10 = strlen(__s);
    builtin_strncpy(pcVar9 + sVar10,"2EEE1433A152E84B3756301D8FA3E69A",0x21);
    __android_log_print(3,"QDReader_Jni","JNI:2");
    uVar11 = (**(code **)(*param_1 + 0x538))(param_1,puVar2);
    __android_log_print(3,"QDReader_Jni","JNI:3");
    lVar12 = (**(code **)(*param_1 + 0x388))
                       (param_1,lVar5,&DAT_00100a86,
                        "(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;");
    __android_log_print(3,"QDReader_Jni","JNI:4");
    if (lVar12 != 0) {
      __android_log_print(3,"QDReader_Jni","sha1id:%d",lVar12);
      __android_log_print(3,"QDReader_Jni","JNI:5");
      uVar13 = (**(code **)(*param_1 + 0x390))(param_1,lVar5,lVar12,param_7,uVar11);
      (**(code **)(*param_1 + 0x550))(param_1,uVar11,puVar2);
      __android_log_print(3,"QDReader_Jni","JNI:6");
      pcVar9 = (char *)(**(code **)(*param_1 + 0x548))(param_1,uVar13,0);
      __android_log_print(3,"QDReader_Jni","sha1key1 = %s",pcVar9);
      __android_log_print(3,"QDReader_Jni","JNI:7");
      sVar10 = strlen(pcVar9);
      if (0x17 < sVar10) {
        memset(&DAT_00104100,0,0x400);
        strncpy(&DAT_00104100,pcVar9,0x18);
      }
      __android_log_print(3,"QDReader_Jni","JNI:8 sha1key2:%s sha1key1:%s",&DAT_00104100,pcVar9);
      (**(code **)(*param_1 + 0x550))(param_1,uVar13,pcVar9);
      uVar11 = (**(code **)(*param_1 + 0x538))(param_1,&DAT_00104100);
      __android_log_print(3,"QDReader_Jni","JNI:9");
      __strcpy_chk(puVar3,&DAT_00104100,0xff);
      __strcat_chk(puVar3,uVar8,0xff);
      __android_log_print(3,"QDReader_Jni","JNI:10");
      uVar13 = (**(code **)(*param_1 + 0x538))(param_1,puVar3);
      __android_log_print(3,"QDReader_Jni","JNI:11");
      lVar5 = (**(code **)(*param_1 + 0x388))
                        (param_1,lVar6,&DAT_00100c2f,
                         "(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;");
      __android_log_print(3,"QDReader_Jni","JNI:12");
      if (lVar5 != 0) {
        __android_log_print(3,"QDReader_Jni","JNI:13");
        uVar14 = (**(code **)(*param_1 + 0x538))(param_1,puVar1);
        uVar15 = (**(code **)(*param_1 + 0x390))(param_1,lVar6,lVar5,uVar14,uVar13);
        (**(code **)(*param_1 + 0x550))(param_1,uVar13,puVar3);
        __android_log_print(3,"QDReader_Jni","JNI:14");
        pcVar9 = (char *)(**(code **)(*param_1 + 0x548))(param_1,uVar15,0);
        __android_log_print(3,"QDReader_Jni","JNI:15");
        sVar10 = strlen(pcVar9);
        if (sVar10 < 0x19) {
          __strcpy_chk(puVar4,pcVar9,0xff);
        }
        else {
          puVar4 = (undefined8 *)&DAT_00104100;
          memset(&DAT_00104100,0,0x400);
          strncpy(&DAT_00104100,pcVar9,0x18);
        }
        (**(code **)(*param_1 + 0x550))(param_1,uVar15,pcVar9);
        __android_log_print(3,"QDReader_Jni","JNI:16");
        uVar13 = (**(code **)(*param_1 + 0x538))(param_1,puVar4);
        __android_log_print(3,"QDReader_Jni","JNI:17");
        lVar5 = (**(code **)(*param_1 + 0x388))
                          (param_1,lVar7,&DAT_00100c72,"([BLjava/lang/String;)[B");
        __android_log_print(3,"QDReader_Jni","JNI:18");
        if (lVar5 != 0) {
          __android_log_print(3,"QDReader_Jni","JNI:19");
          uVar15 = (**(code **)(*param_1 + 0x390))(param_1,lVar7,lVar5,param_5,uVar13);
          __android_log_print(3,"QDReader_Jni","JNI:20");
          uVar11 = (**(code **)(*param_1 + 0x390))(param_1,lVar7,lVar5,uVar15,uVar11);
          __android_log_print(3,"QDReader_Jni","JNI:21");
          (**(code **)(*param_1 + 0x550))(param_1,param_7,uVar8);
          __android_log_print(3,"QDReader_Jni","JNI:22 %s",&DAT_00104100);
          __android_log_print(3,"QDReader_Jni","JNI:23");
          (**(code **)(*param_1 + 0x550))(param_1,uVar13,puVar4);
          __android_log_print(3,"QDReader_Jni","JNI:24");
          (**(code **)(*param_1 + 0x550))(param_1,uVar14,puVar1);
          __android_log_print(3,"QDReader_Jni","JNI:25");
          free(__ptr);
          __android_log_print(3,"QDReader_Jni","JNI:26");
          free(__src);
          __android_log_print(3,"QDReader_Jni","JNI:27");
          return uVar11;
        }
      }
    }
  }
  return 0;
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

def sha1_hmac(key: str, data: str) -> str:
    digest = hmac.new(key.encode(), data.encode(), hashlib.sha1).digest()
    return b64encode(digest).decode()[:24]

def md5_hmac(key: str, data: str) -> str:
    digest = hmac.new(key.encode(), data.encode(), hashlib.md5).digest()
    return b64encode(digest).decode()[:24]

def des3_decrypt(data: bytes, secret: str) -> bytes:
    """3DES/CBC 解密"""
    cipher = DES3.new(secret.encode(), DES3.MODE_CBC, b'\x00' * 8)
    return cipher.decrypt(data)

def decrypt_content(cid: str, chunk1: bytes, uid: str, imei: str) -> str:
    """
    - 对 chunk1 做两次 3DES 解密
    - 自动探测 PKCS#7 填充并丢掉
    - 去掉末尾非加密的 '附加' 字节
    """
    # 计算两把 key
    sec1 = sha1_hmac(
        imei,
        uid + imei + cid + "2EEE1433A152E84B3756301D8FA3E69A",
    )
    sec2 = md5_hmac(uid, sec1 + imei)

    # 解密
    raw = chunk1
    step1 = des3_decrypt(raw, sec2)
    step2 = des3_decrypt(step1, sec1)

    # 自动检测 PKCS#7 填充:
    # 找最后一个重复 p 次的字节 p (1 <= p <= 8),
    # 且 (idx + p) 是 8 的倍数, 即 padded_length = idx + p
    padded_len = None
    pad_len = None
    for p in range(8, 0, -1):
        pattern = bytes([p]) * p
        idx = step2.rfind(pattern)
        if idx != -1 and (idx + p) % 8 == 0:
            padded_len = idx + p
            pad_len = p
            break
    if padded_len is None:
        raise ValueError("无法自动检测填充 (padding) 位置")

    # 去掉后 pad_len 字节
    json_bytes = step2[: padded_len - pad_len ]
    text = json_bytes.decode('utf-8', errors='replace')
    return text
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

由于 `libfock.so` 是另一套独立的 native 实现, 此处不继续深入分析其内部逻辑, 而是选择直接使用 `Frida` 对相关方法进行 Hook。

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

                    resolve(JSON.stringify({
                        status: status,
                        content: contentStr
                    }));
                } catch (e) {
                    resolve(JSON.stringify({
                        status: -999,
                        error: e.toString()
                    }));
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

##### 3.5.4 批量解密与导出实现

基于前述各模块, 可整合为一个完整的批量解密脚本。

该脚本支持对指定目录下的 `.qd` 文件进行批量处理, 并将解析结果导出为对应的 `.json` 文件, 便于后续分析与使用。

使用前, 请根据实际情况修改 `main()` 函数中的以下参数:

* `book_id`, `user_id`, `imei` (作为解密参数)
* `device = frida.get_device("your.device.ip.address")` (根据连接方式选择 IP/USB)

默认行为如下:

* 输入目录: `./data/{book_id}/` (包含章节 `.qd` 文件)
* 输出目录: `./output/{book_id}/` (生成对应的 `.json` 文件)

<details>
<summary>`qd_decrypt.py` (点击展开)</summary>

```python
import json
import hashlib
import hmac
from base64 import b64encode
from io import BytesIO
from pathlib import Path
from typing import Any

import frida
from Crypto.Cipher import DES3


def sha1_hmac(key: str, data: str) -> str:
    digest = hmac.new(key.encode(), data.encode(), hashlib.sha1).digest()
    return b64encode(digest).decode()[:24]


def md5_hmac(key: str, data: str) -> str:
    digest = hmac.new(key.encode(), data.encode(), hashlib.md5).digest()
    return b64encode(digest).decode()[:24]


def des3_decrypt(data: bytes, secret: str) -> bytes:
    """3DES/CBC 解密"""
    cipher = DES3.new(secret.encode(), DES3.MODE_CBC, b'\x00' * 8)
    return cipher.decrypt(data)


def decrypt_content(cid: str, chunk1: bytes, uid: str, imei: str) -> str:
    """
    - 对 chunk1 做两次 3DES 解密
    - 自动探测 PKCS#7 填充并丢掉
    - 去掉末尾非加密的 '附加' 字节
    """
    sec1 = sha1_hmac(
        imei,
        uid + imei + cid + "2EEE1433A152E84B3756301D8FA3E69A",
    )
    sec2 = md5_hmac(uid, sec1 + imei)

    raw = chunk1
    step1 = des3_decrypt(raw, sec2)
    step2 = des3_decrypt(step1, sec1)

    padded_len = None
    pad_len = None
    for p in range(8, 0, -1):
        pattern = bytes([p]) * p
        idx = step2.rfind(pattern)
        if idx != -1 and (idx + p) % 8 == 0:
            padded_len = idx + p
            pad_len = p
            break
    if padded_len is None:
        raise ValueError("无法自动检测填充 (padding) 位置")

    json_bytes = step2[: padded_len - pad_len ]
    text = json_bytes.decode('utf-8', errors='replace')
    return text


def decrypt(
    path: Path,
    book_id: str,
    uid: str,
    imei: str,
    script,
) -> dict[str, Any]:
    """
    解密起点章节 .qd 文件内容

    文件结构格式符合 Java 方法 `com.qidian.common.lib.util.m.r` 中的定义:

    采用定长前缀结构 `[len0][data0][len1][data1]...[len4][data4]`, 共 5 段

    解密流程概述:
    - 分段读取加密数据块
    - 使用解密算法与 Frida 提供的 JS 脚本进行解密
    - 若类型为 `type == 1`, 进一步解包内容与结构块信息 (blocks)
    """
    cid = path.stem
    with path.open('rb') as f:
        buf = BytesIO(f.read())

    def decode_str(barr: bytes) -> str:
        try:
            return barr.decode('utf-8')
        except Exception:
            return barr.decode('utf-8', errors='replace')

    def read_chunk():
        raw = buf.read(4)
        if len(raw) < 4:
            raise IOError("文件结构不完整，无法读取长度")
        length = int.from_bytes(raw, byteorder='little')
        return buf.read(length)

    # 按顺序读出所有 5 段
    chunk0 = read_chunk()
    chunk1 = read_chunk()
    chunk2 = read_chunk()
    chunk3 = read_chunk()
    chunk4 = read_chunk()

    text_1 = decrypt_content(cid, chunk1, uid, imei)
    content = ""
    content_type = 0
    block_infos = []
    author_content = {}
    resources = []
    try:
        data_obj = json.loads(text_1 or "{}")
        content = data_obj.get("content") or data_obj.get("Content", "")
        content_type = data_obj.get("type", 0)
        block_infos = data_obj.get("Blocks", [])
        author_content = data_obj.get("AuthorComments", {})
        resources = data_obj.get("Resources", [])
    except Exception as e:
        print(f"decrypt_content(cid = {cid}): {e}")

    if content_type == 1:
        key_1 = cid
        key_2 = f"{book_id}_{cid}"
        raw = script.exports_sync.unlock(content, key_1, key_2)
        if raw:
            try:
                decoded = json.loads(raw)
                content = decoded.get("content", "")
            except Exception:
                pass

        try:
            txt2 = decode_str(chunk2)
            author_content = json.loads(txt2)
        except Exception:
            author_content = {}

        block_infos: list[Any] = []
        try:
            txt4 = decode_str(chunk4)
            if txt4:
                block_infos = json.loads(txt4)
        except Exception:
            block_infos = []

    return {
        "content": content,
        "type": content_type,
        "author_comments": author_content,
        "blocks": block_infos,
        "resources": resources,
    }


def main():
    book_id = "11111111"
    user_id = "22222222"
    imei = "your:imei:info"

    data_dir = Path.cwd() / "data" / book_id
    out_dir = Path.cwd() / "output" / book_id
    out_dir.mkdir(parents=True, exist_ok=True)

    device = frida.get_device("your.device.ip.address")

    session = device.attach("起点读书")

    with open("hook_fock.js", "r", encoding="utf-8") as f:
        jscode = f.read()

    script = session.create_script(jscode)
    script.load()

    print("[*] Script loaded. Starting unlock tasks...")

    for file_path in data_dir.glob("*.qd"):
        cid = file_path.stem
        out_path = out_dir / f"{cid}.json"

        try:
            obj = decrypt(
                file_path,
                book_id,
                user_id,
                imei,
                script,
            )
        except Exception as e:
            obj = {"error": str(e)}

        with out_path.open('w', encoding='utf-8') as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)

        print(f"{file_path.name} -> {out_path.name}")


if __name__ == "__main__":
    main()
```
</details>
