---
title: JavaScript IIFE Parsing Notes
date: 2025-09-28
---

# JavaScript 标准 IIFE 解析笔记

> 使用 Python 解析 "标准形态" 的 JavaScript IIFE 返回对象
>
> Standard-form JavaScript IIFE extraction and parsing using Python.

日期: 2025/09/28

---

## 一、背景

在使用 Python 解析 HTML 时，有时会遇到**接近 JSON、但不是 JSON**的 JavaScript 对象表达式:

* 键可能未加引号: `{ a: 1 }`
* 值可能是**标识符/形参引用**: `{ a: a, b: foo }`
* 同时包含 `null / undefined / true / false / number / string / list / dict`
* 多见于 **IIFE (Immediately Invoked Function Expression)** 的返回值

这类结构无法直接用 `json.loads`，需要先做一层解析与还原。

---

## 二、IIFE 简介

**IIFE (立即执行函数表达式)** 典型结构:

* 结构: `(function (...) { ... }( ... ));`
  * 第一对括号把 `function` 变为**表达式**
  * 随后紧跟实参 `(...)` **立即调用**
* 可拥有任意数量的形参/实参

常见 IIFE 变体:

```js
// standard IIFE
(function () {
  // statements...
  console.log("Hello IIFE");
})();

(function(a, b) {
  console.log(a + b);
}(1, 2));

// arrow function variant
(() => {
  // statements...
  console.log("Arrow IIFE");
})();

// async IIFE
(async () => {
  // statements...
})();
```

**本笔记仅处理**: 返回 **对象字面量**、且对象内部语法**受限**的“标准形态”，例如:

```js
(function(a, b) {
  return {
    a: a,
    foo: [a, b, a, a]
  }
}(1, 0));
```

**不覆盖**: 计算属性、方法简写、模板字符串、函数/类/正则字面量、表达式求值、解构/展开、`this/new/Symbol`、注入式代码等复杂语义。

> 说明: 为了稳定性，
>
> * 将 `undefined` 视作 `null` (映射到 Python `None`)
> * 数值仅支持十进制与指数形式 (不解析 16/8/2 进制，亦不处理 `NaN/Infinity`)

---

## 三、方案一: 字符串替换版 (转 JSON 再 `json.loads`)

**思路**

1. 用正则将 IIFE 拆为三段: **参数列表**、**返回对象文本**、**实参列表**。
2. 形参与实参一一对应，得到 `mapping` (如 `{"a": 1, "b": 0}`)。
3. 在返回对象文本中:
   * 将**未加引号的键**改写为带引号: `a:` -> `"a":`
   * 将**标识符值**若命中 `mapping`，替换为对应 JSON 字面量; 否则原样保留
4. 得到合法 JSON 字符串后，使用 `json.loads` 解析为 Python 对象。

<details>
<summary>核心片段 (点击展开)</summary>

