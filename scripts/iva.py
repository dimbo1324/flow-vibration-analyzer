#!/usr/bin/env python3
"""Кросс-платформенный диспетчер команд IVA.

Аналог scripts/iva.ps1, но работает на Windows, Linux и macOS без PowerShell.
Запускать из корня репозитория или из любого каталога — скрипт сам находит корень.

Использование::

    python scripts/iva.py setup
    python scripts/iva.py setup-web
    python scripts/iva.py smoke
    python scripts/iva.py quality
    python scripts/iva.py check
    python scripts/iva.py clean --dry-run
    python scripts/iva.py clean --force
    python scripts/iva.py web-backend
    python scripts/iva.py web-frontend
    python scripts/iva.py web-quality
    python scripts/iva.py docker-web-up
    python scripts/iva.py docker-web-down
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

# Корень репозитория — родитель каталога scripts/.
REPO_ROOT = Path(__file__).resolve().parent.parent
VENV_PYTHON_WIN = REPO_ROOT / ".venv" / "Scripts" / "python.exe"
VENV_PYTHON_UNIX = REPO_ROOT / ".venv" / "bin" / "python"


def _python() -> str:
    """Вернуть путь к интерпретатору .venv, если он существует, иначе — системный."""
    if VENV_PYTHON_WIN.exists():
        return str(VENV_PYTHON_WIN)
    if VENV_PYTHON_UNIX.exists():
        return str(VENV_PYTHON_UNIX)
    return sys.executable


def run(cmd: list[str], *, cwd: Path | None = None) -> int:
    """Запустить команду, вывести её на экран и вернуть код возврата."""
    cwd = cwd or REPO_ROOT
    print(f"\n[CMD] {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(cwd))
    return result.returncode


def die(msg: str, code: int = 1) -> None:
    """Вывести сообщение об ошибке и завершить процесс."""
    print(f"\n[FAILED] {msg}", file=sys.stderr)
    sys.exit(code)


def ok(msg: str) -> None:
    print(f"[OK] {msg}")


def info(msg: str) -> None:
    print(f"[INFO] {msg}")


# ---------------------------------------------------------------------------
# Команды
# ---------------------------------------------------------------------------


def cmd_setup() -> int:
    """Установить базовые зависимости разработки."""
    info("Установка зависимостей разработки ...")
    exe = _python()
    rc = run([exe, "-m", "pip", "install", "--upgrade", "pip"])
    if rc != 0:
        return rc
    rc = run([exe, "-m", "pip", "install", "-r", str(REPO_ROOT / "requirements-dev.txt")])
    if rc != 0:
        return rc
    rc = run([exe, "-m", "pip", "install", "-e", str(REPO_ROOT)])
    ok("Зависимости установлены. Запустите 'python scripts/iva.py setup-web' для веб-зависимостей.")
    return rc


def cmd_setup_web() -> int:
    """Установить веб-зависимости (FastAPI, uvicorn, httpx)."""
    info("Установка веб-зависимостей ...")
    exe = _python()
    rc = run([exe, "-m", "pip", "install", "-r", str(REPO_ROOT / "requirements-web.txt")])
    if rc != 0:
        return rc
    rc = run([exe, "-c", "import fastapi, uvicorn, httpx; print('web deps ok')"])
    if rc == 0:
        ok("Веб-зависимости установлены.")
    return rc


def cmd_smoke() -> int:
    """Безоконный smoke-тест приложения."""

    env = {
        **__import__("os").environ,
        "QT_QPA_PLATFORM": "offscreen",
        "QT_OPENGL": "software",
        "MPLBACKEND": "Agg",
    }
    exe = _python()
    info("Запуск smoke-теста ...")
    result = subprocess.run(
        [exe, str(REPO_ROOT / "main.py"), "--smoke-test"], env=env, cwd=str(REPO_ROOT)
    )
    return result.returncode


def cmd_quality() -> int:
    """Запустить полный набор проверок качества (lint + тесты)."""
    exe = _python()
    steps = [
        ([exe, "-m", "black", "--check", "."], "black"),
        ([exe, "-m", "ruff", "check", "."], "ruff"),
        ([exe, "-m", "mypy", "iva", "main.py"], "mypy"),
        ([exe, "-m", "pytest", "-m", "not performance", "-q"], "pytest"),
    ]
    for cmd_args, label in steps:
        info(f"Запуск {label} ...")
        rc = run(cmd_args)
        if rc != 0:
            die(f"{label} завершился с ошибкой (код {rc}).", rc)
    ok("Все проверки качества пройдены.")
    return 0


def cmd_check() -> int:
    """Запустить scripts/check_project.py."""
    return run([_python(), str(REPO_ROOT / "scripts" / "check_project.py")])


def cmd_clean(dry_run: bool, force: bool) -> int:
    """Очистить сгенерированные артефакты."""
    if not dry_run and not force:
        die("Укажите --dry-run или --force. Сначала рекомендуется --dry-run.")
    args = [_python(), str(REPO_ROOT / "scripts" / "clean_project.py")]
    if dry_run:
        args.append("--dry-run")
    if force:
        args.append("--force")
    return run(args)


def cmd_web_backend() -> int:
    """Запустить FastAPI бэкенд на 127.0.0.1:8000."""
    exe = _python()
    # Проверяем наличие fastapi перед запуском.
    check = subprocess.run([exe, "-c", "import fastapi"], capture_output=True)
    if check.returncode != 0:
        die("FastAPI не установлен. Запустите: python scripts/iva.py setup-web")
    info("Запуск FastAPI бэкенда на http://127.0.0.1:8000 ...")
    print("  Документация API: http://127.0.0.1:8000/docs")
    print("  Нажмите Ctrl+C для остановки.")
    return run(
        [
            exe,
            "-m",
            "uvicorn",
            "iva.api.main:app",
            "--reload",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
        ]
    )


def cmd_web_frontend() -> int:
    """Запустить React фронтенд (pnpm dev) на порту 5173."""
    frontend_dir = REPO_ROOT / "web" / "frontend"
    if not frontend_dir.exists():
        die(f"Каталог web/frontend не найден: {frontend_dir}")

    # Проверяем наличие pnpm.
    pnpm = shutil.which("pnpm")
    if pnpm is None:
        die(
            "pnpm не найден. Установите его командой:\n"
            "  corepack enable && corepack prepare pnpm@latest --activate"
        )

    node_modules = frontend_dir / "node_modules"
    if not node_modules.exists():
        info("node_modules не найден — запуск pnpm install ...")
        rc = run(["pnpm", "install"], cwd=frontend_dir)
        if rc != 0:
            return rc

    info("Запуск React фронтенда на http://localhost:5173 ...")
    print("  Нажмите Ctrl+C для остановки.")
    return run(["pnpm", "dev"], cwd=frontend_dir)


def cmd_web_quality() -> int:
    """Запустить проверки качества фронтенда (lint, typecheck, test, build)."""
    frontend_dir = REPO_ROOT / "web" / "frontend"
    steps = [
        (["pnpm", "lint"], "ESLint"),
        (["pnpm", "typecheck"], "TypeScript"),
        (["pnpm", "test", "--run"], "Vitest"),
        (["pnpm", "build"], "build"),
    ]
    for cmd_args, label in steps:
        info(f"Запуск {label} ...")
        rc = run(cmd_args, cwd=frontend_dir)
        if rc != 0:
            die(f"{label} завершился с ошибкой (код {rc}).", rc)
    ok("Все проверки фронтенда пройдены.")
    return 0


def cmd_docker_web_up() -> int:
    """Запустить web-backend и web-frontend через Docker Compose."""
    _check_docker()
    info("Запуск web-backend и web-frontend (docker compose up) ...")
    rc = run(["docker", "compose", "up", "--build", "-d", "web-backend", "web-frontend"])
    if rc == 0:
        ok("Веб-сервисы запущены. Откройте http://localhost:5173")
    return rc


def cmd_docker_web_down() -> int:
    """Остановить web-backend и web-frontend."""
    _check_docker()
    return run(["docker", "compose", "stop", "web-backend", "web-frontend"])


def _check_docker() -> None:
    """Завершить процесс, если Docker недоступен."""
    if shutil.which("docker") is None:
        die(
            "Docker не найден на PATH.\n"
            "Установите Docker Desktop: https://docs.docker.com/desktop/\n"
            "Docker — опциональный инструмент; для локальной разработки он не нужен."
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

COMMANDS = {
    "setup": "Установить базовые зависимости разработки",
    "setup-web": "Установить веб-зависимости (FastAPI, uvicorn, httpx)",
    "smoke": "Безоконный smoke-тест приложения",
    "quality": "Полный набор проверок качества (lint + тесты)",
    "check": "Запустить scripts/check_project.py",
    "clean": "Очистить артефакты (--dry-run / --force)",
    "web-backend": "Запустить FastAPI бэкенд (порт 8000)",
    "web-frontend": "Запустить React фронтенд (pnpm dev, порт 5173)",
    "web-quality": "Проверки качества фронтенда (lint, typecheck, test, build)",
    "docker-web-up": "Поднять веб-стек через Docker Compose",
    "docker-web-down": "Остановить веб-стек Docker Compose",
}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="IVA — кросс-платформенный диспетчер команд",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="\n".join(f"  {k:20s} {v}" for k, v in COMMANDS.items()),
    )
    p.add_argument(
        "command", choices=list(COMMANDS), metavar="команда", help="Команда для выполнения"
    )
    p.add_argument(
        "--dry-run", action="store_true", help="Показать, что будет удалено (только для clean)"
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Выполнить удаление без подтверждения (только для clean)",
    )
    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    cmd = args.command

    rc = 0
    if cmd == "setup":
        rc = cmd_setup()
    elif cmd == "setup-web":
        rc = cmd_setup_web()
    elif cmd == "smoke":
        rc = cmd_smoke()
    elif cmd == "quality":
        rc = cmd_quality()
    elif cmd == "check":
        rc = cmd_check()
    elif cmd == "clean":
        rc = cmd_clean(args.dry_run, args.force)
    elif cmd == "web-backend":
        rc = cmd_web_backend()
    elif cmd == "web-frontend":
        rc = cmd_web_frontend()
    elif cmd == "web-quality":
        rc = cmd_web_quality()
    elif cmd == "docker-web-up":
        rc = cmd_docker_web_up()
    elif cmd == "docker-web-down":
        rc = cmd_docker_web_down()
    else:
        parser.print_help()
        rc = 1

    sys.exit(rc)


if __name__ == "__main__":
    main()
