"""IVA main application window.

Architecture rules:
- No numerical calculations here.
- All session state lives in AnalysisSession.
- Worker runs in Qt thread pool via AnalysisWorker (in iva/ui/).
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QThreadPool, Slot  # type: ignore[import-untyped]
from PySide6.QtGui import QAction, QKeySequence, QShortcut  # type: ignore[import-untyped]
from PySide6.QtWidgets import (  # type: ignore[import-untyped]
    QDialog,
    QDialogButtonBox,
    QDockWidget,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QScrollArea,
    QStackedWidget,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from iva.app.analysis_session import AnalysisSession
from iva.app.settings_manager import load_defaults
from iva.core.models.exceptions import IVAError
from iva.ui.analysis_worker import AnalysisWorker
from iva.ui.pages.import_page import ImportPage
from iva.ui.pages.overview_page import OverviewPage
from iva.ui.pages.physics_page import PhysicsPage
from iva.ui.pages.profiles_page import ProfilesPage
from iva.ui.pages.report_page import ReportPage
from iva.ui.pages.signal_page import SignalPage
from iva.ui.pages.spectrum_page import SpectrumPage
from iva.ui.styles.theme import (
    COLOR_BAD,
    COLOR_BORDER,
    COLOR_MUTED,
    COLOR_SURFACE,
    COLOR_TEXT,
)

__all__ = ["MainWindow"]


class MainWindow(QMainWindow):
    """IVA top-level application window.

    Layout::

        ┌──────────────────────────────────────────────┐
        │  Toolbar                                      │
        ├───────────────┬──────────────────────────────┤
        │ Error banner  (hidden by default)             │
        ├───────────────┬──────────────────────────────┤
        │  Sidebar nav  │  Stacked content pages       │
        └───────────────┴──────────────────────────────┘
        Status bar
    """

    PAGE_NAMES = [
        "01  Overview",
        "02  Import",
        "03  Signal",
        "04  Spectrum",
        "05  Physics",
        "06  Profiles",
        "07  Report",
    ]

    def __init__(self) -> None:
        super().__init__()
        self._session = AnalysisSession()
        self._thread_pool = QThreadPool.globalInstance()
        self._setup_ui()
        self._setup_shortcuts()
        self._load_defaults()
        self.setWindowTitle("Industrial Vibration Analyzer (IVA)")
        self.resize(1400, 900)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        # ── Toolbar ─────────────────────────────────────────────────────
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setObjectName("MainToolbar")

        self._action_open = QAction("Open File  (Ctrl+O)", self)
        self._action_open.setToolTip("Open a data file (Ctrl+O)")
        self._action_open.triggered.connect(self.open_file)

        self._action_run = QAction("Run Analysis  (F5)", self)
        self._action_run.setToolTip("Run the full analysis pipeline (F5)")
        self._action_run.triggered.connect(self.run_analysis)

        self._action_save = QAction("Save Report…  (Ctrl+S)", self)
        self._action_save.setToolTip("Save report — available in Stage 9")
        self._action_save.setEnabled(False)

        self._action_inspector = QAction("Inspector  (R)", self)
        self._action_inspector.setToolTip("Toggle inspector panel (R)")
        self._action_inspector.triggered.connect(self._toggle_inspector)

        toolbar.addAction(self._action_open)
        toolbar.addAction(self._action_run)
        toolbar.addSeparator()
        toolbar.addAction(self._action_save)
        toolbar.addAction(self._action_inspector)
        self.addToolBar(toolbar)

        # ── Central widget: error banner + sidebar + stack ──────────────
        central = QWidget()
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)

        # Error banner (hidden by default)
        self._error_banner = QLabel("")
        self._error_banner.setVisible(False)
        self._error_banner.setWordWrap(True)
        self._error_banner.setContentsMargins(12, 6, 12, 6)
        self._error_banner.setCursor(Qt.CursorShape.PointingHandCursor)
        self._error_banner.setStyleSheet(
            f"background: #2d1515; color: {COLOR_BAD};"
            f" padding: 8px 12px; border-bottom: 1px solid {COLOR_BAD};"
        )
        self._error_banner.mousePressEvent = self._on_banner_click  # type: ignore[method-assign]
        central_layout.addWidget(self._error_banner)

        # Content row: sidebar + stacked pages
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Sidebar navigation
        self._nav = QListWidget()
        self._nav.setObjectName("SidebarNav")
        self._nav.setFixedWidth(170)
        self._nav.addItems(self.PAGE_NAMES)
        self._nav.setStyleSheet(
            f"QListWidget {{ background: {COLOR_SURFACE};"
            f" border-right: 1px solid {COLOR_BORDER}; }}"
        )
        self._nav.currentRowChanged.connect(self._on_nav_changed)

        # Stacked pages
        self._stack = QStackedWidget()
        self._pages: list[QWidget] = [
            OverviewPage(),
            ImportPage(),
            SignalPage(),
            SpectrumPage(),
            PhysicsPage(),
            ProfilesPage(),
            ReportPage(),
        ]
        for page in self._pages:
            self._stack.addWidget(page)

        content_layout.addWidget(self._nav)
        content_layout.addWidget(self._stack, stretch=1)
        central_layout.addWidget(content_widget, stretch=1)

        self.setCentralWidget(central)

        # ── Status bar ──────────────────────────────────────────────────
        self._status_label = QLabel("Ready")
        self._status_label.setStyleSheet(f"color: {COLOR_MUTED};")
        self.statusBar().addWidget(self._status_label)

        self._progress_label = QLabel("")
        self._progress_label.setStyleSheet(f"color: {COLOR_MUTED};")
        self.statusBar().addPermanentWidget(self._progress_label)

        # ── Inspector dock ──────────────────────────────────────────────
        self._inspector_dock = QDockWidget("Inspector", self)
        self._inspector_dock.setObjectName("InspectorDock")
        self._inspector_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        self._inspector_dock.setMinimumWidth(220)

        inspector_scroll = QScrollArea()
        inspector_scroll.setWidgetResizable(True)
        inspector_content = QWidget()
        inspector_layout = QVBoxLayout(inspector_content)
        inspector_layout.setContentsMargins(8, 8, 8, 8)

        self._inspector_text = QLabel(
            "No analysis result yet.\n\nRun an analysis to see details here."
        )
        self._inspector_text.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self._inspector_text.setWordWrap(True)
        self._inspector_text.setStyleSheet(
            f"color: {COLOR_TEXT}; font-size: 11pt; font-family: monospace;"
        )
        inspector_layout.addWidget(self._inspector_text)
        inspector_layout.addStretch()
        inspector_scroll.setWidget(inspector_content)
        self._inspector_dock.setWidget(inspector_scroll)

        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._inspector_dock)
        self._inspector_dock.hide()

        # Select first page
        self._nav.setCurrentRow(0)

        # Keep a reference to stored IVAError for "Details" click
        self._last_error: IVAError | None = None

    # ------------------------------------------------------------------
    # Keyboard shortcuts
    # ------------------------------------------------------------------

    def _setup_shortcuts(self) -> None:
        # Use the (key, parent, slot) positional form for PySide6 compatibility.
        sc_open = QShortcut(QKeySequence("Ctrl+O"), self)
        sc_open.activated.connect(self.open_file)  # type: ignore[attr-defined]
        sc_run = QShortcut(QKeySequence("F5"), self)
        sc_run.activated.connect(self.run_analysis)  # type: ignore[attr-defined]
        sc_save = QShortcut(QKeySequence("Ctrl+S"), self)
        sc_save.activated.connect(self._save_placeholder)  # type: ignore[attr-defined]
        sc_side = QShortcut(QKeySequence("L"), self)
        sc_side.activated.connect(self._toggle_sidebar)  # type: ignore[attr-defined]
        sc_insp = QShortcut(QKeySequence("R"), self)
        sc_insp.activated.connect(self._toggle_inspector)  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # Default settings
    # ------------------------------------------------------------------

    def _load_defaults(self) -> None:
        try:
            settings = load_defaults()
            self._session.settings = settings
        except Exception:  # noqa: BLE001
            pass  # Use dataclass defaults on any failure

    # ------------------------------------------------------------------
    # Public slots
    # ------------------------------------------------------------------

    @Slot()
    def open_file(self) -> None:
        """Open a file-selection dialog and update the session."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Data File",
            "",
            "Data Files (*.csv *.parquet *.xlsx);;CSV Files (*.csv);;All Files (*)",
        )
        if path:
            self._session.source_file_path = Path(path)
            self._status_label.setText(f"File: {Path(path).name}")
            import_page = self._pages[1]
            if isinstance(import_page, ImportPage):
                import_page.set_file_path(Path(path))
            self._hide_error_banner()

    @Slot()
    def run_analysis(self) -> None:
        """Collect form values and launch the analysis worker."""
        # Pull role assignment from the Import page
        import_page = self._pages[1]
        if isinstance(import_page, ImportPage):
            ra = import_page.get_role_assignment()
            if ra is not None:
                self._session.role_assignment = ra

        # Pull flow parameters from the Physics page
        physics_page = self._pages[4]
        if isinstance(physics_page, PhysicsPage):
            fp = physics_page.get_flow_parameters()
            if fp is not None:
                from iva.core.models.settings import AnalysisSettings

                self._session.settings = AnalysisSettings(
                    preprocessing=self._session.settings.preprocessing,
                    spectral=self._session.settings.spectral,
                    flow_parameters=fp,
                )

        if not self._session.is_ready_for_analysis():
            err = IVAError(
                user_message=(
                    "Cannot run analysis: please select a data file and configure "
                    "column assignments on the Import page."
                ),
                technical_details="AnalysisSession.is_ready_for_analysis() returned False",
                recovery_hint="Use 'Open File' (Ctrl+O) to select a CSV file.",
            )
            self.show_error_banner(err)
            return

        self._action_run.setEnabled(False)
        self._status_label.setText("Running analysis…")
        self._hide_error_banner()

        worker = AnalysisWorker(self._session)
        worker.signals.progress_updated.connect(self._on_progress)
        worker.signals.analysis_completed.connect(self._on_analysis_completed)
        worker.signals.error_occurred.connect(self._on_analysis_error)
        worker.signals.unexpected_error_occurred.connect(self._on_unexpected_error)
        self._thread_pool.start(worker)

    # ------------------------------------------------------------------
    # Worker signal handlers
    # ------------------------------------------------------------------

    @Slot(int)
    def _on_progress(self, value: int) -> None:
        self._progress_label.setText(f"{value}%")

    @Slot(object)
    def _on_analysis_completed(self, result: object) -> None:
        from iva.core.models.analysis_result import AnalysisResult

        if not isinstance(result, AnalysisResult):
            return
        self._session.result = result
        self._action_run.setEnabled(True)
        self._progress_label.setText("")
        self._status_label.setText("Analysis complete")
        self._update_all_pages(result)
        self._update_inspector(result)

    @Slot(object)
    def _on_analysis_error(self, error: object) -> None:
        self._action_run.setEnabled(True)
        self._progress_label.setText("")
        if isinstance(error, IVAError):
            self.show_error_banner(error)
        else:
            self._status_label.setText("Analysis failed")

    @Slot(str)
    def _on_unexpected_error(self, message: str) -> None:
        self._action_run.setEnabled(True)
        self._progress_label.setText("")
        self._status_label.setText("Analysis failed")
        QMessageBox.critical(
            self,
            "Unexpected Error",
            f"An unexpected error occurred during analysis:\n\n{message}",
        )

    # ------------------------------------------------------------------
    # Error banner
    # ------------------------------------------------------------------

    def show_error_banner(self, error: IVAError) -> None:
        """Show the error banner with the user-facing message."""
        self._last_error = error
        self._error_banner.setText(f"⚠  {error.user_message}  — click for details")
        self._error_banner.setVisible(True)
        self._status_label.setText("Error — see banner")

    def _hide_error_banner(self) -> None:
        self._error_banner.setVisible(False)
        self._last_error = None

    def _on_banner_click(self, _event: object) -> None:  # noqa: ANN001
        """Show technical error details in a dialog."""
        if self._last_error is None:
            return
        dlg = QDialog(self)
        dlg.setWindowTitle("Error Details")
        dlg.resize(600, 300)
        layout = QVBoxLayout(dlg)

        text = QTextEdit()
        text.setReadOnly(True)
        lines = [f"Message: {self._last_error.user_message}"]
        if self._last_error.technical_details:
            lines.append(f"\nTechnical details:\n{self._last_error.technical_details}")
        if self._last_error.recovery_hint:
            lines.append(f"\nRecovery hint:\n{self._last_error.recovery_hint}")
        text.setPlainText("\n".join(lines))
        layout.addWidget(text)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)
        dlg.exec()

    # ------------------------------------------------------------------
    # Page updates
    # ------------------------------------------------------------------

    def _update_all_pages(self, result: object) -> None:
        for page in self._pages:
            if hasattr(page, "on_analysis_completed"):
                page.on_analysis_completed(result)  # type: ignore[arg-type]

    def _update_inspector(self, result: object) -> None:
        from iva.core.models.analysis_result import AnalysisResult

        if not isinstance(result, AnalysisResult):
            return
        lines: list[str] = []
        if result.spectrum and result.spectrum.dominant_peak:
            pk = result.spectrum.dominant_peak
            lines.append(f"Peak: {pk.frequency_hz:.2f} Hz")
            lines.append(f"  amp: {pk.amplitude:.4g}")
        if result.spectrum:
            lines.append(f"RMS: {result.spectrum.rms_total:.4g}")
        if result.physics:
            ph = result.physics
            lines.append(f"Re: {ph.reynolds_number:.2e}")
            lines.append(f"St: {ph.strouhal_number:.4f}")
            lines.append(f"fs: {ph.calculated_shedding_frequency_hz:.3f} Hz")
        if result.risk:
            lines.append(f"Risk: {result.risk.risk_level.upper()}")
        if result.warnings:
            lines.append(f"\nWarnings: {len(result.warnings)}")
        self._inspector_text.setText(
            "\n".join(lines) if lines else "Analysis complete — no details"
        )

    # ------------------------------------------------------------------
    # Navigation helpers
    # ------------------------------------------------------------------

    @Slot(int)
    def _on_nav_changed(self, index: int) -> None:
        self._stack.setCurrentIndex(index)

    def _toggle_sidebar(self) -> None:
        self._nav.setVisible(not self._nav.isVisible())

    def _toggle_inspector(self) -> None:
        self._inspector_dock.setVisible(not self._inspector_dock.isVisible())

    def _save_placeholder(self) -> None:
        self._status_label.setText("Save report: available in Stage 9")
