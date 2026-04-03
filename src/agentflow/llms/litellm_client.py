# Copyright (c) 2026 AGENTFlow Contributors
# SPDX-License-Identifier: MIT
"""A small LiteLLM wrapper with a stable interface for AGENTFlow."""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from agentflow.llms.base import BaseLLMClient, Message
else:
    from .base import BaseLLMClient, Message


@dataclass(slots=True)
class LiteLLMConfig:
    """Default runtime configuration for LiteLLM requests."""

    model: str
    api_key: str | None = None
    base_url: str | None = None
    timeout: float | None = 60.0
    temperature: float | None = None
    max_tokens: int | None = None
    extra_kwargs: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class LiteLLMResponse:
    """Normalized response returned by the wrapper."""

    model: str | None
    content: str
    usage: dict[str, int] | None
    finish_reason: str | None
    raw: Any


class LiteLLMError(RuntimeError):
    """Raised when a LiteLLM request fails."""


class LiteLLMClient(BaseLLMClient):
    """Thin client around LiteLLM chat completion APIs."""

    def __init__(self, config: LiteLLMConfig) -> None:
        self.config = config

    def complete(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LiteLLMResponse:
        litellm = self._import_litellm()
        payload = self._build_payload(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            kwargs=kwargs,
        )
        try:
            response = litellm.completion(**payload)
        except Exception as exc:
            raise LiteLLMError(str(exc)) from exc
        return self._normalize_response(response)

    async def acomplete(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LiteLLMResponse:
        litellm = self._import_litellm()
        payload = self._build_payload(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            kwargs=kwargs,
        )
        try:
            response = await litellm.acompletion(**payload)
        except Exception as exc:
            raise LiteLLMError(str(exc)) from exc
        return self._normalize_response(response)

    def prompt(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> LiteLLMResponse:
        messages: list[Message] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return self.complete(messages, **kwargs)

    def _build_payload(
        self,
        *,
        messages: list[Message],
        model: str | None,
        temperature: float | None,
        max_tokens: int | None,
        kwargs: dict[str, Any],
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": model or self.config.model,
            "messages": messages,
        }
        if self.config.api_key is not None:
            payload["api_key"] = self.config.api_key
        if self.config.base_url is not None:
            payload["base_url"] = self.config.base_url
        if self.config.timeout is not None:
            payload["timeout"] = self.config.timeout

        effective_temperature = temperature if temperature is not None else self.config.temperature
        if effective_temperature is not None:
            payload["temperature"] = effective_temperature

        effective_max_tokens = max_tokens if max_tokens is not None else self.config.max_tokens
        if effective_max_tokens is not None:
            payload["max_tokens"] = effective_max_tokens

        payload.update(self.config.extra_kwargs)
        payload.update(kwargs)
        return payload

    def _normalize_response(self, response: Any) -> LiteLLMResponse:
        choice = self._first_choice(response)
        message = getattr(choice, "message", None)
        content = self._extract_content(message)
        usage = self._extract_usage(response)
        finish_reason = getattr(choice, "finish_reason", None)
        model = getattr(response, "model", None)
        return LiteLLMResponse(
            model=model,
            content=content,
            usage=usage,
            finish_reason=finish_reason,
            raw=response,
        )

    @staticmethod
    def _first_choice(response: Any) -> Any:
        choices = getattr(response, "choices", None)
        if not choices:
            raise LiteLLMError("LiteLLM response did not contain any choices.")
        return choices[0]

    @staticmethod
    def _extract_content(message: Any) -> str:
        if message is None:
            return ""
        content = getattr(message, "content", "")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, dict):
                    text = item.get("text")
                    if isinstance(text, str):
                        parts.append(text)
                else:
                    text = getattr(item, "text", None)
                    if isinstance(text, str):
                        parts.append(text)
            return "".join(parts)
        return str(content)

    @staticmethod
    def _extract_usage(response: Any) -> dict[str, int] | None:
        usage = getattr(response, "usage", None)
        if usage is None:
            return None
        keys = ("prompt_tokens", "completion_tokens", "total_tokens")
        data: dict[str, int] = {}
        for key in keys:
            value = getattr(usage, key, None)
            if isinstance(value, int):
                data[key] = value
        return data or None

    @staticmethod
    def _import_litellm() -> Any:
        try:
            import litellm
        except ModuleNotFoundError as exc:
            raise ModuleNotFoundError(
                "LiteLLM support requires the optional dependency `litellm`. "
                "Install it with `pip install \"agentflow[llms]\"`."
            ) from exc
        return litellm


def _main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", default="Reply with exactly one short sentence: LiteLLM is working.")
    parser.add_argument("--system-prompt", default="You are a concise test assistant.")
    parser.add_argument("--model", default=os.getenv("AGENTFLOW_MODEL", "gpt-4o-mini"))
    parser.add_argument("--base-url", default=os.getenv("OPENAI_BASE_URL") or os.getenv("AGENTFLOW_BASE_URL"))
    parser.add_argument("--temperature", type=float, default=0.0)
    args = parser.parse_args()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("Missing OPENAI_API_KEY")

    client = LiteLLMClient(
        LiteLLMConfig(
            model=args.model,
            api_key=api_key,
            base_url=args.base_url,
            timeout=60,
        )
    )

    response = client.prompt(
        args.prompt,
        system_prompt=args.system_prompt,
        temperature=args.temperature,
    )

    print("model:", response.model)
    print("finish_reason:", response.finish_reason)
    print("usage:", response.usage)
    print("content:", response.content)


if __name__ == "__main__":
    _main()
