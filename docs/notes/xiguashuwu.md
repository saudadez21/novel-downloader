# 西瓜书屋 (xiguashuwu) 分析笔记

创建日期: 2025/08/01

## 一、加密与分页结构

章节通常分页展示，常见情形:

* 第 1 页: 未加密
* 第 2 页: 通过 JS 打乱内容顺序, 并以图片替代部分文字
* 第 3 页及之后: 采用 AES 加密, 并以图片替代部分文字

## 二、JS 打乱与还原

在 `article.js` 可见如下核心逻辑 (节选):

```js
content = {
	load: function() {
		var e = base64.decode(document.getElementsByTagName('meta')[7].getAttribute('content')).split(/[A-Z]+%/);
		var j = 0;
		function r(a) {
			var c = '';
			var d = document.createElement('span');
			for (var i = 0; i < 20; i++) {
				var n = Math.floor(Math.random() * 99001 + 1000);
				c += String.fromCharCode(n)
			};
			var b = ['。', ': ', '？', '！', '—', '…', '；', ', ', '”', ''];
			c += b[Math.floor(Math.random() * b.length)];
			d.appendChild(document.createTextNode(c));
			a.appendChild(d);
			return a
		};
		for (var i = 0; i < e.length; i++) {
			var k = this.UpWz(e[i], i);
			this.childNode[k] = r(this.box.childNodes[i])
		};
		this.show()
	},
	UpWz: function(m, i) {
		var k = Math.ceil((i + 1) % this.code);
		k = Math.ceil(m - k);
		return k
	},
};
```

### 原理

* 顺序编码: 真实顺序被编码到 `<meta>` 的 Base64 字符串中。前端解码并以 `/[A-Z]+%/` 切分为数值片段数组 `e`。
* 还原映射: 对每个索引 `i` 和对应数值 `m`，用 `UpWz(m, i)` 求得目标索引 `k`，再执行 `childNode[k] = box.childNodes[i]` 完成重排 (等价于 `k = m - ((i + 1) % code)`)。
* 噪声插入: 在节点内附加随机字符 `<span>`，用于干扰，不影响重排。

### 参考复现 (Python)

```python
import base64
import re

raw = "MUIlOFYlNFUlMThXJTE4USUxMVMlNUclMjBNJTVaJTExQyUxM0wlMTVNJTZNJTVOJTEyTiUxNlIlMjJIJTEwUSUxNw=="
codeurl = 6

def restore_order(raw_b64: str, code: int) -> list[int]:
    decoded = base64.b64decode(raw_b64).decode('utf-8')
    fragments = re.split(r'[A-Z]+%', decoded)

    order = [0] * len(fragments)
    for i, m in enumerate(fragments):
        # UpWz logic: k = ceil(parseInt(m) - ceil((i+1) % codeurl))
        k = int(m) - ((i + 1) % code)
        order[k] = i
    return order

restore_order(raw, codeurl)
```

## 三、图片替代文字

### 现象

部分文字被单字切分并替换为 `<img class="hz" src="...">`，示例:

```html
<div id="QHUMBNFZW" class="ANCLMRVOKTQIWESHUGFYZDX">
    <div>
    <p style="text-indent: 2em; padding: 0px; margin: 0px">
        坑底见:将黎屿移<img
        class="hz"
        src="http://www.xiguashuwu.com/wzbodyimg/eOSvYn.png"
        />群吧……<br /><br />
    </p>
    </div>
    <div>
    <p style="text-indent: 2em; padding: 0px; margin: 0px">
        舒澄没好意思反驳他，这么好的看<img
        class="hz"
        src="http://www.xiguashuwu.com/wzbodyimg/C5mkg5.png"
        />，节目组怎么可能会剪掉。<br /><br />
    </p>
    </div>
    <div>
    <p style="text-indent: 2em; padding: 0px; margin: 0px">
        ——哈哈哈哈哈哈我只会哈哈哈哈哈哈哈哈
    </p>
    </div>
</div>
```

粗略统计显示图片字库规模有限 (约 600 余张)，可构建 "图片文件名 -> 字符" 的映射进行回写，例如:

