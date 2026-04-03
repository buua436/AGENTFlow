# Copyright (c) 2026 AGENTFlow Contributors
# SPDX-License-Identifier: MIT
"""Connector integrations for AGENTFlow."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

from .base import BaseConnector

if TYPE_CHECKING:
    from .arxiv_connector import (
        ArxivConnector,
        ArxivConnectorError,
        ArxivNetworkError,
        ArxivPaper,
        ArxivParseError,
        ArxivQueryError,
        ArxivRateLimitError,
        ArxivSearchPage,
        ArxivSearchResult,
        ArxivTimeoutError,
    )


__all__ = [
    "BaseConnector",
    "ArxivConnector",
    "ArxivConnectorError",
    "ArxivNetworkError",
    "ArxivPaper",
    "ArxivParseError",
    "ArxivQueryError",
    "ArxivRateLimitError",
    "ArxivSearchPage",
    "ArxivSearchResult",
    "ArxivTimeoutError",
]


def __getattr__(name: str) -> Any:
    if name not in __all__:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    if name == "BaseConnector":
        return BaseConnector

    module = import_module(".arxiv_connector", __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(__all__)
