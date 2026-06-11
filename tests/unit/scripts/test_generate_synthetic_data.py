"""Unit tests for scripts.generate_synthetic_data."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from scripts.generate_synthetic_data import (
    generate_all,
    generate_clean_sine,
    generate_noisy_sine,
    generate_risk_scenario,
    generate_with_gaps,
    generate_with_harmonics,
    generate_with_outliers,
)

# ---------------------------------------------------------------------------
# per-function tests
# ---------------------------------------------------------------------------


def test_generate_clean_sine_shape():
    """Output has exactly n = duration * sampling_rate rows."""
    df = generate_clean_sine(40.0, 10.0, 1000.0, 1.0)
    assert isinstance(df, pd.DataFrame)
    assert set(df.columns) == {"time_s", "signal"}
    assert len(df) == 10000


def test_generate_clean_sine_amplitude():
    """Peak absolute value equals amplitude (pure sine, no noise)."""
    df = generate_clean_sine(40.0, 10.0, 1000.0, 2.5)
    assert np.max(np.abs(df["signal"].to_numpy())) == pytest.approx(2.5, abs=0.01)


def test_generate_noisy_sine_shape():
    """Noisy sine has the same shape as a clean sine with equivalent parameters."""
    df = generate_noisy_sine(40.0, 5.0, 500.0, 1.0, snr_db=20.0, seed=0)
    assert len(df) == 2500
    assert "time_s" in df.columns and "signal" in df.columns


def test_generate_noisy_sine_deterministic():
    """Two calls with the same seed produce identical DataFrames."""
    df1 = generate_noisy_sine(40.0, 5.0, 500.0, 1.0, snr_db=20.0, seed=99)
    df2 = generate_noisy_sine(40.0, 5.0, 500.0, 1.0, snr_db=20.0, seed=99)
    pd.testing.assert_frame_equal(df1, df2)


def test_generate_with_harmonics_energy_increases():
    """Adding more harmonics increases total signal energy."""
    df1 = generate_with_harmonics(40.0, 1, 5.0, 1000.0, 1.0)
    df3 = generate_with_harmonics(40.0, 3, 5.0, 1000.0, 1.0)
    energy1 = float(np.sum(df1["signal"].to_numpy() ** 2))
    energy3 = float(np.sum(df3["signal"].to_numpy() ** 2))
    assert energy3 > energy1


def test_generate_with_outliers_count():
    """Exactly n_outliers samples are replaced with the given magnitude (abs)."""
    base = generate_clean_sine(40.0, 10.0, 1000.0, 1.0)
    df = generate_with_outliers(base, n_outliers=5, magnitude=100.0, seed=7)
    large = np.sum(np.abs(df["signal"].to_numpy()) > 50.0)
    assert large == 5


def test_generate_with_gaps_nan_fraction():
    """NaN fraction in result matches the requested gap_fraction (approx)."""
    base = generate_clean_sine(40.0, 10.0, 1000.0, 1.0)
    df = generate_with_gaps(base, gap_fraction=0.10, seed=3)
    actual = float(df["signal"].isna().sum()) / len(df)
    assert actual == pytest.approx(0.10, abs=0.005)


def test_generate_risk_scenario_two_frequencies():
    """Risk scenario contains energy at both shedding and natural frequencies."""
    df = generate_risk_scenario(35.0, 38.0, 10.0, 1000.0, 1.0, seed=0)
    assert len(df) == 10000
    assert "time_s" in df.columns
    # Basic sanity: signal is not constant
    assert float(df["signal"].std()) > 0.0


def test_generate_all_creates_files(tmp_path):
    """generate_all creates all expected CSV files and the README."""
    generate_all(tmp_path)

    expected = [
        tmp_path / "data" / "synthetic" / "clean_sine.csv",
        tmp_path / "data" / "synthetic" / "noisy_sine.csv",
        tmp_path / "data" / "synthetic" / "harmonics.csv",
        tmp_path / "data" / "synthetic" / "with_outliers.csv",
        tmp_path / "data" / "synthetic" / "with_gaps.csv",
        tmp_path / "data" / "synthetic" / "risk_scenario.csv",
        tmp_path / "data" / "examples" / "example_clean_sine.csv",
        tmp_path / "data" / "examples" / "example_noisy_sine.csv",
        tmp_path / "data" / "examples" / "example_with_gaps.csv",
        tmp_path / "data" / "examples" / "example_risk_like_signal.csv",
        tmp_path / "data" / "examples" / "README.md",
    ]
    for p in expected:
        assert p.exists(), f"Expected file not created: {p}"