```python
import json
import re
from typing import Any

IIFE_RE = re.compile(
    r'^\(function\((.*?)\)\s*\{\s*return\s*({.*?})\s*\}\s*\((.*?)\)\)$',
    re.S,
)

IDENT_START = re.compile(r'[A-Za-z_$]')
IDENT_BODY  = re.compile(r'[A-Za-z0-9_$]')
INT_RE = re.compile(r'[+-]?\d+')
FLOAT_RE = re.compile(r'^[+-]?(?:\d+\.\d*|\.\d+)(?:[eE][+-]?\d+)?$|^[+-]?\d+[eE][+-]?\d+$')

def parse_js_string(s: str) -> str:
    if not (s and s[0] == s[-1] and s[0] in ("'", '"')):
        raise ValueError(f"Invalid JS string literal: {s!r}")

    body = s[1:-1]
    if "\\" not in body:
        return body

    out = []
    it = iter(body)
    for ch in it:
        if ch != '\\':
            out.append(ch)
            continue

        try:
            esc = next(it)
        except StopIteration:
            break

        if esc in "'\"\\":
            out.append(esc)
        elif esc == 'n':
            out.append('\n')
        elif esc == 'r':
            out.append('\r')
        elif esc == 't':
            out.append('\t')
        elif esc == 'b':
            out.append('\b')
        elif esc == 'f':
            out.append('\f')
        elif esc == 'v':
            out.append('\v')
        elif esc == '0':
            out.append('\0')
        elif esc == 'x':
            hex2 = ''.join(next(it) for _ in range(2))
            out.append(chr(int(hex2, 16)))
        elif esc == 'u':
            hex4 = ''.join(next(it) for _ in range(4))
            out.append(chr(int(hex4, 16)))
        else:
            out.append(esc)  # 宽松处理未知转义

    return ''.join(out)

def parse_js_token(tok: str) -> Any:
    tok = tok.strip()
    match tok:
        case "null" | "undefined":
            return None
        case "true":
            return True
        case "false":
            return False
        case _ if INT_RE.fullmatch(tok):
            return int(tok)
        case _ if FLOAT_RE.fullmatch(tok):
            return float(tok)
        case _ if tok.startswith("'") and tok.endswith("'"):
            return parse_js_string(tok)
        case _ if tok.startswith('"') and tok.endswith('"'):
            return parse_js_string(tok)
        case _:
            return tok  # 标识符等

def split_args(s: str) -> list[str]:
    out = []
    buf = []
    stack = []

    it = iter(s)
    in_str = False
    esc = False
    quote = ''

    for ch in it:
        if in_str:
            buf.append(ch)
            if esc:
                esc = False
            elif ch == '\\':
                esc = True
            elif ch == quote:
                in_str = False
            continue

        if ch in ('"', "'"):
            in_str = True
            quote = ch
            buf.append(ch)
            continue

        if ch in '{[(':
            stack.append(ch)
            buf.append(ch)
            continue

        if ch in '}])':
            if stack:
                stack.pop()
            buf.append(ch)
            continue

        if ch == ',' and not stack:
            item = ''.join(buf).strip()
            if item:
                out.append(item)
            buf.clear()
            continue

        buf.append(ch)

    tail = ''.join(buf).strip()
    if tail:
        out.append(tail)

    return out

def transform_object(js_obj: str, mapping: dict[str, Any]) -> str:
    out = []
    n = len(js_obj)

    in_str = False
    quote = ''
    esc = False

    i = 0
    while i < n:
        ch = js_obj[i]

        if in_str:
            out.append(ch)
            if esc:
                esc = False
            elif ch == '\\':
                esc = True
            elif ch == quote:
                in_str = False
            i += 1
            continue

        if ch in ('"', "'"):
            in_str = True
            quote = ch
            out.append(ch)
            i += 1
            continue

        if IDENT_START.match(ch):
            j = i + 1
            while j < n and IDENT_BODY.match(js_obj[j]):
                j += 1
            ident = js_obj[i:j]

            k = j
            while k < n and js_obj[k] in " \t\r\n":
                k += 1

            if k < n and js_obj[k] == ':':
                out.append(f'"{ident}":')
                i = k + 1
                continue

            if ident in mapping:
                out.append(json.dumps(mapping[ident], ensure_ascii=False))
                i = j
                continue

            out.append(ident)
            i = j
            continue

        out.append(ch)
        i += 1

    return "".join(out)

def parse_iife(iife: str) -> dict:
    m = IIFE_RE.match(iife.strip())
    if not m:
        raise ValueError("Invalid IIFE format")

    params_str, obj_str, args_str = m.groups()

    params = [p.strip() for p in split_args(params_str)]
    args = [a.strip() for a in split_args(args_str)]

    if len(params) != len(args):
        raise ValueError("Param/arg length mismatch")

    mapping = {p: parse_js_token(a) for p, a in zip(params, args)}

    json_text = transform_object(obj_str, mapping)
    return json.loads(json_text)
```

</details>

**优点**

* 纯 Python，直观
* 产物符合 JSON 语义

**局限**

* 假设语法“受限”，对边界情况较敏感
* 注释、尾逗号等需额外处理
* **体量变大**时性能下降明显 (见性能对比)

---

## 四、方案二: Node 子进程 (近似原生语义)

**思路**: 把 IIFE 作为表达式交给 Node 执行，结果用 `JSON.stringify` 回传到 Python。

**Node 侧示例**

```js
// file: iife_eval.js
let code = "";
process.stdin.on("data", chunk => code += chunk);
process.stdin.on("end", () => {
  try {
    const result = eval("(" + code + ")");
    console.log(JSON.stringify(result));
  } catch (err) {
    console.error("Error:", err);
    process.exit(1);
  }
});
```

**Python 侧**

```python
import json
import subprocess

def parse_with_node(iife: str, node_script="iife_eval.js"):
    """Parse IIFE using Node parser."""
    proc = subprocess.run(
        ["node", node_script],
        input=iife.encode("utf-8"),
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)
```

