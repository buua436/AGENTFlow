# AGENTFlow

AGENTFlow is a toolkit project for building AI agents faster and more cleanly.

It focuses on wrapping and organizing the infrastructure that agent systems commonly need, so application code can stay simple and composable.

## What This Project Is For

AGENTFlow aims to provide reusable tools for agent construction, including:

- document parsing and ingestion wrappers such as MinerU
- LLM gateway and model invocation wrappers such as LiteLLM
- unified interfaces for tools, pipelines, and workflow orchestration
- building blocks for agent runtime integration

## Current Direction

The initial goal of this project is to package practical utilities around:

- `MinerU`: for document extraction, parsing, and structured content processing
- `LiteLLM`: for unified access to multiple language model providers

With these wrappers, AGENTFlow can serve as a foundation for:

- agent tool integration
- document understanding workflows
- model routing and invocation
- multi-step agent pipelines

## Planned Features

- clean Python wrappers around third-party tools
- consistent configuration management
- extensible tool abstractions for agents
- easy integration into downstream projects
- examples and starter workflows

## Status

This project is in an early stage and is currently being scaffolded.

## Development

This project uses `uv` to manage Python dependencies and the local development environment.

Common commands:

```bash
uv sync
uv add litellm
uv add mineru
uv run python -c "import agentflow; print(agentflow.__version__)"
```

Install the optional MinerU pipeline runtime dependencies with:

```bash
uv sync --extra mineru-pipeline
```

Project layout:

```text
AGENTFlow/
|- pyproject.toml
|- README.md
`- src/
   `- agentflow/
      `- __init__.py
```

## License

To be added.
