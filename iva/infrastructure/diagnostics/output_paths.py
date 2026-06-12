"""Определение каталогов ресурсов и результатов для разработки и сборки.

В сборке PyInstaller приложение может находиться в недоступном для записи
``Program Files``. Поэтому ресурсы читаются из каталога распаковки, а
создаваемые файлы направляются в пользовательский ``Documents/IVA/out``.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def is_frozen() -> bool:
    """Вернуть ``True``, если код запущен из сборки PyInstaller."""
    return bool(getattr(sys, "frozen", False))


def get_resource_root() -> Path:
    """Вернуть корень доступных только для чтения ресурсов.

    В сборке это каталог распаковки PyInstaller ``sys._MEIPASS``, куда spec
    помещает ``config/`` и ``data/examples/``. В разработке это корень репозитория.
    """
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return get_project_root()


def get_project_root() -> Path:
    """Вернуть корень репозитория относительно текущего модуля."""
    return Path(__file__).resolve().parents[3]


def _get_user_documents_out_dir() -> Path:
    """Вернуть доступный для записи каталог результатов установленного приложения."""
    userprofile = os.environ.get("USERPROFILE")
    base = Path(userprofile) if userprofile else Path.home()
    return base / "Documents" / "IVA" / "out"


def get_out_dir() -> Path:
    """Вернуть базовый каталог результатов с учётом ``IVA_OUT_DIR``.

    Сборка пишет в ``Documents/IVA/out``, поскольку обычный пользователь не
    может создавать файлы рядом с программой в ``Program Files``.
    """
    env = os.environ.get("IVA_OUT_DIR")
    if env:
        return Path(env)
    if is_frozen():
        return _get_user_documents_out_dir()
    return get_project_root() / "out"


def ensure_out_subdir(name: str) -> Path:
    """Создать и вернуть подкаталог ``out/<name>/``."""
    d = get_out_dir() / name
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_logs_dir() -> Path:
    return ensure_out_subdir("logs")


def get_test_results_dir() -> Path:
    return ensure_out_subdir("test-results")


def get_workflow_runs_dir() -> Path:
    return ensure_out_subdir("workflow-runs")


def get_cli_runs_dir() -> Path:
    return ensure_out_subdir("cli-runs")


def get_diagnostics_dir() -> Path:
    return ensure_out_subdir("diagnostics")
