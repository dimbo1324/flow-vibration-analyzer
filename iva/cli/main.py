"""CLI entry point for the Industrial Vibration Analyzer.

Usage::

    python -m iva.cli.main analyze \\
        --data data/examples/example_clean_sine.csv \\
        --config config/example_config.json \\
        --output reports/run_001

Exit codes:
    0 — success
    1 — IVA-specific error (bad input, validation failure, etc.)
    2 — unexpected / unrecognised error

Architecture rule: this module must NOT import from ``iva.ui`` or ``PySide6``.
"""

from __future__ import annotations

import argparse
import sys
import traceback
from collections.abc import Sequence
from pathlib import Path

from iva.app.analysis_runner import AnalysisRunner
from iva.app.analysis_session import AnalysisSession
from iva.app.settings_manager import load_analysis_config_json
from iva.core.models.exceptions import IVAError
from iva.infrastructure.writers.csv_export_writer import (
    export_physics_summary_csv,
    export_signal_csv,
    export_spectrum_csv,
)
from iva.infrastructure.writers.html_summary_writer import export_analysis_summary_html
from iva.infrastructure.writers.json_export_writer import export_analysis_summary_json

__all__ = ["main", "build_parser"]


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser for the IVA CLI."""
    parser = argparse.ArgumentParser(
        prog="iva",
        description="Industrial Vibration Analyzer — command-line interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Example:\n"
            "  python -m iva.cli.main analyze \\\n"
            "      --data data/examples/example_clean_sine.csv \\\n"
            "      --config config/example_config.json \\\n"
            "      --output reports/run_001\n"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    analyze = subparsers.add_parser(
        "analyze",
        help="Run a full vibration analysis from a data file and config.",
    )
    analyze.add_argument(
        "--data",
        required=True,
        metavar="PATH",
        help="Path to the input data file (.csv, .parquet, or .xlsx).",
    )
    analyze.add_argument(
        "--config",
        required=True,
        metavar="PATH",
        help="Path to the JSON analysis configuration file.",
    )
    analyze.add_argument(
        "--output",
        required=True,
        metavar="DIR",
        help="Output directory where result files will be written.",
    )
    analyze.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="Print full tracebacks on error (for debugging).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point.

    Args:
        argv: Argument list (defaults to ``sys.argv[1:]`` when ``None``).

    Returns:
        Exit code (0 = success, 1 = IVAError, 2 = unexpected error).
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "analyze":
        return _run_analyze(args)

    parser.print_help()
    return 1


def _run_analyze(args: argparse.Namespace) -> int:
    """Execute the 'analyze' sub-command.

    Args:
        args: Parsed CLI arguments (must have ``data``, ``config``, ``output``,
              ``debug`` attributes).

    Returns:
        Exit code.
    """
    try:
        # --- load config ---------------------------------------------------
        role_assignment, settings = load_analysis_config_json(args.config)

        # --- build session -------------------------------------------------
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)

        session = AnalysisSession(
            source_file_path=Path(args.data),
            role_assignment=role_assignment,
            settings=settings,
            output_dir=output_dir,
        )

        # --- run pipeline --------------------------------------------------
        runner = AnalysisRunner()
        result = runner.run(session)

        # --- save outputs --------------------------------------------------
        export_analysis_summary_json(result, output_dir / "analysis_summary.json")
        export_spectrum_csv(result, output_dir / "spectrum.csv")
        export_signal_csv(result, output_dir / "signal.csv")
        export_physics_summary_csv(result, output_dir / "physics_summary.csv")
        export_analysis_summary_html(result, output_dir / "analysis_summary.html")

        # --- console summary -----------------------------------------------
        _print_summary(result, output_dir)
        return 0

    except IVAError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        if args.debug:
            traceback.print_exc(file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Unexpected error: {exc}", file=sys.stderr)
        if args.debug:
            traceback.print_exc(file=sys.stderr)
        return 2


def _print_summary(result, output_dir: Path) -> None:  # type: ignore[no-untyped-def]
    """Print a concise analysis summary to stdout."""
    print("=== IVA Analysis Complete ===")
    print(f"Output directory: {output_dir}")

    if result.spectrum is not None and result.spectrum.dominant_peak is not None:
        print(f"Dominant peak: {result.spectrum.dominant_peak.frequency_hz:.2f} Hz")
    else:
        print("Dominant peak: not detected")

    if result.physics is not None:
        print(f"Reynolds number: {result.physics.reynolds_number:.3e}")
        print(f"Strouhal number: {result.physics.strouhal_number:.4f}")
        if result.physics.velocity_ratio is not None:
            print(f"Velocity ratio (Vr): {result.physics.velocity_ratio:.4f}")
    else:
        print("Physics: not calculated (flow_parameters not set)")

    if result.risk is not None:
        print(f"Risk level: {result.risk.risk_level.upper()}")
    else:
        print("Risk level: not assessed")

    if result.warnings:
        print(f"Warnings ({len(result.warnings)}):")
        for w in result.warnings:
            print(f"  - {w}")


if __name__ == "__main__":
    raise SystemExit(main())
