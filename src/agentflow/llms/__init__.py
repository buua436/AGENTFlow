# Copyright (c) 2026 AGENTFlow Contributors
# SPDX-License-Identifier: MIT
"""LLM integrations for AGENTFlow."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

from .base import BaseLLMClient, Message

if TYPE_CHECKING:
    from .litellm_client import LiteLLMClient, LiteLLMConfig, LiteLLMResponse


__all__ = ["BaseLLMClient", "Message", "LiteLLMClient", "LiteLLMConfig", "LiteLLMResponse"]


def __getattr__(name: str) -> Any:
    if name not in __all__:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    if name in {"BaseLLMClient", "Message"}:
        return globals()[name]

    try:
        module = import_module(".litellm_client", __name__)
    except ModuleNotFoundError as exc:
        if exc.name == "litellm":
            raise ModuleNotFoundError(
                "LiteLLM support requires the optional dependency `litellm`. "
                "Install it with `pip install \"agentflow[llms]\"`."
            ) from exc
        raise

    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(__all__)
