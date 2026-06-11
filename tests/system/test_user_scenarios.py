"""System tests based on user scenarios from docs/07_user_scenarios.md.

These tests exercise the full pipeline end-to-end using only domain APIs,
so they run headless without a GUI.  They correspond to Scenario 1 (basic
vibration analysis) and a missing-file error path.
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path

import numpy as np
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _write_sine_csv(path: Path, frequency_hz: float, duration_s: float, fs: float) -> None:
    """Write a clean sine-wave CSV to *path*."""
    n = int(fs * duration_s)
    t = np.linspace(0, duration_s, n, endpoint=False)
    signal = np.sin(2 * np.pi * frequency_hz * t)
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["time_s", "signal"])
        for ti, si in zip(t, signal, strict=True):
            writer.writerow([f"{ti:.6f}", f"{si:.8f}"])


def _make_config(
    tmp_path: Path,
    fs: float,
    with_flow_params: bool = False,
) -> Path:
    """Write a minimal analysis config JSON and return its path."""
    cfg: dict = {
        "columns": {
            "time_column": "time_s",
            "primary_signal_column": "signal",
            "signal_role": "acceleration_x",
            "additional_columns": [],
            "sampling_rate_hz": fs,
            "sensor_conversion_factor": 1.0,
        },
        "preprocessing": {
            "remove_mean": True,
            "detect_outliers": False,
            "fill_gaps": False,
        },
        "spectral": {
            "window_type": "hann",
            "nperseg": 1024,
            "noverlap": 512,
        },
    }
    if with_flow_params:
        cfg["flow_parameters"] = {
            "cylinder_diameter_m": 0.012,
            "mean_flow_velocity_ms": 2.0,
            "fluid_density_kgm3": 998.0,
            "dynamic_viscosity_pas": 0.001002,
            "natural_frequency_hz": 35.0,
            "damping_ratio": 0.02,
            "cylinder_spacing_m": None,
            "geometry_type": "single_cylinder",
        }
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(cfg), encoding="utf-8")
    return config_file


# ---------------------------------------------------------------------------
# Scenario 1 — clean signal, full analysis with physics
# ---------------------------------------------------------------------------


def test_scenario_clean_signal_full_analysis(tmp_path: Path) -> None:
    """Scenario 1: engineer loads clean 40 Hz vibration data and gets risk assessment.

    The dominant spectral peak must be in the range 38–42 Hz, physics results
    must be present, and a risk assessment must be generated.
    """
    fs = 1000.0
    csv_file = tmp_path / "test.csv"
    _write_sine_csv(csv_file, frequency_hz=40.0, duration_s=6.0, fs=fs)
    config_file = _make_config(tmp_path, fs=fs, with_flow_params=True)

    from iva.app.analysis_session import AnalysisSession
    from iva.app.settings_manager import load_analysis_config_json
    from iva.app.workflow_coordinator import run_pipeline

    role_assignment, settings = load_analysis_config_json(config_file)
    session = AnalysisSession(
        source_file_path=csv_file,
        role_assignment=role_assignment,
        settings=settings,
    )
    result = run_pipeline(session)

    assert result is not None
    assert result.spectrum is not None
    assert result.spectrum.dominant_peak is not None, "Expected a dominant peak"

    freq = result.spectrum.dominant_peak.frequency_hz
    assert 38.0 <= freq <= 42.0, f"Expected dominant peak near 40 Hz, got {freq:.2f} Hz"

    assert result.physics is not None, "Physics result expected when flow_parameters provided"
    assert result.risk is not None, "Risk assessment expected when physics result present"


# ---------------------------------------------------------------------------
# Scenario 2 — basic analysis without physics
# ---------------------------------------------------------------------------


def test_scenario_basic_analysis_without_physics(tmp_path: Path) -> None:
    """Scenario: engineer runs analysis with no flow parameters — no risk assessment."""
    fs = 1000.0
    csv_file = tmp_path / "test2.csv"
    _write_sine_csv(csv_file, frequency_hz=50.0, duration_s=6.0, fs=fs)
    config_file = _make_config(tmp_path, fs=fs, with_flow_params=False)

    from iva.app.analysis_session import AnalysisSession
    from iva.app.settings_manager import load_analysis_config_json
    from iva.app.workflow_coordinator import run_pipeline

    role_assignment, settings = load_analysis_config_json(config_file)
    session = AnalysisSession(
        source_file_path=csv_file,
        role_assignment=role_assignment,
        settings=settings,
    )
    result = run_pipeline(session)

    assert result.spectrum is not None
    assert result.physics is None, "No physics expected without flow_parameters"
    assert result.risk is None, "No risk expected without physics"


# ---------------------------------------------------------------------------
# Scenario 3 — invalid file raises IVAError
# ---------------------------------------------------------------------------


def test_scenario_invalid_file_raises_iva_error(tmp_path: Path) -> None:
    """Scenario: engineer loads a nonexistent file — system raises IVAError."""
    from iva.app.analysis_session import AnalysisSession
    from iva.app.workflow_coordinator import run_pipeline
    from iva.core.models.enums import SignalRole
    from iva.core.models.exceptions import IVAError
    from iva.core.models.settings import AnalysisSettings
    from iva.core.models.signal_data import ColumnRoleAssignment

    nonexistent = tmp_path / "doesnotexist.csv"

    ra = ColumnRoleAssignment(
        time_column="time_s",
        primary_signal_column="signal",
        signal_role=SignalRole.ACCELERATION_X,
        additional_columns={},
        sampling_rate_hz=1000.0,
    )

    session = AnalysisSession(
        source_file_path=nonexistent,
        role_assignment=ra,
        settings=AnalysisSettings(),
    )

    with pytest.raises(IVAError):
        run_pipeline(session)
