# Copyright (c) 2026 AGENTFlow Contributors
# SPDX-License-Identifier: MIT
"""Abstract connector interfaces for AGENTFlow."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseConnector(ABC):
    """Base class for external resource connectors."""

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @abstractmethod
    def resolve(self, value: str) -> Any:
        """Resolve an external reference into a normalized local object."""

    def close(self) -> None:
        """Optional lifecycle hook for future connectors."""
        return None
