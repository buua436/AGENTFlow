# Copyright (c) 2026 AGENTFlow Contributors
# SPDX-License-Identifier: MIT
"""Parser integrations for AGENTFlow."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

from .base import BaseParser, StatusCallback

if TYPE_CHECKING:
    from .mineru_parser import MinerUConfig, MinerUParseResult, MinerUParser


__all__ = ["BaseParser", "StatusCallback", "MinerUConfig", "MinerUParseResult", "MinerUParser"]


def __getattr__(name: str) -> Any:
    if name not in __all__:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    if name in {"BaseParser", "StatusCallback"}:
        return globals()[name]

    try:
        module = import_module(".mineru_parser", __name__)
    except ModuleNotFoundError as exc:
        if exc.name == "mineru":
            raise ModuleNotFoundError(
                "MinerU support requires the optional dependency `mineru`. "
                "Install it with `pip install \"agentflow[mineru]\"` or "
                "`pip install \"agentflow[mineru-pipeline]\"` for the local pipeline runtime."
            ) from exc
        raise

    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(__all__)
