"""Page 06 — Profiles: experiment vs CFD comparison (Stage 9)."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt  # type: ignore[import-untyped]
from PySide6.QtWidgets import (  # type: ignore[import-untyped]
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from iva.ui.strings_ru import tr
from iva.ui.styles.theme import (
    COLOR_GOOD,
    COLOR_MUTED,
    COLOR_WARN,
    SPACING_MD,
)
from iva.ui.widgets.chart_widget import ChartWidget
from iva.ui.widgets.page_header import PageHeader
from iva.ui.widgets.page_state import PageStateBanner

if TYPE_CHECKING:
    from iva.core.models.analysis_result import AnalysisResult

__all__ = ["ProfilesPage"]


class ProfilesPage(QWidget):
    """Experiment vs CFD profiles comparison page."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._experiment_path: Path | None = None
        self._cfd_path: Path | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_MD, SPACING_MD, SPACING_MD, SPACING_MD)
        layout.setSpacing(SPACING_MD)

        self._header = PageHeader("Профили", "Сравнение профилей скорости: эксперимент и CFD")
        layout.addWidget(self._header)

        self._state_banner = PageStateBanner()
        layout.addWidget(self._state_banner)

        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setObjectName("profilesPageSplitter")
        self._splitter.setChildrenCollapsible(False)

        chart_box = QGroupBox("Эксперимент / CFD")
        chart_layout = QVBoxLayout(chart_box)
        self._chart = ChartWidget()
        self._chart.setMinimumHeight(300)
        chart_layout.addWidget(self._chart)
        self._splitter.addWidget(chart_box)

        side_panel = QWidget()
        side_layout = QVBoxLayout(side_panel)
        side_layout.setContentsMargins(0, 0, 0, 0)
        side_layout.setSpacing(SPACING_MD)

        # File load buttons
        btn_box = QGroupBox(tr("Load Profile Files"))
        btn_layout = QVBoxLayout(btn_box)

        self._load_exp_btn = QPushButton(tr("Load Experiment CSV…"))
        self._load_exp_btn.setToolTip(
            "Загрузить CSV профиля эксперимента (столбцы coordinate и value)"
        )
        self._load_exp_btn.clicked.connect(self._on_load_experiment)

        self._load_cfd_btn = QPushButton(tr("Load CFD CSV…"))
        self._load_cfd_btn.setToolTip("Загрузить CSV профиля CFD (столбцы coordinate и value)")
        self._load_cfd_btn.clicked.connect(self._on_load_cfd)

        self._compare_btn = QPushButton(tr("Compare"))
        self._compare_btn.setEnabled(False)
        self._compare_btn.clicked.connect(self._on_compare)

        self._exp_file_label = QLabel(tr("No experiment file"))
        self._exp_file_label.setStyleSheet(f"color: {COLOR_MUTED}; font-size: 10pt;")

        self._cfd_file_label = QLabel(tr("No CFD file"))
        self._cfd_file_label.setStyleSheet(f"color: {COLOR_MUTED}; font-size: 10pt;")

        exp_row = QHBoxLayout()
        exp_row.addWidget(self._load_exp_btn)
        exp_row.addWidget(self._exp_file_label, stretch=1)
        cfd_row = QHBoxLayout()
        cfd_row.addWidget(self._load_cfd_btn)
        cfd_row.addWidget(self._cfd_file_label, stretch=1)
        btn_layout.addLayout(exp_row)
        btn_layout.addLayout(cfd_row)
        btn_layout.addWidget(self._compare_btn)
        side_layout.addWidget(btn_box)

        # Validation metrics
        self._validation_box = QGroupBox(tr("Validation Metrics"))
        val_layout = QVBoxLayout(self._validation_box)

        self._metrics_table = QTableWidget(0, 2)
        self._metrics_table.setHorizontalHeaderLabels([tr("Metric"), tr("Value")])
        self._metrics_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._metrics_table.setMinimumHeight(120)
        val_layout.addWidget(self._metrics_table)
        self._validation_box.setVisible(False)
        side_layout.addWidget(self._validation_box)

        # Status label
        self._status_label = QLabel("")
        self._status_label.setStyleSheet(f"color: {COLOR_MUTED}; font-size: 10pt;")
        side_layout.addWidget(self._status_label)
        side_layout.addStretch()

        self._splitter.addWidget(side_panel)
        self._splitter.setStretchFactor(0, 3)
        self._splitter.setStretchFactor(1, 1)
        self._splitter.setSizes([780, 360])
        layout.addWidget(self._splitter, stretch=1)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_load_experiment(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            tr("Load Experiment Profile CSV"),
            "",
            tr("CSV Files (*.csv);;All Files (*)"),
        )
        if path:
            self._experiment_path = Path(path)
            self._exp_file_label.setText(Path(path).name)
            self._exp_file_label.setStyleSheet(f"color: {COLOR_GOOD}; font-size: 10pt;")
            self._update_compare_btn()

    def _on_load_cfd(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            tr("Load CFD Profile CSV"),
            "",
            tr("CSV Files (*.csv);;All Files (*)"),
        )
        if path:
            self._cfd_path = Path(path)
            self._cfd_file_label.setText(Path(path).name)
            self._cfd_file_label.setStyleSheet(f"color: {COLOR_GOOD}; font-size: 10pt;")
            self._update_compare_btn()

    def _update_compare_btn(self) -> None:
        self._compare_btn.setEnabled(
            self._experiment_path is not None and self._cfd_path is not None
        )

    def _on_compare(self) -> None:
        if self._experiment_path is None or self._cfd_path is None:
            return
        try:
            from iva.app.profile_comparison_service import compare_profile_csv_files

            val = compare_profile_csv_files(self._experiment_path, self._cfd_path)
            self._show_metrics(val)
            self._chart.plot_profiles(
                val.coordinate_array,
                val.experiment_array,
                val.cfd_array,
            )
            self._set_status(tr("Comparison complete."), ok=True)
            self.set_result_state()
        except Exception as exc:  # noqa: BLE001
            self._set_status(f"Ошибка сравнения: {exc}", ok=False)
            self._validation_box.setVisible(False)
            self.set_error_state("Не удалось сравнить экспериментальный и CFD-профили.")

    def _show_metrics(self, val: object) -> None:
        """Populate the metrics table from a ValidationResult."""
        from iva.core.models.analysis_result import ValidationResult

        if not isinstance(val, ValidationResult):
            return

        mape_str = f"{val.mape:.4f} %" if val.is_mape_valid and val.mape is not None else "N/A"
        rows = [
            ("RMSE", f"{val.rmse:.6f}"),
            ("MAE", f"{val.mae:.6f}"),
            ("MAPE", mape_str),
            ("Коэффициент Пирсона r", f"{val.pearson_r:.6f}"),
        ]
        self._metrics_table.setRowCount(len(rows))
        for i, (metric, value) in enumerate(rows):
            self._metrics_table.setItem(i, 0, QTableWidgetItem(metric))
            self._metrics_table.setItem(i, 1, QTableWidgetItem(value))
        self._validation_box.setVisible(True)

    def _set_status(self, message: str, ok: bool = True) -> None:
        colour = COLOR_GOOD if ok else COLOR_WARN
        self._status_label.setStyleSheet(f"color: {colour}; font-size: 10pt;")
        self._status_label.setText(message)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def on_analysis_completed(self, result: AnalysisResult) -> None:
        """Show validation metrics if available in the analysis result."""
        if result.validation is None:
            self._validation_box.setVisible(False)
            self._state_banner.show_empty(
                "Профили сравнения не загружены. Добавьте экспериментальные и CFD-данные."
            )
            return

        self.set_result_state()
        val = result.validation
        self._show_metrics(val)
        self._chart.plot_profiles(
            val.coordinate_array,
            val.experiment_array,
            val.cfd_array,
        )

    def set_empty_state(self) -> None:
        """Show the initial page state."""
        self._state_banner.show_empty(
            "Результаты сравнения пока отсутствуют. Загрузите профили или выполните анализ."
        )

    def set_running_state(self, message: str = "") -> None:
        """Show that the current analysis is running."""
        self._state_banner.show_running(message)

    def set_error_state(self, message: str) -> None:
        """Show a profile-page error."""
        self._state_banner.show_error(message)

    def set_result_state(self) -> None:
        """Hide the state banner when comparison data is available."""
        self._state_banner.show_result()

    def clear(self) -> None:
        """Reset the page."""
        self._metrics_table.setRowCount(0)
        self._validation_box.setVisible(False)
        self._chart.clear()
        self._status_label.setText("")
        self._experiment_path = None
        self._cfd_path = None
        self._exp_file_label.setText(tr("No experiment file"))
        self._exp_file_label.setStyleSheet(f"color: {COLOR_MUTED}; font-size: 10pt;")
        self._cfd_file_label.setText(tr("No CFD file"))
        self._cfd_file_label.setStyleSheet(f"color: {COLOR_MUTED}; font-size: 10pt;")
        self._compare_btn.setEnabled(False)
        self.set_empty_state()
