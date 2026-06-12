"""Фасад слоя приложения для сохранения и загрузки сеансов.

Здесь допустима только координация хранилища: численные расчёты и зависимости
от ``iva.ui``/PySide6 нарушили бы границы архитектуры.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from iva.infrastructure.session.session_store import load_project, save_project

if TYPE_CHECKING:
    from iva.app.analysis_session import AnalysisSession

logger = logging.getLogger(__name__)

__all__ = ["save_current_session", "load_saved_session"]


def save_current_session(session: AnalysisSession, path: str | Path) -> Path:
    """Сохранить *session* в ``.vibproj`` и вернуть итоговый путь.

    Args:
        session: Текущий сеанс с уже рассчитанным результатом.
        path: Путь назначения; расширение добавляется автоматически.

    Returns:
        Нормализованный путь сохранённого файла.

    Raises:
        ExportError: Если результата нет или запись завершилась ошибкой.
    """
    saved = save_project(session, path)
    logger.info("session_service.save_current_session: saved to '%s'", saved)
    return saved


def load_saved_session(path: str | Path) -> AnalysisSession:
    """Загрузить сеанс из файла ``.vibproj``.

    Массивы графиков восстанавливаются из ограниченного прореженного
    представления. Для нового полного расчёта первоисточником остаётся исходный
    файл данных, а не содержимое сохранённого проекта.

    Args:
        path: Путь к файлу ``.vibproj``.

    Returns:
        Восстановленный ``AnalysisSession``.

    Raises:
        ValidationError: Если файл отсутствует, повреждён или имеет неподдерживаемую схему.
    """
    session = load_project(path)
    logger.info(
        "session_service.load_saved_session: loaded session %s",
        session.result.session_id if session.result else "?",
    )
    return session
