"""Tests verifying the web frontend and Docker integration files exist."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_web_frontend_dir_exists() -> None:
    assert (REPO_ROOT / "web" / "frontend").is_dir()


def test_web_frontend_package_json_exists() -> None:
    assert (REPO_ROOT / "web" / "frontend" / "package.json").is_file()


def test_docker_compose_has_web_backend() -> None:
    compose_text = (REPO_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    assert "web-backend" in compose_text


def test_docker_compose_has_web_frontend() -> None:
    compose_text = (REPO_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    assert "web-frontend" in compose_text


def test_dockerignore_excludes_node_modules() -> None:
    dockerignore_text = (REPO_ROOT / ".dockerignore").read_text(encoding="utf-8")
    assert "node_modules" in dockerignore_text


def test_backend_dockerfile_exists() -> None:
    assert (REPO_ROOT / "docker" / "backend.Dockerfile").is_file()


def test_requirements_web_exists() -> None:
    assert (REPO_ROOT / "requirements-web.txt").is_file()


def test_requirements_web_has_fastapi() -> None:
    content = (REPO_ROOT / "requirements-web.txt").read_text(encoding="utf-8")
    assert "fastapi" in content.lower()


def test_requirements_web_has_uvicorn() -> None:
    content = (REPO_ROOT / "requirements-web.txt").read_text(encoding="utf-8")
    assert "uvicorn" in content.lower()


def test_requirements_web_has_httpx() -> None:
    content = (REPO_ROOT / "requirements-web.txt").read_text(encoding="utf-8")
    assert "httpx" in content.lower()
