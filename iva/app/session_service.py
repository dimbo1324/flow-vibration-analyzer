"""Session save / load service — application-layer facade over session store.

Architecture rule: no numerical calculations here — only coordination.
Must NOT import from iva.ui or PySide6.
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
    """Save *session* to a ``.vibproj`` file and return the saved path.

    Args:
        session: The current analysis session.  Must have a result set.
        path: Destination path (extension added automatically if missing).

    Returns:
        Resolved path of the saved file.

    Raises:
        ExportError: If the session has no result or the write fails.
    """
    saved = save_project(session, path)
    logger.info("session_service.save_current_session: saved to '%s'", saved)
    return saved


def load_saved_session(path: str | Path) -> AnalysisSession:
    """Load a session from a ``.vibproj`` file.

    Chart arrays are restored from a bounded, decimated representation; the
    original source file remains authoritative for a fresh full analysis.

    Args:
        path: Path to the ``.vibproj`` file.

    Returns:
        Reconstructed :class:`AnalysisSession`.

    Raises:
        ValidationError: If the file is missing, corrupted, or unsupported.
    """
    session = load_project(path)
    logger.info(
        "session_service.load_saved_session: loaded session %s",
        session.result.session_id if session.result else "?",
    )
    return session
