"""Shared utility helpers for the API layer."""

from __future__ import annotations

from pathlib import Path

__all__ = ["validate_resource_id"]


def validate_resource_id(id_str: str) -> None:
    """Raise ValueError if *id_str* contains path separators or traversal sequences.

    Prevents path-traversal attacks like ``../etc/passwd`` being used as IDs.
    """
    if id_str != Path(id_str).name:
        raise ValueError(f"Некорректный идентификатор: {id_str!r}")