**优点**

* 语义最接近 JS 运行时，正确性强
* 对更复杂写法兼容性强

**权衡**

* 需依赖 Node
* 有进程通信开销
* 仅适用于可信输入

---

## 五、方案三: 栈解析器版 (Tokenizer + Recursive Descent)

> 说明：编译原理相关的课是 3 年前学的，可能有遗忘或疏漏，此处仅借鉴部分流程并作了精简与修改。

**思路**

1. **词法分析 (Tokenization)**: 把对象文本切成 token (字符串、`{ } [ ] : ,`、标识符/数字等)，跳过注释
2. **语法分析 (Parsing)**: 递归下降解析对象/数组结构
3. **语义还原**:
   * 标识符若命中 `mapping`，替换为对应 Python 值
   * 字面量通过 `parse_js_token` 转为 Python 类型

<details>
<summary>核心片段 (点击展开)</summary>

```python
import json
import re
from typing import Any

IIFE_RE = re.compile(
    r'^\(function\((.*?)\)\s*\{\s*return\s*({.*?})\s*\}\s*\((.*?)\)\)$',
    re.S,
)

INT_RE = re.compile(r'[+-]?\d+')
FLOAT_RE = re.compile(r'^[+-]?(?:\d+\.\d*|\.\d+)(?:[eE][+-]?\d+)?$|^[+-]?\d+[eE][+-]?\d+$')

def parse_js_string(s: str) -> str:
    if not (s and s[0] == s[-1] and s[0] in ("'", '"')):
        raise ValueError(f"Invalid JS string literal: {s!r}")

    body = s[1:-1]
    if "\\" not in body:
        return body

    out = []
    it = iter(body)
    for ch in it:
        if ch != '\\':
            out.append(ch)
            continue

        try:
            esc = next(it)
        except StopIteration:
            break

        if esc in "'\"\\":
            out.append(esc)
        elif esc == 'n':
            out.append('\n')
        elif esc == 'r':
            out.append('\r')
        elif esc == 't':
            out.append('\t')
        elif esc == 'b':
            out.append('\b')
        elif esc == 'f':
            out.append('\f')
        elif esc == 'v':
            out.append('\v')
        elif esc == '0':
            out.append('\0')
        elif esc == 'x':
            hex2 = ''.join(next(it) for _ in range(2))
            out.append(chr(int(hex2, 16)))
        elif esc == 'u':
            hex4 = ''.join(next(it) for _ in range(4))
            out.append(chr(int(hex4, 16)))
        else:
            out.append(esc)  # 宽松处理未知转义

    return ''.join(out)

def parse_js_token(tok: str) -> Any:
    tok = tok.strip()
    match tok:
        case "null" | "undefined":
            return None
        case "true":
            return True
        case "false":
            return False
        case _ if INT_RE.fullmatch(tok):
            return int(tok)
        case _ if FLOAT_RE.fullmatch(tok):
            return float(tok)
        case _ if tok.startswith("'") and tok.endswith("'"):
            return parse_js_string(tok)
        case _ if tok.startswith('"') and tok.endswith('"'):
            return parse_js_string(tok)
        case _:
            return tok  # 标识符等

def split_args(s: str) -> list[str]:
    out = []
    buf = []
    stack = []

    it = iter(s)
    in_str = False
    esc = False
    quote = ''

    for ch in it:
        if in_str:
            buf.append(ch)
            if esc:
                esc = False
            elif ch == '\\':
                esc = True
            elif ch == quote:
                in_str = False
            continue

        if ch in ('"', "'"):
            in_str = True
            quote = ch
            buf.append(ch)
            continue

        if ch in '{[(':
            stack.append(ch)
            buf.append(ch)
            continue

        if ch in '}])':
            if stack:
                stack.pop()
            buf.append(ch)
            continue

        if ch == ',' and not stack:
            item = ''.join(buf).strip()
            if item:
                out.append(item)
            buf.clear()
            continue

        buf.append(ch)

    tail = ''.join(buf).strip()
    if tail:
        out.append(tail)

    return out

def tokenize_object(src: str) -> list[str]:
    toks = []
    i, n = 0, len(src)
    while i < n:
        ch = src[i]

        # skip space
        if ch in " \t\r\n":
            i += 1
            continue

        # string
        if ch in ("'", '"'):
            quote = ch
            j = i + 1
            esc = False
            while j < n:
                c = src[j]
                if esc:
                    esc = False
                elif c == "\\":
                    esc = True
                elif c == quote:
                    j += 1
                    break
                j += 1
            toks.append(src[i:j])
            i = j
            continue

        # comment
        if ch == '/' and i + 1 < n and src[i+1] in '/*':
            if src[i+1] == '/':
                i += 2
                while i < n and src[i] not in '\r\n':
                    i += 1
            else:
                i += 2
                while i + 1 < n and not (src[i] == '*' and src[i+1] == '/'):
                    i += 1
                i += 2
            continue

        # punctuation
        if ch in "{}[]:,":
            toks.append(ch)
            i += 1
            continue

        # identifier / number
        j = i
        while j < n and src[j] not in " \t\r\n{}[]:,":
            j += 1
        toks.append(src[i:j])
        i = j

    return toks

def parse_js_value(tokens: list[str], idx: int, mapping: dict[str, Any]) -> tuple[Any, int]:
    tok = tokens[idx]

    if tok == "{":
        obj = {}
        idx += 1
        while tokens[idx] != "}":
            key = tokens[idx]
            if key[0] in ('"', "'"):
                key = parse_js_string(key)
            idx += 1
            if tokens[idx] != ":":
                raise ValueError(f"Expected :, got {tokens[idx]}")
            idx += 1
            val, idx = parse_js_value(tokens, idx, mapping)
            obj[key] = val
            if tokens[idx] == ",":
                idx += 1
        return obj, idx + 1

    if tok == "[":
        arr = []
        idx += 1
        while tokens[idx] != "]":
            val, idx = parse_js_value(tokens, idx, mapping)
            arr.append(val)
            if tokens[idx] == ",":
                idx += 1
        return arr, idx + 1

    if tok in mapping:
        return mapping[tok], idx + 1

    return parse_js_token(tok), idx + 1

def parse_iife_direct(iife: str) -> dict[str, Any]:
    m = IIFE_RE.match(iife.strip())
    if not m:
        raise ValueError("Invalid IIFE format")

    params_str, obj_str, args_str = m.groups()

    params = [p.strip() for p in split_args(params_str)]
    args = [a.strip() for a in split_args(args_str)]

    if len(params) != len(args):
        raise ValueError("Param/arg length mismatch")

    mapping = {p: parse_js_token(a) for p, a in zip(params, args)}

    tokens = tokenize_object(obj_str)
    result, _ = parse_js_value(tokens, 0, mapping)
    return result
```

