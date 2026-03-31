# AGENTFlow

AGENTFlow is a Python library for building agent-oriented applications with a small, composable surface area.

It currently focuses on three practical integration layers:

- `agentflow.connectors`: lightweight connectors such as arXiv
- `agentflow.llms`: stable wrappers around model gateways such as LiteLLM
- `agentflow.parsers`: document parsing wrappers such as MinerU

The project is designed to be imported from other Python projects, not only run as a local app scaffold.

## Installation

Install the base package when you only need dependency-light modules such as the arXiv connector:

```bash
pip install agentflow
```

Install optional integrations only when you need them:

```bash
pip install "agentflow[llms]"
pip install "agentflow[mineru]"
pip install "agentflow[mineru-pipeline]"
```

For local development with `uv`:

```bash
uv sync
uv sync --extra llms
uv sync --extra mineru-pipeline
```

## Why The Extras Matter

`LiteLLM` and `MinerU` are now optional dependencies. That means:

- `import agentflow` works even if `litellm` or `mineru` is not installed.
- users can install only the integrations they actually need.
- the package is better suited for publishing on PyPI as a reusable library.

If you access an optional feature without its dependency installed, AGENTFlow raises a clear installation hint.

## Quick Examples

### arXiv Connector

```python
from agentflow import ArxivConnector

connector = ArxivConnector()
paper = connector.resolve("1706.03762")
print(paper.pdf_url)
```

### LiteLLM Wrapper

```python
from agentflow import LiteLLMClient, LiteLLMConfig

client = LiteLLMClient(
    LiteLLMConfig(
        model="gpt-4o-mini",
        api_key="your-api-key",
    )
)

response = client.prompt("Say hello in one short sentence.")
print(response.content)
```

### MinerU Local Parsing

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

### MinerU Parsing From Bytes

```python
from pathlib import Path

from agentflow import MinerUParser

parser = MinerUParser()
pdf_bytes = Path("example.pdf").read_bytes()
result = parser.parse_bytes(pdf_bytes, file_name="example.pdf")
print(result.middle_json_file)
```

## Local Test Entrypoints

Minimal test scripts live next to the modules they exercise:

- `src/agentflow/connectors/test_arxiv_connector_minimal.py`
- `src/agentflow/llms/test_litellm_minimal.py`
- `src/agentflow/parsers/test_mineru_minimal.py`

Examples:

```bash
python src/agentflow/connectors/test_arxiv_connector_minimal.py --search transformer
python src/agentflow/parsers/test_mineru_minimal.py your.pdf
```

## Current Notes

- `MinerUParser` now uses direct local invocation instead of spinning up a temporary `mineru-api` service.
- `MinerUParser.parse_bytes()` and `MinerUParser.aparse_bytes()` are intended to make downstream library integration easier.
- the top-level package uses lazy exports so optional integrations do not break unrelated imports.

## Packaging Notes

Before uploading to PyPI, you should still confirm:

- the package name `agentflow` is available on PyPI
- your final project license choice
- the repository/homepage URLs you want to publish in package metadata

Build commands:

```bash
python -m build
python -m twine check dist/*
python -m twine upload dist/*
```
