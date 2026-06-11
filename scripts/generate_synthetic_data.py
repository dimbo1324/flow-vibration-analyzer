"""Deterministic synthetic signal generator for the Industrial Vibration Analyzer.

Run directly to create development/demo CSV files::

    python scripts/generate_synthetic_data.py

Functions are importable without any side effects; file generation only
happens inside the ``if __name__ == "__main__":`` block (or ``generate_all``
when called explicitly with a base directory).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Generator functions
# ---------------------------------------------------------------------------


def generate_clean_sine(
    frequency_hz: float,
    duration_s: float,
    sampling_rate_hz: float,
    amplitude: float,
) -> pd.DataFrame:
    """Generate a pure, noise-free sinusoidal signal.

    Args:
        frequency_hz: Frequency of the sine wave in Hz.
        duration_s: Total duration of the signal in seconds.
        sampling_rate_hz: Number of samples per second.
        amplitude: Peak amplitude of the signal.

    Returns:
        DataFrame with columns ``time_s`` and ``signal``.
    """
    n = int(duration_s * sampling_rate_hz)
    t = np.linspace(0.0, duration_s, n, endpoint=False)
    signal = amplitude * np.sin(2.0 * np.pi * frequency_hz * t)
    return pd.DataFrame({"time_s": t, "signal": signal})


def generate_noisy_sine(
    frequency_hz: float,
    duration_s: float,
    sampling_rate_hz: float,
    amplitude: float,
    snr_db: float,
    seed: int | None = None,
) -> pd.DataFrame:
    """Generate a sinusoidal signal with additive Gaussian noise.

    Args:
        frequency_hz: Frequency of the sine wave in Hz.
        duration_s: Total duration in seconds.
        sampling_rate_hz: Number of samples per second.
        amplitude: Peak amplitude of the sine component.
        snr_db: Signal-to-noise ratio in decibels.
        seed: Optional random seed for reproducibility.

    Returns:
        DataFrame with columns ``time_s`` and ``signal``.
    """
    rng = np.random.default_rng(seed)
    n = int(duration_s * sampling_rate_hz)
    t = np.linspace(0.0, duration_s, n, endpoint=False)
    sine = amplitude * np.sin(2.0 * np.pi * frequency_hz * t)
    # Signal power = amplitude^2 / 2
    signal_power = (amplitude**2) / 2.0
    noise_power = signal_power / (10.0 ** (snr_db / 10.0))
    noise = rng.normal(0.0, np.sqrt(noise_power), n)
    return pd.DataFrame({"time_s": t, "signal": sine + noise})


def generate_with_harmonics(
    fundamental_hz: float,
    n_harmonics: int,
    duration_s: float,
    sampling_rate_hz: float,
    amplitude: float,
) -> pd.DataFrame:
    """Generate a signal composed of a fundamental frequency and its harmonics.

    Each harmonic k has amplitude = amplitude / k (natural roll-off).

    Args:
        fundamental_hz: Fundamental frequency in Hz.
        n_harmonics: Number of harmonics to include (1 = fundamental only).
        duration_s: Total duration in seconds.
        sampling_rate_hz: Number of samples per second.
        amplitude: Amplitude of the fundamental component.

    Returns:
        DataFrame with columns ``time_s`` and ``signal``.
    """
    n = int(duration_s * sampling_rate_hz)
    t = np.linspace(0.0, duration_s, n, endpoint=False)
    signal = np.zeros(n)
    for k in range(1, n_harmonics + 1):
        signal += (amplitude / k) * np.sin(2.0 * np.pi * k * fundamental_hz * t)
    return pd.DataFrame({"time_s": t, "signal": signal})


def generate_with_outliers(
    base_signal: pd.DataFrame,
    n_outliers: int,
    magnitude: float,
    seed: int | None = None,
) -> pd.DataFrame:
    """Insert isolated spike outliers into a copy of ``base_signal``.

    Args:
        base_signal: Source DataFrame with ``time_s`` and ``signal`` columns.
        n_outliers: Number of outlier points to inject.
        magnitude: Absolute value of the injected outlier spikes.
        seed: Optional random seed.

    Returns:
        A new DataFrame with the same structure but with outlier values.
    """
    rng = np.random.default_rng(seed)
    df = base_signal.copy()
    n = len(df)
    if n_outliers > 0 and n > 0:
        indices = rng.choice(n, size=min(n_outliers, n), replace=False)
        signs = rng.choice([-1.0, 1.0], size=len(indices))
        df.iloc[indices, df.columns.get_loc("signal")] = magnitude * signs
    return df


def generate_with_gaps(
    base_signal: pd.DataFrame,
    gap_fraction: float,
    seed: int | None = None,
) -> pd.DataFrame:
    """Replace a random fraction of signal values with NaN to simulate gaps.

    Args:
        base_signal: Source DataFrame with ``time_s`` and ``signal`` columns.
        gap_fraction: Fraction of samples to set to NaN (0.0 to 1.0).
        seed: Optional random seed.

    Returns:
        A new DataFrame with NaN values at random positions in ``signal``.
    """
    rng = np.random.default_rng(seed)
    df = base_signal.copy()
    n = len(df)
    n_gaps = int(n * gap_fraction)
    if n_gaps > 0:
        indices = rng.choice(n, size=n_gaps, replace=False)
        df.iloc[indices, df.columns.get_loc("signal")] = np.nan
    return df


def generate_risk_scenario(
    shedding_hz: float,
    natural_hz: float,
    duration_s: float,
    sampling_rate_hz: float,
    amplitude: float,
    seed: int | None = None,
) -> pd.DataFrame:
    """Generate a synthetic vibration signal with two close frequency components.

    The two components (shedding and structural) are placed near each other
    to produce a signal representative of a near-resonance scenario.  This
    function generates a *signal* only — it does NOT assess risk, compute
    physics coefficients or implement lock-in logic.

    Args:
        shedding_hz: Frequency of the vortex shedding component.
        natural_hz: Frequency of the structural response component.
        duration_s: Total duration in seconds.
        sampling_rate_hz: Number of samples per second.
        amplitude: Peak amplitude of each frequency component.
        seed: Optional random seed for optional noise.

    Returns:
        DataFrame with columns ``time_s`` and ``signal``.
    """
    rng = np.random.default_rng(seed)
    n = int(duration_s * sampling_rate_hz)
    t = np.linspace(0.0, duration_s, n, endpoint=False)
    shedding_component = amplitude * np.sin(2.0 * np.pi * shedding_hz * t)
    structural_component = (amplitude * 0.5) * np.sin(2.0 * np.pi * natural_hz * t)
    noise = rng.normal(0.0, amplitude * 0.05, n)
    signal = shedding_component + structural_component + noise
    return pd.DataFrame({"time_s": t, "signal": signal})


# ---------------------------------------------------------------------------
# File generation helper
# ---------------------------------------------------------------------------


def generate_all(base_dir: Path | None = None) -> None:
    """Generate all demo and synthetic data files.

    Args:
        base_dir: Repository root.  If None, the parent of this script's
            directory is used.
    """
    if base_dir is None:
        base_dir = Path(__file__).resolve().parent.parent

    synthetic_dir = base_dir / "data" / "synthetic"
    examples_dir = base_dir / "data" / "examples"
    synthetic_dir.mkdir(parents=True, exist_ok=True)
    examples_dir.mkdir(parents=True, exist_ok=True)

    fs = 1000.0  # Hz
    dur = 10.0  # seconds

    created: list[Path] = []

    # -- Synthetic: full-length signals ------------------------------------

    df = generate_clean_sine(40.0, dur, fs, 1.0)
    p = synthetic_dir / "clean_sine.csv"
    df.to_csv(p, index=False)
    created.append(p)

    df = generate_noisy_sine(40.0, dur, fs, 1.0, snr_db=20.0, seed=42)
    p = synthetic_dir / "noisy_sine.csv"
    df.to_csv(p, index=False)
    created.append(p)

    df = generate_with_harmonics(40.0, 3, dur, fs, 1.0)
    p = synthetic_dir / "harmonics.csv"
    df.to_csv(p, index=False)
    created.append(p)

    base = generate_clean_sine(40.0, dur, fs, 1.0)
    df = generate_with_outliers(base, n_outliers=20, magnitude=5.0, seed=42)
    p = synthetic_dir / "with_outliers.csv"
    df.to_csv(p, index=False)
    created.append(p)

    df = generate_with_gaps(base, gap_fraction=0.05, seed=42)
    p = synthetic_dir / "with_gaps.csv"
    df.to_csv(p, index=False)
    created.append(p)

    df = generate_risk_scenario(35.0, 38.0, dur, fs, 1.0, seed=42)
    p = synthetic_dir / "risk_scenario.csv"
    df.to_csv(p, index=False)
    created.append(p)

    # -- Examples: shorter files for Git tracking -------------------------
    # Keep examples small (≤ 1 000 rows each) so they are comfortable in Git.

    ex_fs = 500.0
    ex_dur = 6.0

    df = generate_clean_sine(40.0, ex_dur, ex_fs, 1.0)
    p = examples_dir / "example_clean_sine.csv"
    df.to_csv(p, index=False)
    created.append(p)

    df = generate_noisy_sine(40.0, ex_dur, ex_fs, 1.0, snr_db=15.0, seed=0)
    p = examples_dir / "example_noisy_sine.csv"
    df.to_csv(p, index=False)
    created.append(p)

    base_ex = generate_clean_sine(40.0, ex_dur, ex_fs, 1.0)
    df = generate_with_gaps(base_ex, gap_fraction=0.10, seed=7)
    p = examples_dir / "example_with_gaps.csv"
    df.to_csv(p, index=False)
    created.append(p)

    df = generate_risk_scenario(35.0, 38.0, ex_dur, ex_fs, 1.0, seed=3)
    p = examples_dir / "example_risk_like_signal.csv"
    df.to_csv(p, index=False)
    created.append(p)

    # -- README for examples ----------------------------------------------

    readme = examples_dir / "README.md"
    readme.write_text(
        "# IVA Example Data Files\n\n"
        "Small demonstration CSV files for the Industrial Vibration Analyzer.\n"
        "Each file has two columns: `time_s` (seconds) and `signal` (arbitrary units).\n\n"
        "| File | Description |\n"
        "|---|---|\n"
        "| `example_clean_sine.csv` | Pure 40 Hz sine wave, 6 s at 500 Hz — "
        "ideal for verifying spectral peak detection |\n"
        "| `example_noisy_sine.csv` | 40 Hz sine with Gaussian noise (SNR 15 dB) — "
        "typical sensor recording |\n"
        "| `example_with_gaps.csv` | Clean 40 Hz sine with 10% random NaN gaps — "
        "tests gap-handling in the validator |\n"
        "| `example_risk_like_signal.csv` | Two close frequencies (35 Hz + 38 Hz) "
        "representing a near-resonance scenario |\n\n"
        "These files are generated by `scripts/generate_synthetic_data.py`.\n"
        "Re-run the script to regenerate them.\n",
        encoding="utf-8",
    )
    created.append(readme)

    print("Generated files:")
    for p in created:
        size_kb = p.stat().st_size / 1024
        print(f"  {p.relative_to(base_dir)}  ({size_kb:.1f} KB)")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    generate_all(root)