</details>

**优点**

* 纯 Python，无子进程开销
* 在“受限语法”下**更稳更快**，对大对象表现优于字符串替换版

**局限**

* 语法覆盖面有限，需要维护词法/语法正确性
* 若输入超出受限语法，需要回退其他方案

---

## 六、性能分析

> 以下为实际测量结果，三种方案分别在不同体量的 IIFE 表达式上取平均耗时 (单位: 毫秒)。
>
> 分组标准:
>
> * **小表达式** ≤ 50,000 chars (n=6)
> * **大表达式** ≥ 120,000 chars (n=4)

**分组均值**

| 组别                 | Python 字符串替换版 | Python 栈解析器 |  Node 子进程 |
| -------------------- | ----------------: | --------------: | ----------: |
| 小表达式 (≤50k, n=6)  | **13.49**         | **7.63**        | **82.11**   |
| 大表达式 (≥120k, n=4) | **165.98**        | **49.89**       | **90.19**   |

**放大倍数 (大/小)**

* **Python 字符串替换版**: 约 **12.3×**
* **Python 栈解析器**: 约 **6.5×**
* **Node 子进程**: 约 **1.1×**

**观察**

* **Python 栈解析器**的增长率较为平缓: 大文件耗时约为小文件的 6.5 倍，明显优于正则法。
* **Python 字符串替换版** 虽然实现直观，但随体量增加耗时迅速攀升 (约 12 倍)，在大表达式场景下不够稳定。
* **Node 子进程**存在固定的基线开销 (约 80 ms)，但随体量增加几乎不变，适合作为高兼容性兜底方案。

---

## 七、备注

上述正则 `IIFE_RE` 为工程化启发式，若页面存在**更稳定的边界** (例如特定变量赋值、明确的 `<script>` 包裹)，建议结合上下文加以收紧，以提升定位与健壮性。
