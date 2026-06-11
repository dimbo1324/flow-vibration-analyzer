"""Integration tests for the IVA CLI (iva.cli.main).

Tests run the CLI as a subprocess using ``sys.executable`` to ensure the full
import chain and argument parsing work correctly end-to-end.
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_sine_csv(path: Path, freq_hz: float = 40.0, fs: float = 1000.0) -> None:
    """Write a clean sinusoid CSV to *path*.

    Uses 6 seconds to safely exceed the 5-second minimum required by the
    data quality checker (which measures duration as t[-1] - t[0]).
    """
    duration = 6.0
    n = int(fs * duration) + 1
    t = np.linspace(0, duration, n, endpoint=True)
    signal = np.sin(2 * np.pi * freq_hz * t)
    with open(path, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["time_s", "signal"])
        for ti, si in zip(t, signal, strict=True):
            writer.writerow([ti, si])


def _write_config(path: Path, csv_path: Path) -> None:
    """Write a minimal valid JSON config to *path*."""
    config = {
        "columns": {
            "time_column": "time_s",
            "primary_signal_column": "signal",
            "signal_role": "acceleration_x",
            "additional_columns": [],
            "sampling_rate_hz": 1000.0,
            "sensor_conversion_factor": 1.0,
        },
        "preprocessing": {
            "remove_mean": True,
            "detect_outliers": False,
            "fill_gaps": False,
            "filter_type": "bandpass",
            "filter_cutoff_low_hz": 5.0,
            "filter_cutoff_high_hz": 450.0,
            "filter_order": 4,
        },
        "spectral": {
            "window_type": "hann",
            "nperseg": 512,
            "noverlap": 256,
            "peak_threshold_db": 10.0,
            "peak_min_width_hz": 0.1,
        },
        "flow_parameters": None,
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(config, fh, indent=2)


def _run_cli(*args: str) -> subprocess.CompletedProcess:  # type: ignore[type-arg]
    """Run ``python -m iva.cli.main <args>`` and return the completed process."""
    return subprocess.run(
        [sys.executable, "-m", "iva.cli.main", *args],
        capture_output=True,
        text=True,
        timeout=120,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_cli_help() -> None:
    """``--help`` exits with code 0 and prints usage information."""
    proc = _run_cli("--help")
    assert proc.returncode == 0
    assert "analyze" in proc.stdout.lower() or "usage" in proc.stdout.lower()


def test_cli_analyze_help() -> None:
    """``analyze --help`` exits with code 0."""
    proc = _run_cli("analyze", "--help")
    assert proc.returncode == 0


def test_cli_no_command_exits_nonzero() -> None:
    """Running CLI with no sub-command exits with a non-zero code."""
    proc = _run_cli()
    assert proc.returncode != 0


def test_cli_success(tmp_path: Path) -> None:
    """Full successful analysis exits with code 0 and produces output files."""
    csv_file = tmp_path / "signal.csv"
    config_file = tmp_path / "config.json"
    output_dir = tmp_path / "output"

    _write_sine_csv(csv_file)
    _write_config(config_file, csv_file)

    proc = _run_cli(
        "analyze",
        "--data",
        str(csv_file),
        "--config",
        str(config_file),
        "--output",
        str(output_dir),
    )
    assert proc.returncode == 0, f"CLI failed:\nstdout={proc.stdout}\nstderr={proc.stderr}"

    # Check expected output files exist
    assert (output_dir / "analysis_summary.json").exists()
    assert (output_dir / "spectrum.csv").exists()
    assert (output_dir / "signal.csv").exists()
    assert (output_dir / "physics_summary.csv").exists()
    assert (output_dir / "analysis_summary.html").exists()


def test_cli_output_json_is_valid(tmp_path: Path) -> None:
    """The JSON output file is valid JSON with expected keys."""
    csv_file = tmp_path / "signal.csv"
    config_file = tmp_path / "config.json"
    output_dir = tmp_path / "output"

    _write_sine_csv(csv_file)
    _write_config(config_file, csv_file)

    proc = _run_cli(
        "analyze",
        "--data",
        str(csv_file),
        "--config",
        str(config_file),
        "--output",
        str(output_dir),
    )
    assert proc.returncode == 0

    with open(output_dir / "analysis_summary.json", encoding="utf-8") as fh:
        data = json.load(fh)

    assert "session_id" in data
    assert "completed_at" in data
    assert "spectrum" in data
    assert "warnings" in data


def test_cli_missing_data_file(tmp_path: Path) -> None:
    """CLI exits non-zero when the data file does not exist."""
    config_file = tmp_path / "config.json"
    output_dir = tmp_path / "output"

    _write_config(config_file, tmp_path / "nonexistent.csv")

    proc = _run_cli(
        "analyze",
        "--data",
        str(tmp_path / "nonexistent.csv"),
        "--config",
        str(config_file),
        "--output",
        str(output_dir),
    )
    assert proc.returncode != 0


def test_cli_missing_file_no_raw_traceback(tmp_path: Path) -> None:
    """stderr must not contain a Python traceback when --debug is not set."""
    config_file = tmp_path / "config.json"
    output_dir = tmp_path / "output"

    _write_config(config_file, tmp_path / "missing.csv")

    proc = _run_cli(
        "analyze",
        "--data",
        str(tmp_path / "missing.csv"),
        "--config",
        str(config_file),
        "--output",
        str(output_dir),
    )
    assert proc.returncode != 0
    assert "Traceback" not in proc.stderr, "Raw traceback should not appear without --debug"


def test_cli_missing_config_file(tmp_path: Path) -> None:
    """CLI exits non-zero when the config file does not exist."""
    csv_file = tmp_path / "signal.csv"
    _write_sine_csv(csv_file)

    proc = _run_cli(
        "analyze",
        "--data",
        str(csv_file),
        "--config",
        str(tmp_path / "no_config.json"),
        "--output",
        str(tmp_path / "output"),
    )
    assert proc.returncode != 0
