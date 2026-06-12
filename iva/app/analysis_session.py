"""Analysis session state container.

This is the single source of truth for all data related to one analysis run.
No other module may store session state — all data flows through here.

Architecture rule: this module must NOT import from ``iva.ui`` or ``PySide6``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from iva.core.models.analysis_result import AnalysisResult
from iva.core.models.settings import AnalysisSettings
from iva.core.models.signal_data import ColumnRoleAssignment, RawFileData

__all__ = ["AnalysisSession"]


@dataclass
class AnalysisSession:
    """Mutable container that holds all state for one analysis session.

    The session progresses through the following lifecycle:
    1. ``source_file_path`` is set by the caller (GUI or CLI).
    2. ``role_assignment`` is populated from user input or a config file.
    3. ``settings`` may be customised; defaults are applied on construction.
    4. After running the pipeline, ``result`` and ``warnings`` are populated.

    Only ``AnalysisSession`` is allowed to own session state.  Passing data
    between pipeline steps via other objects or globals is prohibited.
    """

    source_file_path: Path | None = None
    raw_data: RawFileData | None = None
    role_assignment: ColumnRoleAssignment | None = None
    settings: AnalysisSettings = field(default_factory=AnalysisSettings)
    result: AnalysisResult | None = None
    warnings: list[str] = field(default_factory=list)
    output_dir: Path | None = None
    is_demo: bool = False
    demo_scenario_key: str | None = None
    demo_title: str | None = None
    demo_description: str | None = None

    # ------------------------------------------------------------------
    # State queries
    # ------------------------------------------------------------------

    def is_ready_for_analysis(self) -> bool:
        """Return True if the session has enough information to run the pipeline.

        Requires:
        - ``source_file_path`` is set.
        - ``role_assignment`` is set (column roles and sampling rate).
        - ``settings`` is set (always true because of ``default_factory``).
        """
        return (
            self.source_file_path is not None
            and self.role_assignment is not None
            and self.settings is not None
        )

    # ------------------------------------------------------------------
    # State mutation
    # ------------------------------------------------------------------

    def clear(self) -> None:
        """Reset all data fields to their initial state.

        ``settings`` is intentionally preserved so that a user's parameter
        choices survive a «clear and reload» operation.
        """
        self.source_file_path = None
        self.raw_data = None
        self.role_assignment = None
        self.result = None
        self.warnings = []
        self.output_dir = None
        self.is_demo = False
        self.demo_scenario_key = None
        self.demo_title = None
        self.demo_description = None
        # settings is preserved intentionally
