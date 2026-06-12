"""Cross-platform cleanup of repository-local generated artifacts.

Python counterpart of ``scripts/clean.ps1`` for non-Windows shells and CI.
Removes only a conservative, hardcoded list of generated artifacts:

- top-level directories: ``reports``, ``.tmp``, ``.pytest_cache``,
  ``.mypy_cache``, ``.ruff_cache``, ``build``, ``dist`` and (unless
  ``--keep-logs``) ``out``;
- top-level files: ``.coverage`` and ``.coverage.*``;
- anywhere in the tree: ``__pycache__`` directories, ``*.egg-info``
  directories and ``*.pyc`` / ``*.pyo`` files.

Source code, docs, tests, config, demo data, ``.git`` and ``.venv`` are
never removed.  Without ``--force`` (and without ``--dry-run``) the script
asks for interactive confirmation before deleting anything.

Usage::

    python scripts/clean_project.py --dry-run
    python scripts/clean_project.py --dry-run --keep-logs
    python scripts/clean_project.py --force

Exit codes: 0 = success/nothing to do, 1 = removal errors, 2 = safety stop.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from collections.abc import Sequence
from pathlib import Path

__all__ = ["collect_targets", "is_safe_to_remove", "main"]

# Top-level directory names that may be removed as whole trees.
TOP_LEVEL_DIRS: tuple[str, ...] = (
    "reports",
    ".tmp",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "build",
    "dist",
)
# ``out`` holds workflow/diagnostic logs; removed only without --keep-logs.
LOGS_DIR_NAME = "out"

# Artifact names/extensions that may be removed anywhere inside the tree.
_ARTIFACT_DIR_NAMES = ("__pycache__",)
_ARTIFACT_DIR_SUFFIXES = (".egg-info",)
_ARTIFACT_FILE_SUFFIXES = (".pyc", ".pyo")

# Directories never traversed and never removed as a whole.
_NEVER_TRAVERSE = (".git", ".venv", "venv")


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _is_artifact(path: Path) -> bool:
    """Return True if *path* matches the known generated-artifact patterns."""
    name = path.name
    if name in _ARTIFACT_DIR_NAMES:
        return True
    if any(name.endswith(sfx) for sfx in _ARTIFACT_DIR_SUFFIXES):
        return True
    return any(name.endswith(sfx) for sfx in _ARTIFACT_FILE_SUFFIXES)


def is_safe_to_remove(path: Path, root: Path) -> bool:
    """Return True only if *path* may legitimately be removed.

    A path is safe when it is inside *root* AND is either one of the fixed
    top-level generated entries, or matches the artifact patterns
    (``__pycache__``, ``*.egg-info``, ``*.pyc``, ``*.pyo``).  Anything else —
    in particular files under ``iva/``, ``docs/``, ``tests/``, ``config/``,
    ``data/`` — is refused.
    """
    path = path.resolve()
    root = root.resolve()
    if not path.is_relative_to(root) or path == root:
        return False
    rel = path.relative_to(root)
    if any(part in _NEVER_TRAVERSE for part in rel.parts):
        return False
    # Fixed top-level entries.
    if len(rel.parts) == 1:
        name = rel.parts[0]
        if name in TOP_LEVEL_DIRS or name == LOGS_DIR_NAME:
            return True
        if name == ".coverage" or name.startswith(".coverage."):
            return True
    # Everything else must look like a known artifact, wherever it lives.
    return _is_artifact(path)


def collect_targets(root: Path, keep_logs: bool) -> tuple[list[Path], list[Path]]:
    """Return ``(directories, files)`` of existing artifacts under *root*."""
    directories: list[Path] = []
    files: list[Path] = []

    top_dirs = list(TOP_LEVEL_DIRS) + ([] if keep_logs else [LOGS_DIR_NAME])
    for name in top_dirs:
        candidate = root / name
        if candidate.is_dir():
            directories.append(candidate)

    for candidate in root.glob(".coverage*"):
        if candidate.is_file():
            files.append(candidate)

    skip_names = set(_NEVER_TRAVERSE) | set(top_dirs)
    for entry in root.iterdir():
        if entry.name in skip_names or not entry.is_dir():
            continue
        for item in entry.rglob("*"):
            if item.is_dir() and _is_artifact(item):
                directories.append(item)
            elif item.is_file() and _is_artifact(item):
                files.append(item)

    # Drop files already covered by a scheduled directory.
    dir_set = {d.resolve() for d in directories}
    files = [f for f in files if not any(parent in dir_set for parent in f.resolve().parents)]
    return directories, files


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="clean_project",
        description="Remove repository-local generated artifacts (safe, conservative list).",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="List what would be removed; delete nothing."
    )
    parser.add_argument(
        "--force", action="store_true", help="Delete without interactive confirmation."
    )
    parser.add_argument(
        "--keep-logs", action="store_true", help="Keep the out/ directory (workflow logs)."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Repository root override (mainly for tests).",
    )
    args = parser.parse_args(argv)

    root = (args.root or _repo_root()).resolve()
    print(f"[INFO] Repository root: {root}")
    if args.dry_run:
        print("[INFO] DRY RUN - nothing will be deleted.")

    directories, files = collect_targets(root, keep_logs=args.keep_logs)

    for path in [*directories, *files]:
        if not is_safe_to_remove(path, root):
            print(f"[FAILED] Refusing unsafe removal target: {path}", file=sys.stderr)
            return 2

    if not directories and not files:
        print("[OK] Nothing to clean.")
        return 0

    print(f"[INFO] Planned removal: {len(directories)} directories, {len(files)} files.")
    for directory in directories:
        print(f"  [dir]  {directory}")
    for file in files:
        print(f"  [file] {file}")

    if args.dry_run:
        print("[OK] DRY RUN complete - nothing was deleted.")
        return 0

    if not args.force:
        answer = input("Delete the generated artifacts listed above? [y/N] ").strip().lower()
        if answer != "y":
            print("[INFO] Aborted by user. Nothing was deleted.")
            return 0

    had_errors = False
    for file in files:
        try:
            file.unlink()
        except OSError as exc:
            had_errors = True
            print(f"[FAILED] Could not remove file '{file}': {exc}", file=sys.stderr)
    for directory in sorted(directories, key=lambda p: len(str(p)), reverse=True):
        try:
            shutil.rmtree(directory)
        except OSError as exc:
            had_errors = True
            print(f"[FAILED] Could not remove directory '{directory}': {exc}", file=sys.stderr)

    if had_errors:
        print("[FAILED] Cleanup completed with errors.", file=sys.stderr)
        return 1
    print(f"[OK] Removed {len(directories)} directories and {len(files)} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
