# LLM Design And Usage

## Role

The LLM layer is responsible for unified model invocation.

It should not stop at a single completion helper. Over time, it should support the full agent development lifecycle.

There is currently one implementation: `litellm_client`.

## Recommended Base Abstraction

In the long run, AGENTFlow should introduce a shared abstraction such as `BaseLLM` with methods like:

- `complete(messages, **kwargs)`
- `acomplete(messages, **kwargs)`
- `prompt(text, system_prompt=None, **kwargs)`

Later extensions should also cover:

- `stream(...)`
- `tool_call(...)`
- `structured_output(...)`
- `batch(...)`
- `embed(...)`

## Current Implementation: LiteLLMClient

`LiteLLMClient` is currently a thin wrapper that shields downstream users from raw LiteLLM response structures.

### Configuration

`LiteLLMConfig` currently supports:

- `model`
- `api_key`
- `base_url`
- `timeout`
- `temperature`
- `max_tokens`
- `extra_kwargs`

### Main Methods

- `complete(messages, ...)`
synchronous message completion

- `acomplete(messages, ...)`
asynchronous message completion

- `prompt(prompt, system_prompt=None, ...)`
a convenience helper for simple text-based invocation

### Return Object

`LiteLLMResponse` currently normalizes:

- `model`
- `content`
- `usage`
- `finish_reason`
- `raw`

### Error Type

- `LiteLLMError`

## Usage Example

```python
from agentflow import LiteLLMClient, LiteLLMConfig

client = LiteLLMClient(
    LiteLLMConfig(
        model="gpt-4o-mini",
        api_key="your-api-key",
    )
)

response = client.prompt("Say hello in one sentence.")
print(response.content)
```

## Design Goal Across The Agent Lifecycle

The long-term LLM layer should cover much more than plain completion.

A practical roadmap can be thought of in stages.

### Stage 1: Core model access

- sync completion
- async completion
- prompt helper
- normalized metadata such as usage and finish reason

### Stage 2: Production usability

- retries
- fallback routing
- timeout control
- concurrency control
- provider-independent error handling
- unified configuration patterns

### Stage 3: Agent runtime support

- tool calling
- structured outputs
- long-context chunking strategies
- session-state handling
- memory read and write interfaces
- prompt templating

### Stage 4: Full agent development support

- planning / reasoning interfaces
- workflow and step executor integration
- tracing, cost tracking, token accounting
- evaluation hooks
- simulation and replay support

## Why This Layer Matters

The LLM layer is the reasoning core of an agent system, but it should not stand alone.

A mature agent library usually combines:

1. Connectors for resource access
2. Parsers for structured context generation
3. LLMs for reasoning, generation, tool calling, and decision-making

AGENTFlow already has a useful starting point in `LiteLLMClient`, but the long-term goal should be to support the full agent development cycle rather than only wrapping one completion path.

## Future Extension Ideas

Potential future implementations include:

- `OpenAIClient`
- `AnthropicClient`
- `QwenClient`
- `DeepSeekClient`
- `RouterLLM`
- `CachedLLM`
- `ToolCallingLLM`
