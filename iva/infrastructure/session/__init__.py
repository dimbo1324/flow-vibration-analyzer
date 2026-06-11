"""Session persistence package for the Industrial Vibration Analyzer.

Public API:
- :func:`save_project` — save an :class:`AnalysisSession` to a ``.vibproj`` JSON file.
- :func:`load_project` — load an :class:`AnalysisSession` from a ``.vibproj`` file.
- :func:`analysis_result_to_dict` — serialise an :class:`AnalysisResult` to a plain dict.
- :func:`analysis_result_from_dict` — deserialise an :class:`AnalysisResult` from a dict.
"""

from __future__ import annotations

from iva.infrastructure.session.session_serializer import (
    VIBPROJ_SCHEMA_VERSION,
    analysis_result_from_dict,
    analysis_result_to_dict,
)
from iva.infrastructure.session.session_store import load_project, save_project

__all__ = [
    "save_project",
    "load_project",
    "analysis_result_to_dict",
    "analysis_result_from_dict",
    "VIBPROJ_SCHEMA_VERSION",
]
