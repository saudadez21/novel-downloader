# 西瓜书屋 (xiguashuwu) 分析笔记

日期: 2025/08/01

## 一、加密结构

章节内容可能分页展示, 常见三种情况:

* 第 1 页: 未加密
* 第 2 页: 通过 JS 打乱内容顺序, 并以图片替代文字
* 第 3 页及之后: 采用 AES 加密, 并以图片替代文字

## 二、JS 打乱与还原

在 `article.js` 会发现以下代码:

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

### 核心思路

将真实顺序编码进 `<meta>` 的 Base64 字符串; 前端解码后用 "还原函数" 把节点映射回正确位置, 同时插入少量随机噪声字符混淆

**关键点**

* **数据来源**: 读取 `meta[7].content`, 先 Base64 解码, 再用正则 `/[A-Z]+%/` 切分为数字片段数组 `e`
* **乱序 -> 还原**: 对片段下标 `i` 取数值 `m`, 用 `UpWz(m, i)` 得到目标索引 `k`, 执行 `childNode[k] = box.childNodes[i]` 完成重排 (本质等价于 `k = m - ((i + 1) % code)`)
* **噪声处理**: 额外插入随机字符/标点的 `<span>`, 不影响重排, 仅用于干扰

可使用 Python 复现还原逻辑:

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

## 三、图片代替文字

### 现象

部分文字被按 "单字一图" 的方式替换成 `<img class="hz" src="...">`, 如示例所示:

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

粗抓样本显示图片库规模有限 (约 617 张), 因此可通过**字典映射**将图片回写为对应汉字, 示例映射:

```json
{
  "eOSvYn.png": "出",
  "C5mkg5.png": "点",
  "sbmbNu.png": "蕾"
}
```

### 复原策略

#### OCR 识别

对 `class="hz"` 的图片跑 OCR, 得到字形 -> 文本

#### 内容对齐复原

根据分析, 第 3 页及之后返回两部分:

1. **未加密的预览文本** (**不**做图片替换, 纯文字)
2. **AES 加密的完整内容** (解密后是**含图片替换**的完整文本)

因此, **使用页数 >= 3 的响应**做对齐: 拿 "未替换的预览纯文" 去对齐 "解密后的含图完整文本", 从而推导出 "图片 -> 字符" 的映射

### 数据结构

* `img_map: {filename -> char}`: 图片到单字的最终映射
* `img_seen: set[str]`: 已发现但尚未确认/或仅出现过的图片 URL/文件名集合, 用于后续补齐与去重

### 采集与对齐流程

1. **章节筛选**: 遍历**页数 >= 3**的章节 (规模约 500 章, 实际视未识别量而定)
2. **第二页采样**: 收集各章第 2 页出现的 `img.hz` (若有) 到 `img_seen`
3. **完整内容解出**: 对页数 >= 3 的内容, 解出 AES 完整内容 (该处为图片替换版本)
4. **逐行对齐**: 将 "页面可见内容" (纯文本) 与 "完整内容" (含图片) 按行对齐, 对每行:

   * 以 "可见文本" 的**可见字符序**为基准 (忽略标签与多余空白), 对 "完整内容" 同位置进行比对
   * 当 "完整内容" 在某字符位是图片 `<img class="hz" src=".../xxx.png">`:

     * 取同位的 "可见文本" 字符 `ch`, 记 `img_map[xxx.png] = ch`
     * 若 `xxx.png` 已存在映射但值不一致, 则 log 记录并跳过覆盖 (避免误配)
   * 处理完毕后, 将该行 (以及未能对齐到文本的剩余图片 URL) 统一加入 `img_seen`

## 四、AES加密

解密函数:

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

**参数含义与流程**

* `a`: 密文字符串 (先经过 `decodeURIComponent(...)`, 本质是 Base64)
* `b`: 页面里给出的 32 位 hex 串 (示例: `"60e66001b77c190fda1fd44db437bbb9"`)
* **派生方式**: 对 `b` 做 MD5 -> 得到 32 位 *hex 文本*; 取前 16 个字符作为 **IV**, 后 16 个作为 **Key**, 两者都按 **UTF-8 文本字节** 使用
* **算法**: AES-CBC + PKCS7 填充, 输出按 UTF-8 解码为明文

**页面提取点**

```html
<script>
    let newcon = decodeURIComponent(
    "r0Fyb1zxoHYQQdpyqWXez71J%2BYRE..."
    );
    newcon = d(newcon, "60e66001b77c190fda1fd44db437bbb9");
    $("#JLZAKFETS").html(newcon);
</script>
```

* 从脚本里抓 `decodeURIComponent("...")` 的内容 -> URL 解码 -> 得到 `a` (Base64)
* 抓 `d(newcon, "....")` 里的第二个参数 -> 作为 `b`

可使用 Python 复现还原逻辑:

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
