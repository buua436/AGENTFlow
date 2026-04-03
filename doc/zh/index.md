# AGENTFlow 文档索引

## 文档目标

这组文档不是只描述当前已有的 3 个实现文件，而是描述 AGENTFlow 作为一个 Python 工具库的整体设计方向。

核心原则：

- 先定义能力层的抽象边界，再放具体实现
- 先保证接口稳定，再允许底层实现替换
- 先面向 agent 开发全周期设计，再落地单点能力

当前文档按 3 个能力域组织：

- [Connector](connector.md)
- [Parser](parser.md)
- [LLM](llm.md)

## 项目设计总览

AGENTFlow 建议长期采用两层结构：

### 1. 抽象层

抽象层负责定义统一接口，目标是让上层 agent 逻辑不依赖某个具体供应商或具体工具。

每个能力域都应该先有父类或协议层：

- `BaseConnector`
- `BaseParser`
- `BaseLLM`

这些抽象类型负责定义：

- 输入输出的数据模型
- 同步 / 异步方法边界
- 错误类型
- 可观测性边界
- 配置对象的组织方式

### 2. 实现层

实现层负责对接真实能力提供者，例如：

- Connector 当前实现：`arxiv_connector`
- Parser 当前实现：`mineru_parser`
- LLM 当前实现：`litellm_client`

实现层可以逐步扩展，不应该破坏抽象层对上游使用者的稳定性。

## 推荐目录演进

当前项目已经有：

- `agentflow.connectors`
- `agentflow.parsers`
- `agentflow.llms`

未来建议逐步演进为：

- `base.py` 或 `protocols.py`：抽象父类 / 协议
- `types.py`：统一输入输出数据结构
- `errors.py`：统一异常类型
- 具体实现文件：例如 `arxiv_connector.py`、`mineru_parser.py`、`litellm_client.py`

## 面向 Agent 全周期的能力图

AGENTFlow 不应该只停留在“单次调用某个工具”。更完整的 agent 开发周期一般包含：

1. 信息接入
连接外部知识源、网页、论文库、数据库、文件系统

2. 内容解析
把 PDF、图片、Office 文档或网页内容解析成结构化结果

3. 模型推理
完成补全、对话、工具调用、结构化输出、重试与路由

4. 运行编排
管理上下文、记忆、任务状态、工作流与多步骤执行

5. 输出与交付
生成答复、报告、索引结果、结构化对象和工件文件

当前 AGENTFlow 的 `connector / parser / llm` 三层，是这个更大体系的起点。

## 当前状态

当前代码里只有一个具体实现对应每个能力域，但文档写法已经按“未来允许多个实现共存”的方式组织。

所以你可以把这套文档理解为：

- 当前可用 API 的使用说明
- 未来抽象化重构的设计草案
- 对外部项目集成时的稳定接口目标
