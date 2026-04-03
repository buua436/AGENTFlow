# Copyright (c) 2026 AGENTFlow Contributors
# SPDX-License-Identifier: MIT
"""Abstract parser interfaces for AGENTFlow."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable


StatusCallback = Callable[[str], Any]


class BaseParser(ABC):
    """Base class for document parsers."""

    @abstractmethod
    def parse_file(self, file_path: str, **kwargs: Any) -> Any:
        """Synchronously parse a file path."""

    @abstractmethod
    async def aparse_file(self, file_path: str, **kwargs: Any) -> Any:
        """Asynchronously parse a file path."""

    @abstractmethod
    def parse_bytes(self, file_bytes: bytes, **kwargs: Any) -> Any:
        """Synchronously parse raw bytes."""

    @abstractmethod
    async def aparse_bytes(self, file_bytes: bytes, **kwargs: Any) -> Any:
        """Asynchronously parse raw bytes."""

    def stop(self) -> None:
        """Optional lifecycle hook for parsers with background resources."""
        return None
