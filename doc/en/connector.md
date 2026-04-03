# Connector Design And Usage

## Role

The Connector layer is responsible for bringing external resources into AGENTFlow.

Its job is not to parse content, but to discover, normalize, and fetch resources.

Typical responsibilities include:

- normalizing external resource identifiers
- querying external search or index APIs
- downloading raw resources
- returning unified result objects

There is currently one implementation: `arxiv_connector`.

## Recommended Base Abstraction

In the long run, AGENTFlow should introduce a shared abstraction such as `BaseConnector` with methods like:

- `resolve(value)`
normalize an external identifier into a standard resource object

- `search(query, **kwargs)`
search a remote source and return normalized results

- `fetch(...)` or `download(...)`
retrieve raw content and return a local path or bytes

The main goal of the abstraction layer is not to erase all provider differences, but to make usage patterns and error semantics consistent.

## Current Implementation: ArxivConnector

`ArxivConnector` currently provides:

- `resolve(value)`
normalize an arXiv id, abs URL, or pdf URL

- `get_pdf_url(value)`
return the normalized PDF URL

- `search(query, max_results=10, start=0)`
search the arXiv Atom API

- `download_pdf(value, output_path=None, overwrite=False)`
download a PDF locally

### Return Types

- `ArxivPaper`
normalized single-paper reference

- `ArxivSearchResult`
normalized search result item

- `ArxivConnectorError`
raised when normalization, search, or download fails

## Usage Examples

### Resolve an arXiv reference

```python
from agentflow import ArxivConnector

connector = ArxivConnector()
paper = connector.resolve("1706.03762")
print(paper.abs_url)
print(paper.pdf_url)
```

### Search papers

```python
from agentflow import ArxivConnector

connector = ArxivConnector()
results = connector.search("vision transformer", max_results=3)
for item in results:
    print(item.arxiv_id, item.title)
```

### Download a PDF

```python
from agentflow import ArxivConnector

connector = ArxivConnector()
path = connector.download_pdf("1706.03762", output_path="output/attention.pdf", overwrite=True)
print(path)
```

## Why This Layer Matters

The Connector layer is the resource intake boundary for an agent system.

A typical flow is:

1. Connector finds or downloads the resource
2. Parser extracts structured content
3. LLM consumes that structured content for reasoning

## Future Extension Ideas

This layer can grow with additional implementations such as:

- `WebConnector`
- `GithubConnector`
- `FilesystemConnector`
- `DatabaseConnector`
