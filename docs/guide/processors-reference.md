## processors 配置

在导出前按顺序执行的文本处理阶段列表。

典型用途: **正则清理**、**繁简转换 (OpenCC)**、**文本纠错 (pycorrector)**、**文本翻译 (translate)** 等。

> **所有处理器均为可选**; 未配置或列表为空时, 不执行文本处理。

### 内置处理器概览 (简要)

#### `cleaner`

用于移除不可见字符、删除不需要的文本片段、进行字面替换 (可作用于标题与正文)。

| 参数名             | 类型    | 默认值   | 说明                                               |
| ------------------ | ------ | ----- | ------------------------------------------------ |
| `remove_invisible` | `bool` | true  | 移除常见不可见字符 (如零宽字符等)                       |
| `title_removes`    | `str`  | -     | **可选**; JSON 文件路径, 内容为**字符串数组** (正则), 逐条删除           |
| `title_replace`    | `str`  | -     | **可选**; JSON 文件路径, 内容为**字典** (`{"old": "new"}`) 逐条替换 |
| `content_removes`  | `str`  | -     | 同上, 作用于正文                                         |
| `content_replace`  | `str`  | -     | 同上, 作用于正文                                         |
| `overwrite`        | `bool` | false | 若同名阶段已存在, 是否强制重建                                  |

> `*_removes`: JSON 数组; `*_replace`: JSON 对象。

**示例**

假设配置中写入:

```toml
[[general.processors]]
name = "cleaner"
remove_invisible = true
title_removes = "title-remove.json"
content_replace = "content-replace.json"
```

则需要在相同目录下创建对应 JSON 文件:

**title-remove.json**

```json
[
  "\\[广告\\]",
  "\\(无弹窗小说网\\)",
  "PS：.*$"
]
```

**content-replace.json**

```json
{
  "请记住本书首发网址": "",
  "(本章完)": "",
  "li子": "例子",
  "pinbi词": "屏蔽词"
}
```

#### `zh_convert`

进行简繁体转换, 基于 **OpenCC**。

| 参数名           | 类型     | 默认值   | 说明            |
| --------------- | -------- | ------- | --------------- |
| `direction`     | `str`    | `t2s`   | 转换方向 (见下)  |
| `apply_title`   | `bool`   | true    | 是否作用于标题   |
| `apply_content` | `bool`   | true    | 是否作用于正文   |
| `overwrite`     | `bool`   | false   | 是否强制重建     |

**可选转换方向** (`direction`):

| 简写      | 含义                   |
| ------- | -------------------- |
| `hk2s`  | 繁体 (香港标准)  -> 简体        |
| `s2hk`  | 简体 -> 繁体 (香港标准)         |
| `s2t`   | 简体 -> 繁体              |
| `s2tw`  | 简体 -> 繁体 (台湾标准)         |
| `s2twp` | 简体 -> 繁体 (台湾标准，带词汇转换)   |
| `t2hk`  | 繁体 -> 繁体 (香港标准)         |
| `t2s`   | 繁体 -> 简体              |
| `t2tw`  | 繁体 -> 繁体 (台湾标准)         |
| `tw2s`  | 繁体 (台湾标准)  -> 简体        |
| `tw2sp` | 繁体 (台湾标准)  -> 简体 (带词汇转换)  |

