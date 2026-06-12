"""Сбор и вывод диагностики проекта IVA.

Запуск из корня репозитория::

    python scripts/diagnose_project.py

Скрипт пишет диагностику с меткой времени в out/diagnostics/ и выводит её же
в консоль. Секреты и большие журналы намеренно не включаются — диагностику
безопасно прикладывать к отчёту о проблеме.

Используется только стандартная библиотека (кроме проверки версий
сторонних пакетов через их импорт).
"""

from __future__ import annotations

import datetime
import importlib
import os
import platform
import subprocess
import sys
from pathlib import Path

# Корень репозитория вычисляется относительно файла, а не от текущего каталога,
# чтобы диагностику можно было запускать откуда угодно.
_ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------


def _get_out_dir() -> Path:
    # Переменная IVA_OUT_DIR имеет приоритет (используется в тестах/CI, чтобы не
    # писать в общий out/).
    env = os.environ.get("IVA_OUT_DIR")
    if env:
        return Path(env)
    return _ROOT / "out"


def _get_diagnostics_dir() -> Path:
    d = _get_out_dir() / "diagnostics"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _pkg_version(pkg_name: str) -> str:
    """Вернуть версию установленного пакета или 'not installed'."""
    try:
        mod = importlib.import_module(pkg_name)
        return str(getattr(mod, "__version__", "unknown"))
    except ImportError:
        return "not installed"


def _project_version() -> str:
    """Прочитать версию приложения из единственного источника истины.

    Версия живёт в iva/__version__.py; читаем файл напрямую, чтобы не тянуть
    тяжёлые импорты пакета ради одной строки.
    """
    version_file = _ROOT / "iva" / "__version__.py"
    try:
        for line in version_file.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("__version__"):
                return line.split("=", 1)[1].strip().strip("\"'")
    except OSError:
        pass
    return "(unknown)"


def _git_info() -> dict[str, str]:
    """Вернуть ветку, краткий статус и последний коммит git."""
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
            # git может отсутствовать или каталог не быть репозиторием — это не
            # повод ронять всю диагностику.
            return "(unavailable)"

    info["branch"] = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    info["status"] = _run(["git", "status", "--short"])
    info["last_commit"] = _run(["git", "log", "--oneline", "-1"])
    return info


def _docs_status() -> list[str]:
    """Сообщить о каталоге документации и отсутствии устаревшего варианта."""
    lines: list[str] = []
    docs = _ROOT / "docs"
    legacy = _ROOT / "documentation"
    lines.append(f"docs/ present       : {'yes' if docs.is_dir() else 'NO'}")
    # Каталог documentation/ был переименован в docs/; его наличие — признак
    # незавершённой миграции и повод предупредить разработчика.
    lines.append(f"documentation/ stale: {'PRESENT (stale)' if legacy.is_dir() else 'absent'}")
    return lines


def _scripts_status() -> list[str]:
    """Проверить наличие ключевых скриптов автоматизации."""
    expected = [
        "iva.ps1",
        "setup.ps1",
        "run.ps1",
        "clean.ps1",
        "clean-logs.ps1",
        "quality.ps1",
        "build-all.ps1",
        "lib/IvaDevTools.psm1",
    ]
    lines: list[str] = []
    for rel in expected:
        present = (_ROOT / "scripts" / rel).is_file()
        lines.append(f"{rel:<22}: {'ok' if present else 'MISSING'}")
    return lines


def _artifacts_status() -> list[str]:
    """Показать, какие игнорируемые артефакты присутствуют в дереве.

    Это подсказка: например, наличие dist/ и build/ говорит о прошлой сборке,
    которую можно убрать через `iva.ps1 clean`.
    """
    lines: list[str] = []
    checks: list[tuple[str, Path]] = [
        ("out/", _ROOT / "out"),
        ("build/", _ROOT / "build"),
        ("dist/", _ROOT / "dist"),
        (".coverage", _ROOT / ".coverage"),
    ]
    for label, path in checks:
        lines.append(f"{label:<22}: {'present' if path.exists() else 'absent'}")
    egg = list(_ROOT.glob("*.egg-info"))
    lines.append(f"{'*.egg-info':<22}: {'present' if egg else 'absent'}")
    return lines


def _latest_log_file() -> str:
    """Вернуть путь к самому свежему iva_*.log или пояснение, что логов нет."""
    log_dir = _get_out_dir() / "logs"
    if not log_dir.exists():
        return "(no logs directory)"
    log_files = sorted(log_dir.glob("iva_*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not log_files:
        return "(no log files found)"
    return str(log_files[0])


def _latest_workflow_summary() -> str:
    """Вернуть путь к свежему out/workflow-runs/*/summary.txt, если есть."""
    runs_dir = _get_out_dir() / "workflow-runs"
    if not runs_dir.exists():
        return "(no workflow runs)"
    summaries = sorted(
        runs_dir.glob("*/summary.txt"), key=lambda p: p.stat().st_mtime, reverse=True
    )
    if not summaries:
        return "(no summary files)"
    return str(summaries[0])


# ---------------------------------------------------------------------------
# Сбор диагностики
# ---------------------------------------------------------------------------


def collect() -> list[str]:
    lines: list[str] = []
    ts = datetime.datetime.now().isoformat(timespec="seconds")

    lines.append("=" * 60)
    lines.append("IVA Project Diagnostics")
    lines.append(f"Generated: {ts}")
    lines.append(f"App version: {_project_version()}")
    lines.append("=" * 60)
    lines.append("")

    # Python и платформа
    lines.append("--- Python & Platform ---")
    lines.append(f"Python version : {sys.version}")
    lines.append(f"Platform       : {platform.platform()}")
    lines.append(f"Architecture   : {platform.machine()}")
    lines.append(f"OS             : {platform.system()} {platform.release()}")
    lines.append("")

    # Версии пакетов
    packages = [
        ("numpy", "numpy"),
        ("scipy", "scipy"),
        ("pandas", "pandas"),
        ("pyarrow", "pyarrow"),
        ("openpyxl", "openpyxl"),
        ("PySide6", "PySide6"),
        ("matplotlib", "matplotlib"),
        ("reportlab", "reportlab"),
    ]
    lines.append("--- Package Versions ---")
    for display_name, import_name in packages:
        lines.append(f"{display_name:<12}: {_pkg_version(import_name)}")
    lines.append("")

    # Документация
    lines.append("--- Documentation ---")
    lines.extend(_docs_status())
    lines.append("")

    # Скрипты автоматизации
    lines.append("--- Automation Scripts ---")
    lines.extend(_scripts_status())
    lines.append("")

    # Информация git
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

    # Сгенерированные артефакты
    lines.append("--- Generated Artifacts ---")
    lines.extend(_artifacts_status())
    lines.append("")

    # Пути вывода и журналы
    lines.append("--- Output Paths ---")
    out_dir = _get_out_dir()
    lines.append(f"out/ base        : {out_dir}")
    lines.append(f"Latest log       : {_latest_log_file()}")
    lines.append(f"Latest workflow  : {_latest_workflow_summary()}")
    lines.append("")

    lines.append("=" * 60)
    return lines


# ---------------------------------------------------------------------------
# Точка входа
# ---------------------------------------------------------------------------


def main() -> None:
    lines = collect()
    output = "\n".join(lines)

    # Вывод в консоль
    print(output)

    # Запись в файл с меткой времени
    diag_dir = _get_diagnostics_dir()
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = diag_dir / f"{ts}_diagnostics.txt"
    out_path.write_text(output + "\n", encoding="utf-8")

    print(f"\nDiagnostics written to: {out_path}")


if __name__ == "__main__":
    main()
