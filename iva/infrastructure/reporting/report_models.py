"""Data models for the report document structure.

These frozen dataclasses describe the logical structure of a report before
it is rendered to any specific output format (PDF, HTML, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

__all__ = [
    "ReportSection",
    "ReportTable",
    "ReportFigure",
    "ReportDocument",
]


@dataclass(frozen=True)
class ReportSection:
    """A titled text section in the report."""

    title: str
    body: str
    level: int = 1


@dataclass(frozen=True)
class ReportTable:
    """A titled table with headers and rows of strings."""

    title: str
    headers: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class ReportFigure:
    """A titled figure with an optional caption."""

    title: str
    path: Path
    caption: str = ""


@dataclass(frozen=True)
class ReportDocument:
    """The top-level report structure before rendering."""

    title: str
    subtitle: str
    generated_at: datetime
    sections: tuple[ReportSection, ...]
    tables: tuple[ReportTable, ...]
    figures: tuple[ReportFigure, ...]
    metadata: dict[str, str] = field(default_factory=dict)
