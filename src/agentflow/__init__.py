"""AGENTFlow package."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

__version__ = "0.1.0"

if TYPE_CHECKING:
    from .connectors import ArxivConnector, ArxivConnectorError, ArxivPaper, ArxivSearchResult
    from .llms import LiteLLMClient, LiteLLMConfig, LiteLLMResponse
    from .parsers import MinerUConfig, MinerUParseResult, MinerUParser


_EXPORTS = {
    "ArxivConnector": (".connectors", "ArxivConnector"),
    "ArxivConnectorError": (".connectors", "ArxivConnectorError"),
    "ArxivPaper": (".connectors", "ArxivPaper"),
    "ArxivSearchResult": (".connectors", "ArxivSearchResult"),
    "LiteLLMClient": (".llms", "LiteLLMClient"),
    "LiteLLMConfig": (".llms", "LiteLLMConfig"),
    "LiteLLMResponse": (".llms", "LiteLLMResponse"),
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
