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
from iva.core.models.exceptions import ExportError, IVAError
from iva.ui.analysis_worker import AnalysisWorker
from iva.ui.pages.import_page import ImportPage
from iva.ui.pages.overview_page import OverviewPage
from iva.ui.pages.physics_page import PhysicsPage
from iva.ui.pages.profiles_page import ProfilesPage
from iva.ui.pages.report_page import ReportPage
from iva.ui.pages.signal_page import SignalPage
from iva.ui.pages.spectrum_page import SpectrumPage
from iva.ui.strings_ru import RISK_LABELS, display_label, tr
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
        tr("01  Overview"),
        tr("02  Import"),
        tr("03  Signal"),
        tr("04  Spectrum"),
        tr("05  Physics"),
        tr("06  Profiles"),
        tr("07  Report"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._session = AnalysisSession()
        self._thread_pool = QThreadPool.globalInstance()
        self._setup_ui()
        self._setup_shortcuts()
        self._load_defaults()
        self.setWindowTitle(tr("Industrial Vibration Analyzer (IVA)"))
        self.resize(1400, 900)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        # ── Toolbar ─────────────────────────────────────────────────────
        toolbar = QToolBar(tr("Main Toolbar"))
        toolbar.setMovable(False)
        toolbar.setObjectName("MainToolbar")

        self._action_open = QAction(tr("Open File  (Ctrl+O)"), self)
        self._action_open.setToolTip(tr("Open a data file (Ctrl+O)"))
        self._action_open.triggered.connect(self.open_file)

        self._action_run = QAction(tr("Run Analysis  (F5)"), self)
        self._action_run.setToolTip(tr("Run the full analysis pipeline (F5)"))
        self._action_run.triggered.connect(self.run_analysis)

        self._action_save = QAction(tr("Save Project  (Ctrl+S)"), self)
        self._action_save.setToolTip(tr("Save project session as .vibproj file (Ctrl+S)"))
        self._action_save.setEnabled(False)
        self._action_save.triggered.connect(self._save_project)

        self._action_save_as = QAction(tr("Save Project As…  (Ctrl+Shift+S)"), self)
        self._action_save_as.setToolTip(tr("Save project session with a new name (Ctrl+Shift+S)"))
        self._action_save_as.setEnabled(False)
        self._action_save_as.triggered.connect(self._save_project_as)

        self._action_open_project = QAction(tr("Open Project  (Ctrl+Shift+O)"), self)
        self._action_open_project.setToolTip(
            tr("Open a saved .vibproj session file (Ctrl+Shift+O)")
        )
        self._action_open_project.triggered.connect(self._open_project)

        self._action_new_session = QAction(tr("New Session  (Ctrl+N)"), self)
        self._action_new_session.setToolTip(tr("Clear current session (Ctrl+N)"))
        self._action_new_session.triggered.connect(self._new_session)

        self._action_export_report = QAction(tr("Export Report Bundle…"), self)
        self._action_export_report.setToolTip(
            tr("Export PDF, HTML, JSON and CSV reports to a directory")
        )
        self._action_export_report.setEnabled(False)
        self._action_export_report.triggered.connect(self._export_report_bundle)

        self._action_inspector = QAction(tr("Inspector  (R)"), self)
        self._action_inspector.setToolTip(tr("Toggle inspector panel (R)"))
        self._action_inspector.triggered.connect(self._toggle_inspector)

        toolbar.addAction(self._action_new_session)
        toolbar.addAction(self._action_open)
        toolbar.addAction(self._action_open_project)
        toolbar.addAction(self._action_run)
        toolbar.addSeparator()
        toolbar.addAction(self._action_save)
        toolbar.addAction(self._action_save_as)
        toolbar.addAction(self._action_export_report)
        toolbar.addAction(self._action_inspector)
        self.addToolBar(toolbar)

        # Store current project path for save (non-as)
        self._current_project_path: Path | None = None

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
        self._connect_quick_start_actions()

        content_layout.addWidget(self._nav)
        content_layout.addWidget(self._stack, stretch=1)
        central_layout.addWidget(content_widget, stretch=1)

        self.setCentralWidget(central)

        # ── Status bar ──────────────────────────────────────────────────
        self._status_label = QLabel(tr("Ready"))
        self._status_label.setStyleSheet(f"color: {COLOR_MUTED};")
        self.statusBar().addWidget(self._status_label)

        self._progress_label = QLabel("")
        self._progress_label.setStyleSheet(f"color: {COLOR_MUTED};")
        self.statusBar().addPermanentWidget(self._progress_label)

        # ── Inspector dock ──────────────────────────────────────────────
        self._inspector_dock = QDockWidget(tr("Inspector"), self)
        self._inspector_dock.setObjectName("InspectorDock")
        self._inspector_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        self._inspector_dock.setMinimumWidth(220)

        inspector_scroll = QScrollArea()
        inspector_scroll.setWidgetResizable(True)
        inspector_content = QWidget()
        inspector_layout = QVBoxLayout(inspector_content)
        inspector_layout.setContentsMargins(8, 8, 8, 8)

        self._inspector_text = QLabel(
            "Результат анализа пока отсутствует.\n\n" "Запустите анализ, чтобы увидеть подробности."
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
        sc_save.activated.connect(self._save_project)  # type: ignore[attr-defined]
        sc_save_as = QShortcut(QKeySequence("Ctrl+Shift+S"), self)
        sc_save_as.activated.connect(self._save_project_as)  # type: ignore[attr-defined]
        sc_open_proj = QShortcut(QKeySequence("Ctrl+Shift+O"), self)
        sc_open_proj.activated.connect(self._open_project)  # type: ignore[attr-defined]
        sc_new = QShortcut(QKeySequence("Ctrl+N"), self)
        sc_new.activated.connect(self._new_session)  # type: ignore[attr-defined]
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

    def _connect_quick_start_actions(self) -> None:
        overview_page = self._pages[0]
        import_page = self._pages[1]
        if isinstance(overview_page, OverviewPage):
            overview_page.open_file_requested.connect(self.open_file)
            overview_page.demo_requested.connect(self.run_demo_analysis)
            overview_page.open_project_requested.connect(self._open_project)
        if isinstance(import_page, ImportPage):
            import_page.demo_requested.connect(self.run_demo_analysis)

    # ------------------------------------------------------------------
    # Public slots
    # ------------------------------------------------------------------

    @Slot()
    def open_file(self) -> None:
        """Open a file-selection dialog and update the session."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            tr("Open Data File"),
            "",
            tr("Data Files (*.csv *.parquet *.xlsx);;CSV Files (*.csv);;All Files (*)"),
        )
        if path:
            self._session.source_file_path = Path(path)
            self._session.is_demo = False
            self._session.demo_scenario_key = None
            self._session.demo_title = None
            self._session.demo_description = None
            self._status_label.setText(f"Файл: {Path(path).name}")
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
                    "Не удалось запустить анализ: выберите файл данных и настройте "
                    "назначение столбцов на странице «Импорт»."
                ),
                technical_details="AnalysisSession.is_ready_for_analysis() returned False",
                recovery_hint="Нажмите «Открыть файл» (Ctrl+O) и выберите файл данных.",
            )
            self.show_error_banner(err)
            return

        self._start_analysis_worker(tr("Running analysis…"))

    @Slot()
    @Slot(str)
    def run_demo_analysis(self, scenario_key: str | None = None) -> None:
        """Prepare a built-in scenario and launch it in the background."""
        import_page = self._pages[1]
        selected_key = scenario_key
        if not selected_key and isinstance(import_page, ImportPage):
            selected_key = import_page.selected_demo_key()
        try:
            from iva.app.demo_service import create_demo_session

            self._session = create_demo_session(selected_key or "clean_40hz")
            if isinstance(import_page, ImportPage) and self._session.source_file_path is not None:
                assert self._session.role_assignment is not None
                import_page.set_demo_session(
                    self._session.demo_title or "Демо-сценарий",
                    self._session.demo_description or "",
                    self._session.source_file_path,
                    self._session.role_assignment.sampling_rate_hz,
                    self._session.role_assignment.signal_role,
                )
            physics_page = self._pages[4]
            flow_parameters = self._session.settings.flow_parameters
            if isinstance(physics_page, PhysicsPage) and flow_parameters is not None:
                physics_page.set_flow_parameters(flow_parameters)
            self._nav.setCurrentRow(0)
            self._start_analysis_worker("Демонстрационный анализ запущен")
        except IVAError as exc:
            self.show_error_banner(exc)
        except Exception as exc:  # noqa: BLE001
            self.show_error_banner(
                IVAError(
                    user_message="Не удалось подготовить демонстрационный анализ.",
                    technical_details=str(exc),
                    recovery_hint="Выберите другой демо-сценарий и повторите попытку.",
                )
            )

    def _start_analysis_worker(self, status_text: str) -> None:
        self._action_run.setEnabled(False)
        self._status_label.setText(status_text)
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
        self._status_label.setText(tr("Analysis complete"))
        # Enable save/export now that we have a result
        self._action_save.setEnabled(True)
        self._action_save_as.setEnabled(True)
        self._action_export_report.setEnabled(True)
        if result.is_demo:
            self._status_label.setText("Демонстрационный анализ завершен")
        self._update_all_pages(result)
        self._update_inspector(result)

    @Slot(object)
    def _on_analysis_error(self, error: object) -> None:
        self._action_run.setEnabled(True)
        self._progress_label.setText("")
        if isinstance(error, IVAError):
            self.show_error_banner(error)
        else:
            self._status_label.setText(tr("Analysis failed"))

    @Slot(str)
    def _on_unexpected_error(self, message: str) -> None:
        self._action_run.setEnabled(True)
        self._progress_label.setText("")
        self._status_label.setText(tr("Analysis failed"))
        QMessageBox.critical(
            self,
            tr("Unexpected Error"),
            f"Во время анализа произошла непредвиденная ошибка:\n\n{message}",
        )

    # ------------------------------------------------------------------
    # Error banner
    # ------------------------------------------------------------------

    def show_error_banner(self, error: IVAError) -> None:
        """Show the error banner with the user-facing message."""
        self._last_error = error
        self._error_banner.setText(f"⚠  {error.user_message}  — нажмите для подробностей")
        self._error_banner.setVisible(True)
        self._status_label.setText(tr("Error — see banner"))

    def _hide_error_banner(self) -> None:
        self._error_banner.setVisible(False)
        self._last_error = None

    def _on_banner_click(self, _event: object) -> None:  # noqa: ANN001
        """Show technical error details in a dialog."""
        if self._last_error is None:
            return
        dlg = QDialog(self)
        dlg.setWindowTitle(tr("Error Details"))
        dlg.resize(600, 300)
        layout = QVBoxLayout(dlg)

        text = QTextEdit()
        text.setReadOnly(True)
        lines = [f"Сообщение: {self._last_error.user_message}"]
        if self._last_error.technical_details:
            lines.append(f"\nТехнические сведения:\n{self._last_error.technical_details}")
        if self._last_error.recovery_hint:
            lines.append(f"\nКак исправить:\n{self._last_error.recovery_hint}")
        text.setPlainText("\n".join(lines))
        layout.addWidget(text)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close_button = buttons.button(QDialogButtonBox.StandardButton.Close)
        if close_button is not None:
            close_button.setText("Закрыть")
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
        if result.is_demo:
            lines.append("ДЕМО: синтетические данные")
            if result.demo_title:
                lines.append(result.demo_title)
            lines.append("")
        if result.spectrum and result.spectrum.dominant_peak:
            pk = result.spectrum.dominant_peak
            lines.append(f"Пик: {pk.frequency_hz:.2f} Hz")
            lines.append(f"  амплитуда: {pk.amplitude:.4g}")
        if result.spectrum:
            lines.append(f"RMS: {result.spectrum.rms_total:.4g}")
        if result.physics:
            ph = result.physics
            lines.append(f"Re: {ph.reynolds_number:.2e}")
            lines.append(f"St: {ph.strouhal_number:.4f}")
            lines.append(f"fs: {ph.calculated_shedding_frequency_hz:.3f} Hz")
        if result.risk:
            lines.append(f"Риск: {display_label(RISK_LABELS, result.risk.risk_level)}")
        if result.warnings:
            lines.append(f"\nПредупреждения: {len(result.warnings)}")
        self._inspector_text.setText(
            "\n".join(lines) if lines else "Анализ завершен — подробности отсутствуют"
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

    def _new_session(self) -> None:
        """Clear the current session (Ctrl+N)."""
        self._session.clear()
        self._current_project_path = None
        self._action_save.setEnabled(False)
        self._action_save_as.setEnabled(False)
        self._action_export_report.setEnabled(False)
        for page in self._pages:
            if hasattr(page, "clear"):
                page.clear()  # type: ignore[attr-defined]
        self._inspector_text.clear()
        self.setWindowTitle(tr("Industrial Vibration Analyzer (IVA)"))
        self._status_label.setText(tr("New session started"))
        self._hide_error_banner()

    def _save_project(self) -> None:
        """Save to existing path or prompt for new path (Ctrl+S)."""
        if self._session.result is None:
            self._status_label.setText(tr("Nothing to save — run an analysis first"))
            return
        if self._current_project_path is not None:
            self._do_save_project(self._current_project_path)
        else:
            self._save_project_as()

    def _save_project_as(self) -> None:
        """Prompt for a path and save (Ctrl+Shift+S)."""
        if self._session.result is None:
            self._status_label.setText(tr("Nothing to save — run an analysis first"))
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            tr("Save Project As"),
            "project.vibproj",
            tr("IVA Project Files (*.vibproj);;All Files (*)"),
        )
        if path:
            self._do_save_project(Path(path))

    def _do_save_project(self, path: Path) -> None:
        try:
            from iva.app.session_service import save_current_session

            saved = save_current_session(self._session, path)
            self._current_project_path = saved
            self.setWindowTitle(f"IVA — {saved.name}")
            self._status_label.setText(f"Проект сохранен: {saved.name}")
        except Exception as exc:  # noqa: BLE001
            err = ExportError(
                user_message=f"Не удалось сохранить проект: {exc}",
                technical_details=str(exc),
            )
            self.show_error_banner(err)

    def _open_project(self) -> None:
        """Open a .vibproj session file (Ctrl+Shift+O)."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            tr("Open Project"),
            "",
            tr("IVA Project Files (*.vibproj);;All Files (*)"),
        )
        if not path:
            return
        try:
            from iva.app.session_service import load_saved_session

            loaded = load_saved_session(path)
            self._session = loaded
            self._current_project_path = Path(path)
            self.setWindowTitle(f"IVA — {Path(path).name}")
            self._status_label.setText(f"Проект загружен: {Path(path).name}")
            self._action_save.setEnabled(True)
            self._action_save_as.setEnabled(True)
            self._action_export_report.setEnabled(loaded.result is not None)
            if loaded.result is not None:
                self._update_all_pages(loaded.result)
                self._update_inspector(loaded.result)
            self._hide_error_banner()
        except Exception as exc:  # noqa: BLE001
            from iva.core.models.exceptions import IVAError as _IVAError

            if isinstance(exc, _IVAError):
                self.show_error_banner(exc)
            else:
                err = ExportError(
                    user_message=f"Не удалось открыть проект: {exc}",
                    technical_details=str(exc),
                )
                self.show_error_banner(err)

    def _export_report_bundle(self) -> None:
        """Export all report formats to a directory."""
        if self._session.result is None:
            self._status_label.setText(tr("Nothing to export — run an analysis first"))
            return
        output_dir = QFileDialog.getExistingDirectory(
            self, tr("Select Output Directory for Report Bundle")
        )
        if not output_dir:
            return
        try:
            from iva.app.report_service import export_report_bundle

            written = export_report_bundle(self._session.result, output_dir)
            self._status_label.setText(
                f"Экспортировано файлов: {len(written)}; папка: {Path(output_dir).name}"
            )
        except Exception as exc:  # noqa: BLE001
            err = ExportError(
                user_message=f"Не удалось экспортировать отчет: {exc}",
                technical_details=str(exc),
            )
            self.show_error_banner(err)
