# Parser Design And Usage

## Role

The Parser layer converts raw input files or raw bytes into structured outputs.

Its job is not to find resources, but to transform already available input into representations that can be consumed by downstream agent logic.

Typical responsibilities include:

- reading local files or in-memory bytes
- calling a parsing backend
- producing markdown, json, content lists, and related artifacts
- exposing a stable Python-friendly result object

There is currently one implementation: `mineru_parser`.

## Recommended Base Abstraction

In the long run, AGENTFlow should introduce a shared abstraction such as `BaseParser` with methods like:

- `parse_file(path, **kwargs)`
- `parse_bytes(data, file_name=..., **kwargs)`
- `aparse_file(...)`
- `aparse_bytes(...)`

The abstraction goal is to unify:

- file-based input
- in-memory input
- sync and async entrypoints
- normalized result models and errors

## Current Implementation: MinerUParser

`MinerUParser` is currently a direct local wrapper around MinerU. It no longer depends on starting a temporary local API service first.

### Main Methods

- `parse_file(...)`
synchronous local file parsing

- `aparse_file(...)`
asynchronous local file parsing

- `parse_bytes(...)`
synchronous parsing from bytes

- `aparse_bytes(...)`
asynchronous parsing from bytes

### Configuration

`MinerUConfig` currently controls:

- `backend`
- `parse_method`
- `lang_list`
- `formula_enable`
- `table_enable`
- `server_url`
- page range options
- output toggles

### Result Object

`MinerUParseResult` currently exposes:

- `output_dir`
- `parse_dir`
- `markdown_files`
- `middle_json_files`
- `content_list_files`
- `content_list_v2_files`
- `model_output_files`
- `original_files`
- convenience properties such as `markdown_file`

### Error Type

- `MinerUError`

## Usage Examples

### Parse a local PDF

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

### Parse from bytes

```python
from pathlib import Path

from agentflow import MinerUParser

parser = MinerUParser()
pdf_bytes = Path("example.pdf").read_bytes()
result = parser.parse_bytes(pdf_bytes, file_name="example.pdf")
print(result.middle_json_file)
```

## Why This Layer Matters

The Parser layer is the structure-building stage in an agent workflow.

A common sequence is:

1. Connector obtains the source material
2. Parser converts it into structured output
3. LLM consumes the structured output for reasoning, summarization, QA, or tool decisions

## Future Extension Ideas

Possible future parser implementations include:

- `PDFParser`
- `OfficeParser`
- `HTMLParser`
- `ImageParser`
