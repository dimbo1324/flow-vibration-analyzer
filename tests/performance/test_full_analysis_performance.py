"""Performance test: full analysis pipeline for 60,000 row dataset.

Expected: completes in under 3 seconds on a normal development machine.
Mark with 'performance' marker for optional CI exclusion.
"""

from __future__ import annotations

import csv
import json
import time
from pathlib import Path

import numpy as np
import pytest

pytestmark = pytest.mark.performance


def test_full_analysis_60k_rows(tmp_path: Path) -> None:
    """Full pipeline analysis of 60,000 rows should complete in < 3 seconds."""
    # Generate 60k rows: 60 seconds at 1000 Hz sample rate
    fs = 1000.0
    n = 60_000
    t = np.linspace(0, n / fs, n, endpoint=False)
    rng = np.random.default_rng(42)
    signal = np.sin(2 * np.pi * 40 * t) + 0.1 * rng.standard_normal(n)

    # Write CSV
    csv_file = tmp_path / "perf_60k.csv"
    with open(csv_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["time_s", "signal"])
        for ti, si in zip(t, signal, strict=True):
            writer.writerow([f"{ti:.6f}", f"{si:.8f}"])

    # Build minimal config JSON
    config = {
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
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(config), encoding="utf-8")

    from iva.app.analysis_session import AnalysisSession
    from iva.app.settings_manager import load_analysis_config_json
    from iva.app.workflow_coordinator import run_pipeline

    role_assignment, settings = load_analysis_config_json(config_file)
    session = AnalysisSession(
        source_file_path=csv_file,
        role_assignment=role_assignment,
        settings=settings,
    )

    start = time.perf_counter()
    result = run_pipeline(session)
    elapsed = time.perf_counter() - start

    assert result is not None, "Pipeline must return a result"
    assert result.spectrum is not None, "Spectrum must be computed"
    assert elapsed < 3.0, f"60k-row analysis took {elapsed:.2f}s, expected < 3.0s"
