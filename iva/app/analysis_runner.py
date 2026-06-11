"""Synchronous analysis runner — thin wrapper over the workflow coordinator.

On Stage 7 this is a plain synchronous call.  Stage 8 will add a
``QRunnable``-based wrapper for background execution in the GUI thread pool.

Architecture rule: this module must NOT import from ``iva.ui`` or ``PySide6``.
"""

from __future__ import annotations

from iva.app.analysis_session import AnalysisSession
from iva.app.workflow_coordinator import run_pipeline
from iva.core.models.analysis_result import AnalysisResult
from iva.infrastructure.logging.app_logger import get_logger

logger = get_logger(__name__)

__all__ = ["AnalysisRunner"]


class AnalysisRunner:
    """Thin wrapper that executes the analysis pipeline synchronously.

    Usage::

        runner = AnalysisRunner()
        result = runner.run(session)

    This class exists so that Stage 8 can introduce a ``QRunnable``-based
    subclass without changing the call sites.
    """

    def run(self, session: AnalysisSession) -> AnalysisResult:
        """Run the pipeline and return the result.

        Args:
            session: A prepared :class:`~iva.app.analysis_session.AnalysisSession`.

        Returns:
            A fully populated :class:`~iva.core.models.analysis_result.AnalysisResult`.

        Raises:
            IVAError: Any error raised by the pipeline is propagated as-is.
        """
        logger.info("AnalysisRunner.run called for '%s'", session.source_file_path)
        return run_pipeline(session)
