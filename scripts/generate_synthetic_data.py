"""CLI wrapper around :mod:`iva.core.synthetic` signal generators."""

# ruff: noqa: E402 - direct script execution requires adding the repository root first.

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from iva.core.synthetic import (
    generate_clean_sine as _generate_clean_sine,
)
from iva.core.synthetic import (
    generate_demo_signal,
    list_demo_scenarios,
)
from iva.core.synthetic import (
    generate_noisy_sine as _generate_noisy_sine,
)
from iva.core.synthetic import (
    generate_risk_scenario as _generate_risk_scenario,
)
from iva.core.synthetic import (
    generate_with_gaps as _generate_with_gaps,
)
from iva.core.synthetic import (
    generate_with_harmonics as _generate_with_harmonics,
)
from iva.core.synthetic import (
    generate_with_outliers as _generate_with_outliers,
)


def _frame(time_s: np.ndarray, signal: np.ndarray) -> pd.DataFrame:
    return pd.DataFrame({"time_s": time_s, "signal": signal})


def generate_clean_sine(
    frequency_hz: float,
    duration_s: float,
    sampling_rate_hz: float,
    amplitude: float,
) -> pd.DataFrame:
    """Backward-compatible DataFrame wrapper for a clean sine wave."""
    return _frame(*_generate_clean_sine(frequency_hz, duration_s, sampling_rate_hz, amplitude))


def generate_noisy_sine(
    frequency_hz: float,
    duration_s: float,
    sampling_rate_hz: float,
    amplitude: float,
    snr_db: float,
    seed: int | None = None,
) -> pd.DataFrame:
    """Backward-compatible DataFrame wrapper for a noisy sine wave."""
    return _frame(
        *_generate_noisy_sine(
            frequency_hz,
            duration_s,
            sampling_rate_hz,
            amplitude,
            snr_db,
            seed,
        )
    )


def generate_with_harmonics(
    fundamental_hz: float,
    n_harmonics: int,
    duration_s: float,
    sampling_rate_hz: float,
    amplitude: float,
) -> pd.DataFrame:
    """Preserve the original script argument order for harmonic signals."""
    return _frame(
        *_generate_with_harmonics(
            fundamental_hz,
            duration_s,
            sampling_rate_hz,
            amplitude,
            n_harmonics,
        )
    )


def generate_with_outliers(
    base_signal: pd.DataFrame,
    n_outliers: int,
    magnitude: float,
    seed: int | None = None,
) -> pd.DataFrame:
    """Preserve the original DataFrame API for injecting outliers."""
    frame = base_signal.copy()
    frame["signal"] = _generate_with_outliers(
        frame["signal"].to_numpy(dtype=np.float64), n_outliers, magnitude, seed
    )
    return frame


def generate_with_gaps(
    base_signal: pd.DataFrame,
    gap_fraction: float,
    seed: int | None = None,
) -> pd.DataFrame:
    """Preserve the original DataFrame API for inserting gaps."""
    frame = base_signal.copy()
    frame["signal"] = _generate_with_gaps(
        frame["signal"].to_numpy(dtype=np.float64), gap_fraction, seed
    )
    return frame


def generate_risk_scenario(
    shedding_hz: float,
    natural_hz: float,
    duration_s: float,
    sampling_rate_hz: float,
    amplitude: float,
    seed: int | None = None,
) -> pd.DataFrame:
    """Backward-compatible DataFrame wrapper for a near-resonance signal."""
    return _frame(
        *_generate_risk_scenario(
            shedding_hz,
            natural_hz,
            duration_s,
            sampling_rate_hz,
            amplitude,
            seed,
        )
    )


def _write_frame(frame: pd.DataFrame, path: Path, created: list[Path]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    created.append(path)


def generate_all(base_dir: Path | None = None) -> None:
    """Regenerate the tracked development and example synthetic CSV files."""
    root = base_dir or Path(__file__).resolve().parent.parent
    synthetic_dir = root / "data" / "synthetic"
    examples_dir = root / "data" / "examples"
    created: list[Path] = []

    fs = 1000.0
    duration = 10.0
    clean = generate_clean_sine(40.0, duration, fs, 1.0)
    _write_frame(clean, synthetic_dir / "clean_sine.csv", created)
    _write_frame(
        generate_noisy_sine(40.0, duration, fs, 1.0, 20.0, 42),
        synthetic_dir / "noisy_sine.csv",
        created,
    )
    _write_frame(
        generate_with_harmonics(40.0, 3, duration, fs, 1.0),
        synthetic_dir / "harmonics.csv",
        created,
    )
    _write_frame(
        generate_with_outliers(clean, 20, 5.0, 42),
        synthetic_dir / "with_outliers.csv",
        created,
    )
    _write_frame(
        generate_with_gaps(clean, 0.05, 42),
        synthetic_dir / "with_gaps.csv",
        created,
    )
    _write_frame(
        generate_risk_scenario(35.0, 38.0, duration, fs, 1.0, 42),
        synthetic_dir / "risk_scenario.csv",
        created,
    )

    example_fs = 500.0
    example_duration = 6.0
    example_clean = generate_clean_sine(40.0, example_duration, example_fs, 1.0)
    _write_frame(example_clean, examples_dir / "example_clean_sine.csv", created)
    _write_frame(
        generate_noisy_sine(40.0, example_duration, example_fs, 1.0, 15.0, 0),
        examples_dir / "example_noisy_sine.csv",
        created,
    )
    _write_frame(
        generate_with_gaps(example_clean, 0.10, 7),
        examples_dir / "example_with_gaps.csv",
        created,
    )
    _write_frame(
        generate_risk_scenario(35.0, 38.0, example_duration, example_fs, 1.0, 3),
        examples_dir / "example_risk_like_signal.csv",
        created,
    )

    readme = examples_dir / "README.md"
    readme.write_text(
        "# IVA Example Data Files\n\n"
        "Small demonstration CSV files generated by `scripts/generate_synthetic_data.py`.\n"
        "Each file contains `time_s` and `signal` columns.\n",
        encoding="utf-8",
    )
    created.append(readme)
    _print_created(created, root)


def generate_selected_scenario(scenario_key: str, output_dir: Path) -> Path:
    """Write one built-in demo scenario to a selected output directory."""
    scenario, columns = generate_demo_signal(scenario_key)
    destination = output_dir / f"demo_{scenario.key}.csv"
    _write_frame(pd.DataFrame(columns), destination, [])
    print(f"Создан демо-сценарий: {scenario.title_ru}")
    print(destination)
    return destination


def _print_created(created: list[Path], root: Path) -> None:
    print("Generated files:")
    for path in created:
        try:
            display_path = path.relative_to(root)
        except ValueError:
            display_path = path
        print(f"  {display_path}  ({path.stat().st_size / 1024:.1f} KB)")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Генератор синтетических данных IVA")
    parser.add_argument(
        "base_dir",
        nargs="?",
        type=Path,
        help="Корень репозитория для прежнего режима generate_all.",
    )
    parser.add_argument("--scenario", choices=[item.key for item in list_demo_scenarios()])
    parser.add_argument("--output-dir", type=Path, help="Папка для выбранного сценария.")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    if args.scenario:
        output_dir = args.output_dir or Path("data") / "synthetic"
        generate_selected_scenario(args.scenario, output_dir)
    else:
        generate_all(args.base_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
