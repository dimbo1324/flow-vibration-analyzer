"""Collect and print project diagnostics.

Run from the repository root:
    python scripts/diagnose_project.py

Writes a timestamped diagnostics file to out/diagnostics/ and prints the
same information to the console.  No secrets are included.
Standard library only (except checking importable third-party packages).
"""

from __future__ import annotations

import datetime
import importlib
import os
import platform
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_out_dir() -> Path:
    env = os.environ.get("IVA_OUT_DIR")
    if env:
        return Path(env)
    return Path(__file__).resolve().parent.parent / "out"


def _get_diagnostics_dir() -> Path:
    d = _get_out_dir() / "diagnostics"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _pkg_version(pkg_name: str) -> str:
    """Return the version string of an installed package, or 'not installed'."""
    try:
        mod = importlib.import_module(pkg_name)
        return str(getattr(mod, "__version__", "unknown"))
    except ImportError:
        return "not installed"


def _git_info() -> dict[str, str]:
    """Return a dict with git branch and short status."""
    info: dict[str, str] = {}

    def _run(args: list[str]) -> str:
        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
            )
            return result.stdout.strip() if result.returncode == 0 else "(error)"
        except Exception:
            return "(unavailable)"

    info["branch"] = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    info["status"] = _run(["git", "status", "--short"])
    info["last_commit"] = _run(["git", "log", "--oneline", "-1"])
    return info


def _latest_log_file() -> str:
    """Return the path to the most recently modified iva_*.log file, or ''."""
    log_dir = _get_out_dir() / "logs"
    if not log_dir.exists():
        return "(no logs directory)"
    log_files = sorted(log_dir.glob("iva_*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not log_files:
        return "(no log files found)"
    return str(log_files[0])


# ---------------------------------------------------------------------------
# Collect diagnostics
# ---------------------------------------------------------------------------


def collect() -> list[str]:
    lines: list[str] = []
    ts = datetime.datetime.now().isoformat(timespec="seconds")

    lines.append("=" * 60)
    lines.append("IVA Project Diagnostics")
    lines.append(f"Generated: {ts}")
    lines.append("=" * 60)
    lines.append("")

    # Python / platform
    lines.append("--- Python & Platform ---")
    lines.append(f"Python version : {sys.version}")
    lines.append(f"Platform       : {platform.platform()}")
    lines.append(f"Architecture   : {platform.machine()}")
    lines.append(f"OS             : {platform.system()} {platform.release()}")
    lines.append("")

    # Package versions
    packages = [
        ("numpy", "numpy"),
        ("scipy", "scipy"),
        ("pandas", "pandas"),
        ("pyarrow", "pyarrow"),
        ("openpyxl", "openpyxl"),
    ]
    lines.append("--- Package Versions ---")
    for display_name, import_name in packages:
        lines.append(f"{display_name:<12}: {_pkg_version(import_name)}")
    lines.append("")

    # Git info
    git = _git_info()
    lines.append("--- Git ---")
    lines.append(f"Branch      : {git.get('branch', '(unknown)')}")
    lines.append(f"Last commit : {git.get('last_commit', '(unknown)')}")
    status = git.get("status", "")
    if status:
        lines.append("Status (short):")
        for status_line in status.splitlines():
            lines.append(f"  {status_line}")
    else:
        lines.append("Status      : clean")
    lines.append("")

    # Output paths
    lines.append("--- Output Paths ---")
    out_dir = _get_out_dir()
    lines.append(f"out/ base      : {out_dir}")
    lines.append(f"Latest log     : {_latest_log_file()}")
    lines.append("")

    lines.append("=" * 60)
    return lines


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    lines = collect()
    output = "\n".join(lines)

    # Print to console
    print(output)

    # Write to file
    diag_dir = _get_diagnostics_dir()
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = diag_dir / f"{ts}_diagnostics.txt"
    out_path.write_text(output + "\n", encoding="utf-8")

    print(f"\nDiagnostics written to: {out_path}")


if __name__ == "__main__":
    main()
