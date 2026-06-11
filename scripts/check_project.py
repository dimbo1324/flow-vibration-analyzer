"""Run the full project quality-check suite.

Run from the repository root:
    python scripts/check_project.py

Creates a timestamped run directory under out/workflow-runs/ with individual
log files for each check step.  Also prints readable progress to the console.
Exits with a non-zero code if any required command fails.
"""

from __future__ import annotations

import datetime
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Output directory helpers
# ---------------------------------------------------------------------------


def _get_out_dir() -> Path:
    """Return base output directory (out/ by default, or IVA_OUT_DIR env)."""
    import os

    env = os.environ.get("IVA_OUT_DIR")
    if env:
        return Path(env)
    # scripts/ sits one level inside the project root
    return Path(__file__).resolve().parent.parent / "out"


def _make_run_dir() -> Path:
    """Create and return a timestamped workflow-run directory."""
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = _get_out_dir() / "workflow-runs" / ts
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


class CheckRunner:
    def __init__(self) -> None:
        self.run_dir = _make_run_dir()
        self.commands_log = self.run_dir / "commands.log"
        self.summary_lines: list[str] = []
        self.failed = False

        print("\nFlow Vibration Analyzer — full project check")
        print(f"Python: {sys.version}")
        print(f"Run directory: {self.run_dir}\n")

        with self.commands_log.open("w", encoding="utf-8") as f:
            f.write(f"Run started: {datetime.datetime.now().isoformat()}\n")
            f.write(f"Python: {sys.version}\n\n")

    def run(
        self,
        label: str,
        cmd: list[str],
        log_name: str | None = None,
        required: bool = True,
    ) -> bool:
        """Run a command, print progress, write log, return True on success."""
        print(f"{'='*60}")
        print(f"  {label}")
        print(f"  {' '.join(cmd)}")
        print(f"{'='*60}")

        # Append to commands.log
        with self.commands_log.open("a", encoding="utf-8") as f:
            f.write(f"CMD [{label}]: {' '.join(cmd)}\n")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        # Print output to console (use errors="replace" for Windows cp1251 consoles)
        if result.stdout:
            sys.stdout.buffer.write(
                result.stdout.encode(sys.stdout.encoding or "utf-8", errors="replace")
            )
            sys.stdout.flush()
        if result.stderr:
            sys.stderr.buffer.write(
                result.stderr.encode(sys.stderr.encoding or "utf-8", errors="replace")
            )
            sys.stderr.flush()

        # Write individual log file
        if log_name:
            log_path = self.run_dir / log_name
            with log_path.open("w", encoding="utf-8") as f:
                f.write(f"Command: {' '.join(cmd)}\n")
                f.write(f"Return code: {result.returncode}\n\n")
                f.write("--- STDOUT ---\n")
                f.write(result.stdout or "")
                f.write("\n--- STDERR ---\n")
                f.write(result.stderr or "")

        ok = result.returncode == 0
        status = "[OK]" if ok else f"[FAILED] (exit {result.returncode})"
        print(f"{status} {label}\n")

        self.summary_lines.append(f"{status} {label}")

        with self.commands_log.open("a", encoding="utf-8") as f:
            f.write(f"  -> exit {result.returncode}\n\n")

        if not ok and required:
            self.failed = True
            self._write_summary()
            sys.exit(result.returncode)

        return ok

    def _write_summary(self) -> None:
        summary_path = self.run_dir / "summary.txt"
        with summary_path.open("w", encoding="utf-8") as f:
            f.write(f"Run: {datetime.datetime.now().isoformat()}\n")
            f.write(f"Python: {sys.version}\n\n")
            for line in self.summary_lines:
                f.write(line + "\n")
        print(f"\nSummary written to: {summary_path}")

    def finish(self) -> None:
        self._write_summary()
        if not self.failed:
            print("\n[DONE] All checks passed.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    runner = CheckRunner()
    exe = sys.executable

    # Packages that may or may not exist (targeted mypy checks)
    _project_root = Path(__file__).resolve().parent.parent

    def mypy_if_exists(label: str, pkg_path: str, log_name: str) -> None:
        if (_project_root / pkg_path).exists():
            runner.run(
                f"mypy: {label}",
                [exe, "-m", "mypy", pkg_path],
                log_name=log_name,
                required=False,
            )

    # --- Required checks ---
    runner.run(
        "Smoke test: python main.py",
        [exe, "main.py"],
        log_name="smoke.log",
    )

    runner.run(
        "CLI help: python -m iva.cli.main --help",
        [exe, "-m", "iva.cli.main", "--help"],
        log_name="cli_help.log",
    )

    runner.run(
        "Compile: syntax check all Python files",
        [exe, "-m", "compileall", "main.py", "iva", "tests", "scripts", "-q"],
        log_name="compile.log",
    )

    runner.run(
        "pytest: run all tests",
        [exe, "-m", "pytest"],
        log_name="pytest.log",
    )

    runner.run(
        "black: verify formatting",
        [exe, "-m", "black", "--check", "."],
        log_name="black.log",
    )

    runner.run(
        "ruff: lint check",
        [exe, "-m", "ruff", "check", "."],
        log_name="ruff.log",
    )

    runner.run(
        "mypy: full iva package and main",
        [exe, "-m", "mypy", "iva", "main.py"],
        log_name="mypy.log",
    )

    # --- Targeted mypy checks (skip missing packages) ---
    targeted_packages = [
        ("core/models", "iva/core/models", "mypy_core_models.log"),
        ("core/signal", "iva/core/signal", "mypy_core_signal.log"),
        ("core/spectrum", "iva/core/spectrum", "mypy_core_spectrum.log"),
        ("core/physics", "iva/core/physics", "mypy_core_physics.log"),
        ("core/validation", "iva/core/validation", "mypy_core_validation.log"),
        ("infrastructure", "iva/infrastructure", "mypy_infrastructure.log"),
        ("app", "iva/app", "mypy_app.log"),
        ("cli", "iva/cli", "mypy_cli.log"),
    ]
    for label, pkg_path, log_name in targeted_packages:
        mypy_if_exists(label, pkg_path, log_name)

    runner.finish()


if __name__ == "__main__":
    main()
