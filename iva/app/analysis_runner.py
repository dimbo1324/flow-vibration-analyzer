"""Синхронный запуск анализа поверх координатора конвейера.

Модуль намеренно не содержит вычислений и деталей Qt. Фоновый запуск для GUI
реализован отдельным ``QRunnable`` в слое ``iva.ui``, поэтому CLI может
использовать тот же координатор без зависимости от PySide6.

Архитектурное правило: импортировать ``iva.ui`` или ``PySide6`` здесь нельзя.
"""

from __future__ import annotations

from iva.app.analysis_session import AnalysisSession
from iva.app.workflow_coordinator import run_pipeline
from iva.core.models.analysis_result import AnalysisResult
from iva.infrastructure.logging.app_logger import get_logger

logger = get_logger(__name__)

__all__ = ["AnalysisRunner"]


class AnalysisRunner:
    """Синхронно выполнить единый конвейер анализа.

    Usage::

        runner = AnalysisRunner()
        result = runner.run(session)

    Класс служит стабильной точкой входа для CLI и GUI: UI оборачивает вызов в
    рабочий поток, не меняя контракт слоя приложения.
    """

    def run(self, session: AnalysisSession) -> AnalysisResult:
        """Запустить конвейер и вернуть полностью собранный результат.

        Args:
            session: Подготовленный сеанс анализа.

        Returns:
            Полностью заполненный ``AnalysisResult``.

        Raises:
            IVAError: Доменная ошибка конвейера передаётся вызывающему коду без подмены.
        """
        logger.info("AnalysisRunner.run called for '%s'", session.source_file_path)
        return run_pipeline(session)
