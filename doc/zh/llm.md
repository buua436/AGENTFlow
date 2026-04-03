# LLM 设计与使用说明

## 角色定位

LLM 层负责统一封装模型调用能力。

它不应该只解决一次简单 completion，而应该逐步支持完整的 agent 开发生命周期。

当前实现只有一个：`litellm_client`。

## 建议的抽象父类

长期建议增加统一抽象，例如 `BaseLLM`，定义：

- `complete(messages, **kwargs)`
标准消息补全

- `acomplete(messages, **kwargs)`
异步补全

- `prompt(text, system_prompt=None, **kwargs)`
简化文本调用

未来还建议扩展：

- `stream(...)`
流式输出

- `tool_call(...)`
工具调用统一接口

- `structured_output(...)`
结构化输出模式

- `batch(...)`
批量调用

- `embed(...)`
嵌入接口

## 当前实现：LiteLLMClient

`LiteLLMClient` 当前是一个较薄的包装层，目标是让上层代码不直接依赖 LiteLLM 的原始返回结构。

### 配置对象

`LiteLLMConfig` 当前支持：

- `model`
- `api_key`
- `base_url`
- `timeout`
- `temperature`
- `max_tokens`
- `extra_kwargs`

### 主要接口

- `complete(messages, ...)`
同步消息补全

- `acomplete(messages, ...)`
异步消息补全

- `prompt(prompt, system_prompt=None, ...)`
简化单轮调用

### 返回对象

`LiteLLMResponse` 当前统一了：

- `model`
- `content`
- `usage`
- `finish_reason`
- `raw`

### 错误类型

- `LiteLLMError`

## 使用示例

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

## 面向 Agent 全周期的设计目标

LLM 层未来不应只提供“补全”这一种能力，而应逐步覆盖 agent 全周期中的模型交互需求。

建议分阶段演进：

### 第一阶段：基础模型调用

- completion
- async completion
- prompt helper
- 标准化 usage / finish_reason / raw

### 第二阶段：工程可用性

- 重试机制
- fallback 模型路由
- 超时控制
- 并发控制
- 统一异常层
- 统一 provider 配置

### 第三阶段：Agent 运行能力

- 工具调用
- 结构化输出
- 长上下文切片策略
- 会话状态管理
- 记忆读写接口
- 提示模板系统

### 第四阶段：完整 Agent 开发支持

- planning / reasoning 接口约定
- workflow / step executor 集成
- tracing / cost / token accounting
- evaluation hooks
- simulation / replay / test harness

## 后续扩展建议

LLM 层未来可以继续增加：

- `OpenAIClient`
- `AnthropicClient`
- `QwenClient`
- `DeepSeekClient`
- `RouterLLM`
- `CachedLLM`
- `ToolCallingLLM`

## 对 Agent 开发的意义

LLM 层是 agent 系统的“决策核心”，但它不应该单独存在。

一个成熟的 agent 工具库通常需要：

1. Connector 提供资源入口
2. Parser 提供结构化上下文
3. LLM 提供推理、生成、工具调用与决策能力

AGENTFlow 当前的 `llm` 层已经有一个可用起点，但未来目标应该是支撑整个 agent 开发周期，而不是只包一层 LiteLLM completion。
