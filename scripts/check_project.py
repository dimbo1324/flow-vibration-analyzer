"""Run the full project quality-check suite.

Run from the repository root:
    python scripts/check_project.py

Exits with a non-zero code if any check fails.
"""

from __future__ import annotations

import subprocess
import sys


def run(label: str, cmd: list[str]) -> None:
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"  {' '.join(cmd)}")
    print(f"{'='*60}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"\n[FAILED] {label} exited with code {result.returncode}")
        sys.exit(result.returncode)
    print(f"[OK] {label}")


def main() -> None:
    print("Flow Vibration Analyzer — full project check")
    print(f"Python: {sys.version}")

    run("Smoke test: run main.py", [sys.executable, "main.py"])

    run(
        "Compile: syntax check all Python files",
        [sys.executable, "-m", "compileall", "main.py", "iva", "tests", "-q"],
    )

    run("pytest: run all tests", [sys.executable, "-m", "pytest"])

    run(
        "black: verify formatting",
        [sys.executable, "-m", "black", "--check", "."],
    )

    run("ruff: lint check", [sys.executable, "-m", "ruff", "check", "."])

    run(
        "mypy: type-check core models",
        [sys.executable, "-m", "mypy", "iva/core/models"],
    )

    run(
        "mypy: type-check full iva package and main",
        [sys.executable, "-m", "mypy", "iva", "main.py"],
    )

    print("\n[DONE] All checks passed.")


if __name__ == "__main__":
    main()
