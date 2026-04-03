# Copyright (c) 2026 AGENTFlow Contributors
# SPDX-License-Identifier: MIT
"""Abstract LLM interfaces for AGENTFlow."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


Message = dict[str, Any]


class BaseLLMClient(ABC):
    """Base class for chat-oriented LLM clients."""

    @abstractmethod
    def complete(self, messages: list[Message], **kwargs: Any) -> Any:
        """Run a synchronous completion request."""

    @abstractmethod
    async def acomplete(self, messages: list[Message], **kwargs: Any) -> Any:
        """Run an asynchronous completion request."""

    def prompt(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> Any:
        messages: list[Message] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return self.complete(messages, **kwargs)
