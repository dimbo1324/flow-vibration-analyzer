"""Статические проверки Docker-автоматизации IVA.

Тесты не запускают Docker и не требуют его установки: они проверяют только
содержимое и структуру файлов конфигурации. Это позволяет CI убедиться в
корректности Docker-настроек, не имея самого Docker.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


# ---------------------------------------------------------------------------
# Наличие файлов
# ---------------------------------------------------------------------------


def test_dockerfile_exists() -> None:
    assert (ROOT / "Dockerfile").is_file()


def test_dockerignore_exists() -> None:
    assert (ROOT / ".dockerignore").is_file()


def test_docker_compose_exists() -> None:
    assert (ROOT / "docker-compose.yml").is_file()


def test_docker_script_exists() -> None:
    assert (ROOT / "scripts" / "docker.ps1").is_file()


# ---------------------------------------------------------------------------
# .dockerignore исключает локальные артефакты
# ---------------------------------------------------------------------------


def _dockerignore() -> str:
    return (ROOT / ".dockerignore").read_text(encoding="utf-8")


def test_dockerignore_excludes_venv() -> None:
    text = _dockerignore()
    assert ".venv/" in text


def test_dockerignore_excludes_build() -> None:
    text = _dockerignore()
    assert "build/" in text


def test_dockerignore_excludes_dist() -> None:
    text = _dockerignore()
    assert "dist/" in text


def test_dockerignore_excludes_out() -> None:
    text = _dockerignore()
    assert "out/" in text


def test_dockerignore_excludes_pytest_cache() -> None:
    text = _dockerignore()
    assert ".pytest_cache/" in text


def test_dockerignore_excludes_mypy_cache() -> None:
    text = _dockerignore()
    assert ".mypy_cache/" in text


def test_dockerignore_excludes_pycache() -> None:
    text = _dockerignore()
    assert "__pycache__/" in text


# ---------------------------------------------------------------------------
# Dockerfile: базовые контракты
# ---------------------------------------------------------------------------


def _dockerfile() -> str:
    return (ROOT / "Dockerfile").read_text(encoding="utf-8")


def test_dockerfile_uses_python_base_image() -> None:
    text = _dockerfile()
    assert "FROM python:" in text


def test_dockerfile_sets_headless_qt_env() -> None:
    text = _dockerfile()
    assert "QT_QPA_PLATFORM" in text
    assert "offscreen" in text


def test_dockerfile_sets_matplotlib_backend() -> None:
    text = _dockerfile()
    assert "MPLBACKEND" in text
    assert "Agg" in text


def test_dockerfile_installs_requirements() -> None:
    text = _dockerfile()
    assert "requirements" in text


def test_dockerfile_has_no_user_specific_paths() -> None:
    text = _dockerfile()
    assert "C:\\Users\\" not in text
    assert "/home/" not in text


# ---------------------------------------------------------------------------
# docker-compose.yml: ожидаемые сервисы
# ---------------------------------------------------------------------------


def _compose() -> str:
    return (ROOT / "docker-compose.yml").read_text(encoding="utf-8")


def test_compose_has_quality_service() -> None:
    assert "quality:" in _compose()


def test_compose_has_test_service() -> None:
    assert "test:" in _compose()


def test_compose_has_cli_demo_service() -> None:
    assert "cli-demo:" in _compose()


# ---------------------------------------------------------------------------
# scripts/docker.ps1: ожидаемые команды и безопасность
# ---------------------------------------------------------------------------


def _docker_script() -> str:
    return (ROOT / "scripts" / "docker.ps1").read_text(encoding="utf-8")


def test_docker_script_supports_build() -> None:
    assert '"build"' in _docker_script()


def test_docker_script_supports_quality() -> None:
    assert '"quality"' in _docker_script()


def test_docker_script_supports_test() -> None:
    assert '"test"' in _docker_script()


def test_docker_script_supports_cli_demo() -> None:
    assert '"cli-demo"' in _docker_script()


def test_docker_script_supports_shell() -> None:
    assert '"shell"' in _docker_script()


def test_docker_script_supports_clean() -> None:
    assert '"clean"' in _docker_script()


def test_docker_script_checks_docker_availability() -> None:
    text = _docker_script()
    # Скрипт должен проверять наличие Docker перед запуском команд.
    assert "docker" in text.lower()
    assert "Test-DockerAvailable" in text or "Get-Command docker" in text


def test_docker_script_has_no_user_specific_paths() -> None:
    text = _docker_script()
    assert "C:\\Users\\Users" not in text
    assert "C:\\Users\\dim" not in text
    assert "/home/" not in text


def test_docker_script_has_param_block() -> None:
    assert "param(" in _docker_script().lower()


def test_docker_script_has_exit_codes() -> None:
    assert "exit" in _docker_script().lower()
