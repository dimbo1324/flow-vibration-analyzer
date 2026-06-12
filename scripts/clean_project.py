"""Кроссплатформенная очистка сгенерированных артефактов репозитория.

Python-аналог ``scripts/clean.ps1`` для не-Windows оболочек и CI. Удаляет
только консервативный, жёстко заданный список сгенерированных артефактов:

- каталоги верхнего уровня: ``reports``, ``.tmp``, ``.pytest_cache``,
  ``.mypy_cache``, ``.ruff_cache``, ``build``, ``dist`` и (если не задан
  ``--keep-logs``) ``out``;
- файлы верхнего уровня: ``.coverage`` и ``.coverage.*``;
- в любом месте дерева: каталоги ``__pycache__`` и ``*.egg-info``,
  файлы ``*.pyc`` / ``*.pyo``.

Исходный код, docs, tests, config, демо-данные, ``.git`` и ``.venv`` НИКОГДА
не удаляются — это защита от случайной потери данных. Без ``--force`` (и без
``--dry-run``) скрипт запрашивает подтверждение перед удалением.

Использование::

    python scripts/clean_project.py --dry-run
    python scripts/clean_project.py --dry-run --keep-logs
    python scripts/clean_project.py --force

Коды возврата: 0 — успех/нечего делать, 1 — ошибки удаления, 2 — отказ по
соображениям безопасности (попытка удалить недопустимый путь).
"""

from __future__ import annotations

import argparse
import shutil
import sys
from collections.abc import Sequence
from pathlib import Path

__all__ = ["collect_targets", "is_safe_to_remove", "main"]

# Каталоги верхнего уровня, которые разрешено удалять целиком.
TOP_LEVEL_DIRS: tuple[str, ...] = (
    "reports",
    ".tmp",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "build",
    "dist",
)
# ``out`` содержит журналы workflow/diagnostics и сохраняется с --keep-logs.
LOGS_DIR_NAME = "out"

# Имена и расширения артефактов, допустимые в любой части дерева.
_ARTIFACT_DIR_NAMES = ("__pycache__",)
_ARTIFACT_DIR_SUFFIXES = (".egg-info",)
_ARTIFACT_FILE_SUFFIXES = (".pyc", ".pyo")

# Эти каталоги не обходятся и никогда не удаляются целиком.
_NEVER_TRAVERSE = (".git", ".venv", "venv")


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _is_artifact(path: Path) -> bool:
    """Проверить путь по закрытому списку шаблонов артефактов."""
    name = path.name
    if name in _ARTIFACT_DIR_NAMES:
        return True
    if any(name.endswith(sfx) for sfx in _ARTIFACT_DIR_SUFFIXES):
        return True
    return any(name.endswith(sfx) for sfx in _ARTIFACT_FILE_SUFFIXES)


def is_safe_to_remove(path: Path, root: Path) -> bool:
    """Разрешить удаление только известного артефакта внутри *root*.

    Путь должен находиться внутри *root* и быть либо одним из фиксированных
    элементов верхнего уровня, либо соответствовать шаблону ``__pycache__``,
    ``*.egg-info``, ``*.pyc`` или ``*.pyo``. Исходные файлы под ``iva/``,
    ``docs/``, ``tests/``, ``config/`` и ``data/`` всегда отклоняются.
    """
    path = path.resolve()
    root = root.resolve()
    if not path.is_relative_to(root) or path == root:
        return False
    rel = path.relative_to(root)
    if any(part in _NEVER_TRAVERSE for part in rel.parts):
        return False
    # Фиксированные элементы верхнего уровня.
    if len(rel.parts) == 1:
        name = rel.parts[0]
        if name in TOP_LEVEL_DIRS or name == LOGS_DIR_NAME:
            return True
        if name == ".coverage" or name.startswith(".coverage."):
            return True
    # Всё остальное обязано выглядеть как известный сгенерированный артефакт.
    return _is_artifact(path)


def collect_targets(root: Path, keep_logs: bool) -> tuple[list[Path], list[Path]]:
    """Собрать существующие артефакты как ``(directories, files)``."""
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

    # Файлы внутри уже выбранного каталога отдельно удалять не нужно.
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
