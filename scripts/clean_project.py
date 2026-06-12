"""Безопасная очистка локальных артефактов репозитория IVA.

Скрипт удаляет только явно перечисленные результаты сборки, кэши и служебные
файлы. Он не пытается интерпретировать весь ``.gitignore``: такой подход мог бы
случайно захватить пользовательские данные или новые исходные каталоги.

Использование::

    python scripts/clean_project.py --dry-run
    python scripts/clean_project.py --force
    python scripts/clean_project.py --dry-run --keep-logs
    python scripts/clean_project.py --force --keep-logs
    python scripts/clean_project.py --dry-run --include-venv
    python scripts/clean_project.py --force --include-venv

Виртуальные окружения ``.venv/``, ``venv/`` и ``env/`` включаются в план
только с ``--include-venv``. Реальное удаление всегда требует ``--force``.

Коды возврата: 0 — успех, 1 — ошибка удаления, 2 — защитный отказ.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from collections.abc import Sequence
from pathlib import Path

__all__ = [
    "collect_targets",
    "is_safe_to_remove",
    "main",
    "validate_repository_root",
]

# Удаление ограничено закрытым списком известных артефактов верхнего уровня.
TOP_LEVEL_DIRS: tuple[str, ...] = (
    "reports",
    ".tmp",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "build",
    "dist",
)
LOGS_DIR_NAME = "out"
VENV_DIR_NAMES: tuple[str, ...] = (".venv", "venv", "env")

# Корни проекта нельзя удалять целиком. Вложенные __pycache__ и *.pyc при этом
# остаются допустимыми артефактами: исходный каталог сохраняется, кэш исчезает.
PROTECTED_ROOT_NAMES: tuple[str, ...] = (
    "iva",
    "docs",
    "documentation",
    "tests",
    "scripts",
    "config",
    "data",
    ".git",
)
PROTECTED_ROOT_FILES: tuple[str, ...] = (
    "README.md",
    "pyproject.toml",
    "requirements.txt",
    "requirements-dev.txt",
    "main.py",
)

_ARTIFACT_DIR_NAMES = ("__pycache__",)
_ARTIFACT_DIR_SUFFIXES = (".egg-info",)
_ARTIFACT_FILE_SUFFIXES = (".pyc", ".pyo")


def _repo_root() -> Path:
    """Определить корень независимо от текущего рабочего каталога."""
    return Path(__file__).resolve().parent.parent


def validate_repository_root(root: Path) -> Path:
    """Подтвердить, что *root* похож именно на репозиторий IVA.

    Проверка не позволяет ошибочно принять произвольный родительский каталог
    за корень и затем удалить одноимённые ``build/`` или ``out/``.
    """
    resolved = root.resolve()
    required = (resolved / "pyproject.toml", resolved / "iva", resolved / "scripts")
    if not required[0].is_file() or not all(path.is_dir() for path in required[1:]):
        raise ValueError("корень репозитория должен содержать pyproject.toml, iva/ и scripts/")
    return resolved


def _is_artifact(path: Path) -> bool:
    """Проверить путь по закрытому списку шаблонов артефактов."""
    name = path.name
    if name in _ARTIFACT_DIR_NAMES:
        return True
    if any(name.endswith(suffix) for suffix in _ARTIFACT_DIR_SUFFIXES):
        return True
    return any(name.endswith(suffix) for suffix in _ARTIFACT_FILE_SUFFIXES)


def is_safe_to_remove(path: Path, root: Path, *, include_venv: bool = False) -> bool:
    """Разрешить удаление только известного артефакта внутри *root*.

    Симлинки намеренно отклоняются даже тогда, когда их цель находится внутри
    репозитория. Это сохраняет простую гарантию: очистка никогда не следует по
    ссылкам и не затрагивает неожиданный каталог за пределами рабочего дерева.
    """
    root = root.resolve()
    if path.is_symlink():
        return False
    try:
        resolved = path.resolve()
        relative = resolved.relative_to(root)
    except (OSError, ValueError):
        return False
    if resolved == root:
        return False

    if relative.parts[0] in VENV_DIR_NAMES and not include_venv:
        return False

    if len(relative.parts) == 1:
        name = relative.parts[0]
        if name in PROTECTED_ROOT_NAMES or name in PROTECTED_ROOT_FILES:
            return False
        if name in TOP_LEVEL_DIRS or name == LOGS_DIR_NAME:
            return True
        if name in VENV_DIR_NAMES:
            return include_venv
        if name == ".coverage" or name.startswith(".coverage."):
            return True

    # Внутри исходных каталогов допустимы только точные шаблоны кэшей; обычный
    # файл Python или каталог слоя приложения сюда никогда не попадёт.
    return _is_artifact(resolved)


def collect_targets(
    root: Path,
    keep_logs: bool,
    include_venv: bool = False,
) -> tuple[list[Path], list[Path]]:
    """Собрать существующие артефакты как ``(directories, files)``."""
    directories: list[Path] = []
    files: list[Path] = []

    top_dirs = list(TOP_LEVEL_DIRS)
    if not keep_logs:
        top_dirs.append(LOGS_DIR_NAME)
    if include_venv:
        top_dirs.extend(VENV_DIR_NAMES)

    for name in top_dirs:
        candidate = root / name
        if candidate.is_symlink() or candidate.is_dir():
            directories.append(candidate)

    for candidate in root.glob(".coverage*"):
        if candidate.is_symlink() or candidate.is_file():
            files.append(candidate)

    # Уже выбранные целиком каталоги, .git и не включённые окружения обходить
    # бессмысленно и потенциально дорого. Остальные деревья нужны для поиска
    # вложенных __pycache__, *.egg-info, *.pyc и *.pyo.
    skipped_root_names = {".git", *top_dirs}
    if not include_venv:
        skipped_root_names.update(VENV_DIR_NAMES)

    for entry in root.iterdir():
        if entry.name in skipped_root_names or entry.is_symlink() or not entry.is_dir():
            continue
        for item in entry.rglob("*"):
            if item.is_symlink():
                if _is_artifact(item):
                    target_list = files if item.suffix in _ARTIFACT_FILE_SUFFIXES else directories
                    target_list.append(item)
                continue
            if item.is_dir() and _is_artifact(item):
                directories.append(item)
            elif item.is_file() and _is_artifact(item):
                files.append(item)

    directories = sorted(set(directories), key=lambda path: str(path).casefold())
    directory_roots = {path.resolve() for path in directories if not path.is_symlink()}
    files = [
        path
        for path in sorted(set(files), key=lambda item: str(item).casefold())
        if not any(parent in directory_roots for parent in path.resolve().parents)
    ]
    return directories, files


def _plan_statistics(directories: Sequence[Path], files: Sequence[Path]) -> tuple[int, int, int]:
    """Оценить число объектов и размер плана, не переходя по симлинкам."""
    directory_count = len(directories)
    file_count = len(files)
    total_bytes = 0

    for file in files:
        if file.is_symlink():
            continue
        try:
            total_bytes += file.stat().st_size
        except OSError:
            pass

    for directory in directories:
        if directory.is_symlink() or not directory.is_dir():
            continue
        for item in directory.rglob("*"):
            if item.is_symlink():
                continue
            try:
                if item.is_dir():
                    directory_count += 1
                elif item.is_file():
                    file_count += 1
                    total_bytes += item.stat().st_size
            except OSError:
                continue
    return directory_count, file_count, total_bytes


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="clean_project",
        description="Безопасно удалить локальные сгенерированные артефакты IVA.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Показать план без удаления.")
    parser.add_argument("--force", action="store_true", help="Разрешить реальное удаление.")
    parser.add_argument("--keep-logs", action="store_true", help="Сохранить каталог out/.")
    parser.add_argument(
        "--include-venv",
        action="store_true",
        help="Явно включить .venv/, venv/ и env/ в план очистки.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Переопределить корень репозитория (используется тестами).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    try:
        root = validate_repository_root(args.root or _repo_root())
    except ValueError as exc:
        print(f"[FAILED] Защитный отказ: {exc}.", file=sys.stderr)
        return 2

    print(f"[INFO] Корень репозитория: {root}")
    if not args.dry_run and not args.force:
        print(
            "[FAILED] Реальное удаление требует явного флага --force. "
            "Сначала используйте --dry-run.",
            file=sys.stderr,
        )
        return 2

    directories, files = collect_targets(
        root,
        keep_logs=args.keep_logs,
        include_venv=args.include_venv,
    )

    for path in [*directories, *files]:
        if not is_safe_to_remove(path, root, include_venv=args.include_venv):
            print(f"[FAILED] Отказ от небезопасной цели: {path}", file=sys.stderr)
            return 2

    protected = [name for name in PROTECTED_ROOT_NAMES if (root / name).exists()]
    print(f"[INFO] Защищённые корни не удаляются: {', '.join(protected)}")
    if args.include_venv:
        print("[WARN] Виртуальные окружения явно включены в план очистки.")
    else:
        print("[INFO] Виртуальные окружения сохранены (нет --include-venv).")

    if not directories and not files:
        print("[OK] Подходящих артефактов нет.")
        return 0

    directory_count, file_count, total_bytes = _plan_statistics(directories, files)
    total_mb = total_bytes / (1024 * 1024)
    print(
        f"[INFO] План: {directory_count} каталогов, {file_count} файлов, "
        f"примерно {total_mb:.2f} MB."
    )
    for directory in directories:
        print(f"  [dir]  {directory}")
    for file in files:
        print(f"  [file] {file}")

    if args.dry_run:
        print("[OK] DRY RUN завершён: ничего не удалено.")
        return 0

    had_errors = False
    for file in files:
        try:
            file.unlink()
        except OSError as exc:
            had_errors = True
            print(f"[FAILED] Не удалось удалить файл '{file}': {exc}", file=sys.stderr)
    for directory in sorted(directories, key=lambda path: len(str(path)), reverse=True):
        try:
            shutil.rmtree(directory)
        except OSError as exc:
            had_errors = True
            print(f"[FAILED] Не удалось удалить каталог '{directory}': {exc}", file=sys.stderr)

    if had_errors:
        print("[FAILED] Очистка завершилась с ошибками.", file=sys.stderr)
        return 1
    print(
        f"[OK] Удалено: {directory_count} каталогов, {file_count} файлов, "
        f"освобождено примерно {total_mb:.2f} MB."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
