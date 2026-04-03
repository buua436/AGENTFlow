# Connector 设计与使用说明

## 角色定位

Connector 层负责把外部信息源接入到 AGENTFlow。

它的目标不是“解析内容”，而是“发现、定位、获取资源”。

典型职责包括：

- 规范化外部资源标识
- 查询外部索引或搜索接口
- 下载原始资源
- 返回统一的数据结构

当前实现只有一个：`arxiv_connector`。

## 建议的抽象父类

长期建议增加统一抽象，例如 `BaseConnector`，定义这类通用能力：

- `resolve(value)`
把任意外部标识标准化成统一资源对象

- `search(query, **kwargs)`
根据查询条件返回搜索结果列表

- `fetch(...)` 或 `download(...)`
获取原始资源并返回本地路径或字节流

抽象层重点不在于强行统一所有供应商，而在于统一使用方式和错误语义。

## 当前实现：ArxivConnector

当前 `ArxivConnector` 提供：

- `resolve(value)`
支持 arXiv id、abs URL、pdf URL 的规范化

- `get_pdf_url(value)`
快速得到 PDF 下载地址

- `search(query, max_results=10, start=0)`
通过 arXiv Atom API 搜索论文

- `download_pdf(value, output_path=None, overwrite=False)`
下载 PDF 到本地

### 返回类型

- `ArxivPaper`
表示单篇论文的标准化引用

- `ArxivSearchResult`
表示搜索结果中的单个条目

- `ArxivConnectorError`
表示规范化、搜索或下载过程中的错误

## 使用示例

### 解析 arXiv 标识

```python
from agentflow import ArxivConnector

connector = ArxivConnector()
paper = connector.resolve("1706.03762")
print(paper.abs_url)
print(paper.pdf_url)
```

### 搜索论文

```python
from agentflow import ArxivConnector

connector = ArxivConnector()
results = connector.search("vision transformer", max_results=3)
for item in results:
    print(item.arxiv_id, item.title)
```

### 下载 PDF

```python
from agentflow import ArxivConnector

connector = ArxivConnector()
path = connector.download_pdf("1706.03762", output_path="output/attention.pdf", overwrite=True)
print(path)
```

## 当前设计的优点

- 依赖轻，基础包即可使用
- 输入兼容 id 和 URL
- 输出数据结构清晰
- 很适合在 agent 中作为“论文检索入口”使用

## 后续扩展建议

Connector 层未来可以继续扩展：

- `WebConnector`
网页抓取与页面资源定位

- `GithubConnector`
代码仓库、Issue、PR、Release 信息获取

- `FilesystemConnector`
本地文档、目录、批量文件发现

- `DatabaseConnector`
向量库、关系型数据库、文档数据库的统一访问

## 对 Agent 开发的意义

Connector 层属于 agent 的“感知入口”。

在完整 agent 系统中，它通常先于 Parser 和 LLM：

1. Connector 找到资源
2. Parser 解析资源
3. LLM 使用解析后的结构化内容进行推理