> 更多方向及说明见:
> [OpenCC 官方文档](https://github.com/yichen0831/opencc-python?tab=readme-ov-file#conversions-%E8%BD%89%E6%8F%9B)
>
> 依赖: `opencc-python-reimplemented`。

#### `translator.google`

| 参数名           | 类型     | 默认值   |
| --------------- | -------- | ------- |
| `source`        | `str`    | `auto`  |
| `target`        | `str`    | `zh-CN` |
| `sleep`         | `float`  | 2.0     |

??? note "支持语言列表 (点击展开)"

    --8<-- "docs/data/google_languages.md"

#### `translator.edge`

| 参数名           | 类型     | 默认值    |
| --------------- | -------- | --------- |
| `source`        | `str`    | `auto`    |
| `target`        | `str`    | `zh-Hans` |
| `sleep`         | `float`  | 1.0       |

??? note "支持语言列表 (点击展开)"

    --8<-- "docs/data/edge_languages.md"

#### `translator.youdao`

| 参数名           | 类型     | 默认值    |
| --------------- | -------- | --------- |
| `source`        | `str`    | `auto`    |
| `target`        | `str`    | `zh-CHS`  |
| `sleep`         | `float`  | 1.0       |

??? note "支持语言列表 (点击展开)"

    --8<-- "docs/data/youdao_languages.md"

#### `corrector`

中文文本纠错, 基于 [**pycorrector**](https://github.com/shibing624/pycorrector)。

可选择多种纠错引擎, 如 `kenlm`、`macbert`、`t5`、`ernie_csc`、`gpt`、`mucgec_bart` 等。

> 注意: 小说文本上纠错效果受模型影响较大, 通常不佳。

| 参数名            | 类型     | 默认值     | 说明              |
| ---------------- | -------- | --------- | --------------- |
| `engine`         | str      | `"kenlm"` | 纠错引擎类型          |
| `apply_title`    | bool     | true      | 是否作用于标题         |
| `apply_content`  | bool     | true      | 是否作用于正文         |
| `apply_author`   | bool     | false     | 是否作用于作者名        |
| `apply_tags`     | bool     | false     | 是否作用于标签         |
| `skip_if_len_le` | int|None | None      | 文本长度小于等于该值时跳过处理 |
| `overwrite`      | bool     | false     | 是否强制重建          |

> 依赖: `pycorrector` 及对应模型; 首次加载可能较慢。
>
> 各引擎的参数说明与官方文档参见下表。

**各引擎支持与参数**

| 引擎 Key          | 说明                        | 文档链接                                                                                                                                       | 额外参数                                                                                                                                   |
| --------------- | ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------- |
| **kenlm**       | 基于统计语言模型的中文纠错             | [kenlm 模型(统计模型)](https://github.com/shibing624/pycorrector?tab=readme-ov-file#kenlm%E6%A8%A1%E5%9E%8B%E7%BB%9F%E8%AE%A1%E6%A8%A1%E5%9E%8B) | `language_model_path`, `custom_confusion_path_or_dict`, `proper_name_path`, `common_char_path`, `same_pinyin_path`, `same_stroke_path` |
| **macbert**     | 基于 Transformer 的拼写纠错模型    | [MacBERT 模型](https://github.com/shibing624/pycorrector?tab=readme-ov-file#macbert4csc%E6%A8%A1%E5%9E%8B)                                   | `model_name_or_path`                                                                                                                   |
| **t5**          | T5 架构的中文纠错模型              | [T5 模型](https://github.com/shibing624/pycorrector?tab=readme-ov-file#t5%E6%A8%A1%E5%9E%8B)                                                 | `model_name_or_path`                                                                                                                   |
| **ernie_csc**   | 基于 ERNIE 的中文纠错模型          | [ErnieCSC 模型](https://github.com/shibing624/pycorrector?tab=readme-ov-file#erniecsc%E6%A8%A1%E5%9E%8B)                                     | `model_name_or_path`                                                                                                                   |
| **gpt**         | 基于 ChatGLM / Qwen 等大模型的纠错 | [GPT 模型](https://github.com/shibing624/pycorrector?tab=readme-ov-file#gpt%E6%A8%A1%E5%9E%8B)                                               | `model_name_or_path`, `model_type`, `peft_name`                                                                                        |
| **mucgec_bart** | Bart 架构的中文纠错模型            | [Bart / MuCGEC Bart 模型](https://github.com/shibing624/pycorrector?tab=readme-ov-file#bart%E6%A8%A1%E5%9E%8B)                               | `model_name_or_path`                                                                                                                   |
