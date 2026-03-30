from __future__ import annotations

import os

from agentflow import LiteLLMClient, LiteLLMConfig


def main() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("Missing OPENAI_API_KEY")

    model = os.getenv("AGENTFLOW_MODEL", "gpt-4o-mini")
    base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("AGENTFLOW_BASE_URL")

    client = LiteLLMClient(
        LiteLLMConfig(
            model=model,
            api_key=api_key,
            base_url=base_url,
            timeout=60,
        )
    )

    response = client.prompt(
        "Reply with exactly one short sentence: LiteLLM is working.",
        system_prompt="You are a concise test assistant.",
        temperature=0,
    )

    print("model:", response.model)
    print("finish_reason:", response.finish_reason)
    print("usage:", response.usage)
    print("content:", response.content)


if __name__ == "__main__":
    main()
