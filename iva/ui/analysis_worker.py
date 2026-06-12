"""Фоновый исполнитель анализа поверх пула потоков Qt.

Воркер намеренно расположен в ``iva/ui/`` (а не в ``iva/app/``): так слой
``iva/app/`` остаётся свободным от импортов PySide6 и может использоваться из
CLI без графического интерфейса. Это ключевая архитектурная граница проекта.

Архитектурное правило: здесь НЕ должно быть числовых расчётов — только вызовы
``iva.app``. Вся математика живёт в ``iva.core``.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, QRunnable, Signal  # type: ignore[import-untyped]

from iva.app.analysis_runner import AnalysisRunner
from iva.app.analysis_session import AnalysisSession
from iva.core.models.exceptions import IVAError

__all__ = ["AnalysisWorker", "AnalysisWorkerSignals"]


class AnalysisWorkerSignals(QObject):
    """Signals emitted by :class:`AnalysisWorker`."""

    #: Emits progress percentage (0–100).
    progress_updated = Signal(int)
    #: Emits the completed :class:`~iva.core.models.analysis_result.AnalysisResult`.
    analysis_completed = Signal(object)
    #: Emits an :class:`~iva.core.models.exceptions.IVAError` on domain error.
    error_occurred = Signal(object)
    #: Emits a plain string on unexpected Python exception.
    unexpected_error_occurred = Signal(str)


class AnalysisWorker(QRunnable):
    """Runs the analysis pipeline in the Qt global thread pool.

    Usage::

        worker = AnalysisWorker(session)
        worker.signals.analysis_completed.connect(my_slot)
        worker.signals.error_occurred.connect(my_error_slot)
        QThreadPool.globalInstance().start(worker)
    """

    def __init__(self, session: AnalysisSession) -> None:
        super().__init__()
        self.session = session
        self.signals = AnalysisWorkerSignals()
        self.setAutoDelete(True)

    def run(self) -> None:  # noqa: D102
        # Любой результат и любая ошибка передаются в основной поток только через
        # сигналы Qt: напрямую трогать виджеты из рабочего потока нельзя.
        # Доменные ошибки (IVAError) и непредвиденные исключения разделены,
        # чтобы интерфейс показал понятное сообщение, а не сырой traceback.
        try:
            self.signals.progress_updated.emit(10)
            runner = AnalysisRunner()
            result = runner.run(self.session)
            self.signals.progress_updated.emit(90)
            self.signals.analysis_completed.emit(result)
            self.signals.progress_updated.emit(100)
        except IVAError as exc:
            self.signals.error_occurred.emit(exc)
        except Exception as exc:  # noqa: BLE001
            self.signals.unexpected_error_occurred.emit(str(exc))
