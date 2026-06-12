"""Application service for preparing and running built-in demo analyses."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from iva.app.analysis_runner import AnalysisRunner
from iva.app.analysis_session import AnalysisSession
from iva.core.models.analysis_result import AnalysisResult
from iva.core.models.settings import AnalysisSettings
from iva.core.models.signal_data import ColumnRoleAssignment
from iva.core.synthetic.demo_scenarios import (
    DemoScenario,
    generate_demo_signal,
    list_demo_scenarios,
)

__all__ = [
    "list_available_demo_scenarios",
    "create_demo_session",
    "run_demo_analysis",
]


def list_available_demo_scenarios() -> tuple[DemoScenario, ...]:
    """Return the stable list of built-in demonstration scenarios."""
    return list_demo_scenarios()


def create_demo_session(
    scenario_key: str,
    output_dir: str | Path | None = None,
) -> AnalysisSession:
    """Generate runtime CSV data and return a fully prepared demo session."""
    scenario, columns = generate_demo_signal(scenario_key)
    runtime_dir = (
        Path(output_dir)
        if output_dir is not None
        else Path(__file__).resolve().parents[2] / "out" / "demo-data"
    )
    runtime_dir.mkdir(parents=True, exist_ok=True)
    source_path = runtime_dir / f"demo_{scenario.key}.csv"
    pd.DataFrame(columns).to_csv(source_path, index=False)

    return AnalysisSession(
        source_file_path=source_path,
        role_assignment=ColumnRoleAssignment(
            time_column="time_s",
            primary_signal_column="signal",
            signal_role=scenario.signal_role,
            additional_columns={},
            sampling_rate_hz=scenario.sampling_rate_hz,
            sensor_conversion_factor=None,
        ),
        settings=AnalysisSettings(
            preprocessing=scenario.preprocessing_settings,
            spectral=scenario.spectral_settings,
            flow_parameters=scenario.flow_parameters,
        ),
        output_dir=runtime_dir,
        is_demo=True,
        demo_scenario_key=scenario.key,
        demo_title=scenario.title_ru,
        demo_description=scenario.description_ru,
    )


def run_demo_analysis(
    scenario_key: str,
    output_dir: str | Path | None = None,
) -> AnalysisResult:
    """Run a built-in demo through the normal analysis pipeline."""
    session = create_demo_session(scenario_key, output_dir)
    return AnalysisRunner().run(session)
