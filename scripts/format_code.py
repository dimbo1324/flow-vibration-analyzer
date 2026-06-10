"""Format all Python source files using black and ruff.

Run from the repository root:
    python scripts/format_code.py
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
    print("Flow Vibration Analyzer — code formatter")

    run("black: format all Python files", [sys.executable, "-m", "black", "."])
    run(
        "ruff: auto-fix imports and lint issues",
        [sys.executable, "-m", "ruff", "check", ".", "--fix"],
    )

    print("\n[DONE] Formatting complete — all files are clean.")


if __name__ == "__main__":
    main()
