# Copyright (c) 2026 AGENTFlow Contributors
# SPDX-License-Identifier: MIT
"""AGENTFlow package."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

__version__ = "0.1.0"

if TYPE_CHECKING:
    from .connectors import (
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
        BaseConnector,
    )
    from .llms import BaseLLMClient, LiteLLMClient, LiteLLMConfig, LiteLLMResponse, Message
    from .parsers import BaseParser, MinerUConfig, MinerUParseResult, MinerUParser, StatusCallback


_EXPORTS = {
    "BaseConnector": (".connectors", "BaseConnector"),
    "ArxivConnector": (".connectors", "ArxivConnector"),
    "ArxivConnectorError": (".connectors", "ArxivConnectorError"),
    "ArxivNetworkError": (".connectors", "ArxivNetworkError"),
    "ArxivPaper": (".connectors", "ArxivPaper"),
    "ArxivParseError": (".connectors", "ArxivParseError"),
    "ArxivQueryError": (".connectors", "ArxivQueryError"),
    "ArxivRateLimitError": (".connectors", "ArxivRateLimitError"),
    "ArxivSearchPage": (".connectors", "ArxivSearchPage"),
    "ArxivSearchResult": (".connectors", "ArxivSearchResult"),
    "ArxivTimeoutError": (".connectors", "ArxivTimeoutError"),
    "BaseLLMClient": (".llms", "BaseLLMClient"),
    "Message": (".llms", "Message"),
    "LiteLLMClient": (".llms", "LiteLLMClient"),
    "LiteLLMConfig": (".llms", "LiteLLMConfig"),
    "LiteLLMResponse": (".llms", "LiteLLMResponse"),
    "BaseParser": (".parsers", "BaseParser"),
    "StatusCallback": (".parsers", "StatusCallback"),
    "MinerUConfig": (".parsers", "MinerUConfig"),
    "MinerUParseResult": (".parsers", "MinerUParseResult"),
    "MinerUParser": (".parsers", "MinerUParser"),
}

__all__ = [*list(_EXPORTS), "__version__"]


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module_name, attr_name = _EXPORTS[name]
    module = import_module(module_name, __name__)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(__all__)
