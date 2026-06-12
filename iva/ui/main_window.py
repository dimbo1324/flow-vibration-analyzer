"""IVA main application window.

Architecture rules:
- No numerical calculations here.
- All session state lives in AnalysisSession.
- Worker runs in Qt thread pool via AnalysisWorker (in iva/ui/).
"""

from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import (  # type: ignore[import-untyped]
    QEasingCurve,
    QPropertyAnimation,
    QSettings,
    QSize,
    Qt,
    QThreadPool,
    QTimer,
    Slot,
)
from PySide6.QtGui import QAction, QKeySequence, QShortcut  # type: ignore[import-untyped]
from PySide6.QtWidgets import (  # type: ignore[import-untyped]
    QDialog,
    QDialogButtonBox,
    QDockWidget,
    QFileDialog,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSplitter,
    QStackedWidget,
    QStyle,
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
from iva.ui.strings_ru import tr
from iva.ui.styles.theme import (
    ANIM_NORMAL_MS,
    COLOR_ACCENT,
    COLOR_BAD,
    COLOR_BORDER,
    COLOR_MUTED,
    COLOR_PANEL,
    COLOR_SURFACE,
)
from iva.ui.widgets.chart_widget import ChartWidget
from iva.ui.widgets.inspector_panel import InspectorPanel

__all__ = ["MainWindow"]


class MainWindow(QMainWindow):
    """IVA top-level application window.

    Layout::

        ┌──────────────────────────────────────────────┐
        │  Toolbar                                      │
        ├──────────────────────────────────────────────┤
        │ Error banner  (hidden by default)             │
        ├────────────┬──────────────────────┬──────────┤
        │ Navigation │ Central workspace    │ Inspector│
        └────────────┴──────────────────────┴──────────┘
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
        self._ui_settings = QSettings("IVA", "Industrial Vibration Analyzer")
        self._persist_ui_state = os.environ.get("QT_QPA_PLATFORM") != "offscreen"
        self._sidebar_compact = False
        self._focus_mode = False
        self._focus_previous_page_index = 0
        self._focus_previous_sidebar_visible = True
        self._focus_previous_inspector_visible = False
        self._setup_ui()
        self._setup_shortcuts()
        self._load_defaults()
        self._restore_ui_preferences()
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

        self._action_sidebar = QAction("Свернуть навигацию  (L)", self)
        self._action_sidebar.setToolTip("Переключить компактный режим навигации (L)")
        self._action_sidebar.triggered.connect(self._toggle_sidebar)

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
        toolbar.addSeparator()
        toolbar.addAction(self._action_sidebar)
        toolbar.addAction(self._action_inspector)
        self.addToolBar(toolbar)

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

        # Workstation shell: navigation + workspace + inspector.
        self._main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self._main_splitter.setObjectName("MainWorkstationSplitter")
        self._main_splitter.setChildrenCollapsible(False)

        self._sidebar_panel = QWidget()
        self._sidebar_panel.setObjectName("SidebarPanel")
        self._sidebar_panel.setMinimumWidth(180)
        self._sidebar_panel.setMaximumWidth(320)
        sidebar_layout = QVBoxLayout(self._sidebar_panel)
        sidebar_layout.setContentsMargins(8, 12, 8, 8)
        sidebar_layout.setSpacing(8)

        self._sidebar_title = QLabel("РАБОЧИЙ ПРОЦЕСС")
        self._sidebar_title.setStyleSheet(f"color: {COLOR_MUTED}; font-weight: 700;")
        sidebar_layout.addWidget(self._sidebar_title)

        self._nav = QListWidget()
        self._nav.setObjectName("SidebarNav")
        self._nav.setIconSize(QSize(22, 22))
        self._nav.setSpacing(3)
        standard_icons = (
            QStyle.StandardPixmap.SP_ComputerIcon,
            QStyle.StandardPixmap.SP_DialogOpenButton,
            QStyle.StandardPixmap.SP_MediaPlay,
            QStyle.StandardPixmap.SP_FileDialogDetailedView,
            QStyle.StandardPixmap.SP_DriveHDIcon,
            QStyle.StandardPixmap.SP_FileDialogContentsView,
            QStyle.StandardPixmap.SP_DialogSaveButton,
        )
        for page_name, icon_kind in zip(self.PAGE_NAMES, standard_icons, strict=True):
            item = QListWidgetItem(self.style().standardIcon(icon_kind), page_name)
            item.setToolTip(page_name)
            item.setSizeHint(QSize(0, 44))
            self._nav.addItem(item)
        self._nav.setStyleSheet(
            f"QListWidget {{ background: {COLOR_SURFACE};" f" border: 1px solid {COLOR_BORDER}; }}"
        )
        self._nav.currentRowChanged.connect(self._on_nav_changed)
        sidebar_layout.addWidget(self._nav, stretch=1)
        self._main_splitter.addWidget(self._sidebar_panel)

        # Central workspace contains normal pages and a chart-focus view.
        self._stack = QStackedWidget()
        self._stack.setObjectName("AnalysisPageStack")
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

        self._workspace_stack = QStackedWidget()
        self._workspace_stack.setObjectName("CentralWorkspace")
        self._workspace_stack.addWidget(self._stack)

        self._focus_container = QWidget()
        focus_layout = QVBoxLayout(self._focus_container)
        focus_layout.setContentsMargins(12, 10, 12, 12)
        focus_layout.setSpacing(8)
        focus_header = QHBoxLayout()
        self._focus_label = QLabel("Режим просмотра графика - Esc для выхода")
        self._focus_label.setStyleSheet(
            f"color: {COLOR_ACCENT}; background: {COLOR_PANEL}; padding: 8px;"
            f" border: 1px solid {COLOR_BORDER}; font-weight: 700;"
        )
        focus_exit = QPushButton("Вернуться  (Esc)")
        focus_exit.clicked.connect(self.exit_chart_focus_mode)
        focus_header.addWidget(self._focus_label, stretch=1)
        focus_header.addWidget(focus_exit)
        focus_layout.addLayout(focus_header)
        self._focus_chart = ChartWidget()
        focus_layout.addWidget(self._focus_chart, stretch=1)
        self._workspace_stack.addWidget(self._focus_container)
        self._main_splitter.addWidget(self._workspace_stack)

        for chart in self._stack.findChildren(ChartWidget):
            chart.focus_requested.connect(self.enter_chart_focus_mode)

        # QDockWidget is retained as the compatibility surface, but it lives
        # inside the splitter as a stable resizable inspector panel.
        self._inspector_dock = QDockWidget(tr("Inspector"), self._main_splitter)
        self._inspector_dock.setObjectName("InspectorDock")
        self._inspector_dock.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self._inspector_dock.setMinimumWidth(280)
        self._inspector_dock.setMaximumWidth(420)
        inspector_scroll = QScrollArea()
        inspector_scroll.setWidgetResizable(True)
        self._inspector_panel = InspectorPanel()
        self._inspector_text = self._inspector_panel._text
        inspector_scroll.setWidget(self._inspector_panel)
        self._inspector_dock.setWidget(inspector_scroll)
        self._main_splitter.addWidget(self._inspector_dock)
        self._inspector_dock.hide()

        self._main_splitter.setStretchFactor(0, 0)
        self._main_splitter.setStretchFactor(1, 1)
        self._main_splitter.setStretchFactor(2, 0)
        self._main_splitter.setSizes([240, 1040, 0])
        central_layout.addWidget(self._main_splitter, stretch=1)

        self.setCentralWidget(central)

        # ── Status bar ──────────────────────────────────────────────────
        self._status_label = QLabel(tr("Ready"))
        self._status_label.setStyleSheet(f"color: {COLOR_MUTED};")
        self.statusBar().addWidget(self._status_label)

        self._progress_bar = QProgressBar()
        self._progress_bar.setObjectName("analysisProgressBar")
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(True)
        self._progress_bar.setFixedWidth(190)
        self._progress_bar.hide()
        self.statusBar().addPermanentWidget(self._progress_bar)

        self._progress_label = QLabel("")
        self._progress_label.setStyleSheet(f"color: {COLOR_MUTED}; min-width: 38px;")
        self.statusBar().addPermanentWidget(self._progress_label)

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
        self._shortcut_focus = QShortcut(QKeySequence("F"), self)
        self._shortcut_focus.activated.connect(self._toggle_chart_focus_mode)  # type: ignore[attr-defined]
        self._shortcut_escape = QShortcut(QKeySequence("Esc"), self)
        self._shortcut_escape.activated.connect(self.exit_chart_focus_mode)  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # Default settings
    # ------------------------------------------------------------------

    def _load_defaults(self) -> None:
        try:
            settings = load_defaults()
            self._session.settings = settings
        except Exception:  # noqa: BLE001
            pass  # Use dataclass defaults on any failure

    def _restore_ui_preferences(self) -> None:
        sidebar_compact = False
        inspector_visible = False
        if self._persist_ui_state:
            sidebar_compact = bool(self._ui_settings.value("ui/sidebar_compact", False, type=bool))
            inspector_visible = bool(
                self._ui_settings.value("ui/inspector_visible", False, type=bool)
            )
        self._set_sidebar_compact(sidebar_compact, persist=False)
        self._set_inspector_visible(inspector_visible, persist=False)

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

        self._start_analysis_worker("Выполняется анализ...")

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
            self._start_analysis_worker("Выполняется демонстрационный анализ...")
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
        self._progress_bar.setValue(0)
        self._progress_bar.show()
        self._progress_label.setText("0%")
        self._set_pages_running_state(status_text)
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
        self._progress_bar.setValue(value)
        self._progress_bar.show()
        self._progress_label.setText(f"{value}%")

    @Slot(object)
    def _on_analysis_completed(self, result: object) -> None:
        from iva.core.models.analysis_result import AnalysisResult

        if not isinstance(result, AnalysisResult):
            return
        self._session.result = result
        self._action_run.setEnabled(True)
        self._progress_bar.setValue(100)
        self._progress_label.setText("100%")
        self._status_label.setText(tr("Analysis complete"))
        # Enable save/export now that we have a result
        self._action_save.setEnabled(True)
        self._action_save_as.setEnabled(True)
        self._action_export_report.setEnabled(True)
        if result.is_demo:
            self._status_label.setText("Демонстрационный анализ завершён")
        self._update_all_pages(result)
        self._update_inspector(result)
        QTimer.singleShot(1400, self._hide_completed_progress)

    @Slot(object)
    def _on_analysis_error(self, error: object) -> None:
        self._action_run.setEnabled(True)
        self._reset_progress()
        if isinstance(error, IVAError):
            self._set_pages_error_state(error.user_message)
            self.show_error_banner(error)
        else:
            self._set_pages_error_state("Не удалось построить данные для страницы.")
            self._status_label.setText(tr("Analysis failed"))

    @Slot(str)
    def _on_unexpected_error(self, message: str) -> None:
        self._action_run.setEnabled(True)
        self._reset_progress()
        self._set_pages_error_state("Не удалось построить данные для страницы.")
        self._status_label.setText(tr("Analysis failed"))
        QMessageBox.critical(
            self,
            tr("Unexpected Error"),
            f"Во время анализа произошла непредвиденная ошибка:\n\n{message}",
        )

    def _hide_completed_progress(self) -> None:
        if self._progress_bar.value() >= 100:
            self._progress_bar.hide()
            self._progress_label.clear()

    def _reset_progress(self) -> None:
        self._progress_bar.setValue(0)
        self._progress_bar.hide()
        self._progress_label.clear()

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

    def _set_pages_running_state(self, message: str) -> None:
        for page in self._pages:
            if hasattr(page, "set_running_state"):
                page.set_running_state(message)  # type: ignore[attr-defined]

    def _set_pages_error_state(self, message: str) -> None:
        for page in self._pages:
            if hasattr(page, "set_error_state"):
                page.set_error_state(message)  # type: ignore[attr-defined]

    def _set_pages_empty_state(self) -> None:
        for page in self._pages:
            if hasattr(page, "set_empty_state"):
                page.set_empty_state()  # type: ignore[attr-defined]

    def _update_inspector(self, result: object) -> None:
        from iva.core.models.analysis_result import AnalysisResult

        if not isinstance(result, AnalysisResult):
            return
        self._inspector_panel.update_result(result, self._current_project_path)

    # ------------------------------------------------------------------
    # Navigation helpers
    # ------------------------------------------------------------------

    @Slot(int)
    def _on_nav_changed(self, index: int) -> None:
        self._stack.setCurrentIndex(index)
        self._animate_page_transition()

    def _animate_page_transition(self) -> None:
        """Fade the freshly shown page in for a smooth, modern transition.

        Skipped in offscreen mode (tests/CI): without a running render loop
        the animation would never progress and the page would stay at the
        starting opacity.
        """
        if os.environ.get("QT_QPA_PLATFORM") == "offscreen":
            return
        page = self._stack.currentWidget()
        if page is None:
            return
        effect = QGraphicsOpacityEffect(page)
        page.setGraphicsEffect(effect)
        animation = QPropertyAnimation(effect, b"opacity", self)
        animation.setDuration(ANIM_NORMAL_MS)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        # Remove the effect afterwards: a lingering QGraphicsOpacityEffect
        # degrades chart canvas rendering quality.
        animation.finished.connect(lambda p=page: p.setGraphicsEffect(None))
        animation.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        self._page_fade_animation = animation

    def _toggle_sidebar(self) -> None:
        if self._focus_mode:
            return
        self._set_sidebar_compact(not self._sidebar_compact)

    def _set_sidebar_compact(self, compact: bool, persist: bool = True) -> None:
        self._sidebar_compact = compact
        width = 64 if compact else 240
        self._sidebar_panel.setMinimumWidth(width if compact else 180)
        self._sidebar_panel.setMaximumWidth(width if compact else 320)
        self._sidebar_title.setText("IVA" if compact else "РАБОЧИЙ ПРОЦЕСС")
        self._sidebar_title.setAlignment(
            Qt.AlignmentFlag.AlignCenter if compact else Qt.AlignmentFlag.AlignLeft
        )
        for index, page_name in enumerate(self.PAGE_NAMES):
            item = self._nav.item(index)
            if item is None:
                continue
            item.setText("" if compact else page_name)
            item.setToolTip(page_name)
            item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
                if compact
                else Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            )
        self._action_sidebar.setText(
            "Развернуть навигацию  (L)" if compact else "Свернуть навигацию  (L)"
        )
        sizes = self._main_splitter.sizes()
        central_width = max(sizes[1] if len(sizes) > 1 else 900, 400)
        inspector_width = sizes[2] if len(sizes) > 2 else 0
        self._main_splitter.setSizes([width, central_width, inspector_width])
        if persist and self._persist_ui_state:
            self._ui_settings.setValue("ui/sidebar_compact", compact)

    def _toggle_inspector(self) -> None:
        if self._focus_mode:
            return
        self._set_inspector_visible(self._inspector_dock.isHidden())

    def _set_inspector_visible(self, visible: bool, persist: bool = True) -> None:
        self._inspector_dock.setVisible(visible)
        self._action_inspector.setText(
            "Скрыть инспектор  (R)" if visible else "Показать инспектор  (R)"
        )
        sizes = self._main_splitter.sizes()
        sidebar_width = 64 if self._sidebar_compact else 240
        central_width = max(sizes[1] if len(sizes) > 1 else 900, 400)
        self._main_splitter.setSizes([sidebar_width, central_width, 320 if visible else 0])
        if persist and self._persist_ui_state:
            self._ui_settings.setValue("ui/inspector_visible", visible)

    def _toggle_chart_focus_mode(self) -> None:
        if self._focus_mode:
            self.exit_chart_focus_mode()
        else:
            self.enter_chart_focus_mode()

    @Slot(object)
    def enter_chart_focus_mode(self, chart: object | None = None) -> None:
        """Show a page chart in the central focus workspace without recalculation."""
        if self._focus_mode:
            return
        source_chart = chart if isinstance(chart, ChartWidget) else None
        if source_chart is None:
            page = self._stack.currentWidget()
            charts = page.findChildren(ChartWidget) if page is not None else []
            source_chart = charts[0] if charts else None
        if source_chart is None:
            self._status_label.setText("На текущей странице нет графика для просмотра")
            return

        self._focus_previous_page_index = self._stack.currentIndex()
        self._focus_previous_sidebar_visible = not self._sidebar_panel.isHidden()
        self._focus_previous_inspector_visible = not self._inspector_dock.isHidden()
        source_chart.copy_plot_to(self._focus_chart)
        self._focus_mode = True
        self._sidebar_panel.hide()
        self._inspector_dock.hide()
        self._workspace_stack.setCurrentWidget(self._focus_container)
        self._status_label.setText("Режим просмотра графика - Esc для выхода")

    @Slot()
    def exit_chart_focus_mode(self) -> None:
        """Restore the page, sidebar, and inspector state saved before focus mode."""
        if not self._focus_mode:
            return
        self._workspace_stack.setCurrentWidget(self._stack)
        self._stack.setCurrentIndex(self._focus_previous_page_index)
        self._sidebar_panel.setVisible(self._focus_previous_sidebar_visible)
        self._focus_mode = False
        self._set_sidebar_compact(self._sidebar_compact, persist=False)
        self._set_inspector_visible(
            self._focus_previous_inspector_visible,
            persist=False,
        )
        self._status_label.setText(tr("Ready"))

    def _new_session(self) -> None:
        """Clear the current session (Ctrl+N)."""
        self.exit_chart_focus_mode()
        self._session.clear()
        self._current_project_path = None
        self._action_save.setEnabled(False)
        self._action_save_as.setEnabled(False)
        self._action_export_report.setEnabled(False)
        for page in self._pages:
            if hasattr(page, "clear"):
                page.clear()  # type: ignore[attr-defined]
        self._inspector_panel.clear()
        self._reset_progress()
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
            if self._session.result is not None:
                self._update_inspector(self._session.result)
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
            else:
                self._set_pages_empty_state()
                self._inspector_panel.clear()
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