```json
{
  "eOSvYn.png": "出",
  "C5mkg5.png": "点",
  "sbmbNu.png": "蕾"
}
```

### 复原策略

1. OCR: 对 `class="hz"` 的图片进行识别，得到字形对应文本。
2. 文本对齐: 利用页数 >= 3 的响应中 "未加密预览文本" (纯文字) 与 "解密后的完整内容" (含图片替换) 进行逐行对齐; 当完整内容在某字符位出现 `<img class="hz" src=".../xxx.png">`，以同位的预览字符 `ch` 作为映射值，记录 `img_map[xxx.png] = ch`。若已存在不同映射，记录冲突并保留原值。

### 数据结构

* `img_map: {filename -> char}`: 最终映射。
* `img_seen: set[str]`: 已发现但未确认的图片标识集合。

### 采集与对齐流程

1. 章节筛选: 遍历页数 >= 3 的章节。
2. 采样收集: 在第 2 页收集出现的 `img.hz` 加入 `img_seen`。
3. 完整解密: 对页数 >= 3 的内容, 解出 AES 完整内容 (该处为图片替换版本)
4. 逐行对齐: 基于可见纯文与完整内容对齐，生成/补全 `img_map`，并维护 `img_seen` 去重。

## 四、AES加密

解密函数 (页面脚本):

```js
function d(a, b) {
    b = CryptoJS.MD5(b).toString();
    var d = CryptoJS.enc.Utf8.parse(b.substring(0, 16));
    var e = CryptoJS.enc.Utf8.parse(b.substring(16));
    return CryptoJS.AES.decrypt(a, e, {
        iv: d,
        padding: CryptoJS.pad.Pkcs7
    }).toString(CryptoJS.enc.Utf8)
}
```

### 参数与流程

* `a`: 密文字符串 (通常先经 `decodeURIComponent(...)`, 本质为 Base64)
* `b`: 页面里给出的 32 位 hex 串 (示例: `"60e66001b77c190fda1fd44db437bbb9"`)
* 派生: 对 `b` 做 MD5 -> 得到 32 位 hex 文本; 取前 16 个字符作为 IV, 后 16 个作为 Key, 均以 UTF-8 文本字节参与运算
* 算法: AES-CBC + PKCS7 填充, 输出按 UTF-8 解码

页面示例提取点:

```html
<script>
    let newcon = decodeURIComponent(
    "r0Fyb1zxoHYQQdpyqWXez71J%2BYRE..."
    );
    newcon = d(newcon, "60e66001b77c190fda1fd44db437bbb9");
    $("#JLZAKFETS").html(newcon);
</script>
```

提取步骤:

1. 抓取 `decodeURIComponent("...")` 的参数并 URL 解码，得到 Base64 密文 `a`
2. 抓取 `d(newcon, "....")` 的第二个参数作为 `b`
3. 按上述派生方式解密

参考复现 (Python):

```python
import base64
import hashlib
import re
import urllib.parse

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

_RE_NEWCON = re.compile(r"""let\s+newcon\s*=\s*decodeURIComponent\(\s*['"](.+?)['"]\s*\);?""", re.IGNORECASE)
_RE_D_CALL = re.compile(r"""d\(\s*[^,]+,\s*['"]([0-9A-Fa-f]{32})['"]\s*\);?""", re.IGNORECASE)

def parse_newcon(text: str) -> str:
    m = _RE_NEWCON.search(text)
    if not m:
        raise ValueError("newcon not found")
    return urllib.parse.unquote(m.group(1))

def parse_d_key(text: str) -> str:
    m = _RE_D_CALL.search(text)
    if not m:
        raise ValueError("d() call with key not found")
    return m.group(1)

def decrypt_d(a: str, b: str) -> str:
    digest = hashlib.md5(b.encode("utf-8")).hexdigest()  # 32 hex chars

    iv  = digest[:16].encode('utf-8')
    key = digest[16:].encode('utf-8')

    ct = base64.b64decode(a)

    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded = cipher.decrypt(ct)
    plaintext = unpad(padded, block_size=16, style="pkcs7")

    return plaintext.decode('utf-8')
```
