# AGENTFlow Documentation Index

## Purpose

These documents are not limited to describing the three current implementation files.

They describe the intended long-term design of AGENTFlow as a reusable Python library.

Core principles:

- define abstraction boundaries before implementation details
- stabilize interfaces before scaling implementations
- design for the full agent development lifecycle, not just single utility calls

The documents are organized by capability domain:

- [Connector](connector.md)
- [Parser](parser.md)
- [LLM](llm.md)

## Architecture Overview

AGENTFlow is best understood as a two-layer design.

### 1. Abstraction Layer

The abstraction layer defines stable interfaces so upper-level agent logic does not depend on a specific provider.

Each capability domain should eventually have a base abstraction such as:

- `BaseConnector`
- `BaseParser`
- `BaseLLM`

These abstractions should define:

- shared input and output models
- sync and async method boundaries
- error semantics
- observability boundaries
- configuration layout

### 2. Implementation Layer

The implementation layer provides concrete integrations, for example:

- current connector implementation: `arxiv_connector`
- current parser implementation: `mineru_parser`
- current llm implementation: `litellm_client`

Implementations can grow over time, but the abstraction layer should remain stable for downstream users.

## Recommended Package Evolution

The current package already has:

- `agentflow.connectors`
- `agentflow.parsers`
- `agentflow.llms`

Over time, each domain should ideally evolve toward:

- `base.py` or `protocols.py` for abstract interfaces
- `types.py` for shared data models
- `errors.py` for shared exception types
- one or more concrete implementation files

## Capability Map For The Agent Lifecycle

AGENTFlow should not stop at single-function wrappers.

A broader agent development lifecycle usually includes:

1. resource access
connect to knowledge sources, websites, paper indexes, files, databases

2. content parsing
turn PDFs, images, office files, or HTML into structured intermediate outputs

3. model reasoning
perform completion, chat, tool calling, structured outputs, retries, and routing

4. runtime orchestration
manage context, memory, tasks, workflows, and multi-step execution

5. delivery
produce answers, reports, indexed outputs, structured objects, and artifacts

The current `connector / parser / llm` domains are the starting point for that larger system.

## Current Status

There is only one concrete implementation per domain today, but the documentation is intentionally organized as if multiple implementations will coexist in the future.

So these docs should be read as:

- usage docs for the current API
- a design draft for future abstraction
- a guide for how downstream projects should integrate AGENTFlow
