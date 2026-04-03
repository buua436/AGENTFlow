# Parser 设计与使用说明

## 角色定位

Parser 层负责把原始文件或原始内容转换成结构化结果。

它的目标不是查找资源，而是把已有输入解析成后续 agent 可以消费的中间表示。

典型职责包括：

- 读取原始文档或字节流
- 调用具体解析引擎
- 输出 Markdown、JSON、内容列表等结构化结果
- 提供统一的数据模型与结果对象

当前实现只有一个：`mineru_parser`。

## 建议的抽象父类

长期建议增加统一抽象，例如 `BaseParser`，定义：

- `parse_file(path, **kwargs)`
解析本地文件

- `parse_bytes(data, file_name=..., **kwargs)`
解析内存字节流

- `aparse_file(...)` / `aparse_bytes(...)`
异步接口

- 统一的结果对象与错误类型

Parser 层的抽象重点在于：

- 输入源统一
- 输出结果统一
- 同步 / 异步调用方式统一

## 当前实现：MinerUParser

当前 `MinerUParser` 是对 MinerU 的本地直调封装，不再通过临时 API 服务转发。

主要能力包括：

- `parse_file(...)`
同步解析本地文件

- `aparse_file(...)`
异步解析本地文件

- `parse_bytes(...)`
同步解析字节流

- `aparse_bytes(...)`
异步解析字节流

### 配置对象

`MinerUConfig` 当前主要控制：

- `backend`
- `parse_method`
- `lang_list`
- `formula_enable`
- `table_enable`
- `server_url`
- 页码范围
- 输出内容开关

### 返回对象

`MinerUParseResult` 当前提供：

- `output_dir`
- `parse_dir`
- `markdown_files`
- `middle_json_files`
- `content_list_files`
- `content_list_v2_files`
- `model_output_files`
- `original_files`
- 若干便捷属性，如 `markdown_file`

### 错误类型

- `MinerUError`

## 使用示例

### 解析本地 PDF

```python
from agentflow import MinerUConfig, MinerUParser

parser = MinerUParser(
    MinerUConfig(
        backend="pipeline",
        parse_method="auto",
        lang_list=("ch",),
    )
)

result = parser.parse_file("example.pdf")
print(result.parse_dir)
print(result.markdown_file)
```

### 解析字节流

```python
from pathlib import Path

from agentflow import MinerUParser

parser = MinerUParser()
pdf_bytes = Path("example.pdf").read_bytes()
result = parser.parse_bytes(pdf_bytes, file_name="example.pdf")
print(result.middle_json_file)
```

## 当前设计的优点

- 直接本地解析，避免额外服务启动开销
- 同时支持文件和字节流输入
- 结果对象比底层返回更适合作为 Python 库使用
- 适合在 agent 的文档理解流程中作为标准解析入口

## 后续扩展建议

Parser 层未来可以增加：

- `PDFParser`
更轻量的文本型 PDF 提取器

- `OfficeParser`
Word / PPT / Excel 的统一封装

- `HTMLParser`
网页内容、DOM 和主文本抽取

- `ImageParser`
OCR 与版面分析抽象

## 对 Agent 开发的意义

Parser 层属于 agent 的“理解准备层”。

典型链路如下：

1. Connector 获取文件
2. Parser 输出结构化内容
3. LLM 以结构化内容为上下文继续推理、问答、总结或工具调用
