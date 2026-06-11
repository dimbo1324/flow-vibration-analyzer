"""Page 06 — Profiles: experiment vs CFD comparison (Stage 9)."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtWidgets import (  # type: ignore[import-untyped]
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from iva.ui.styles.theme import (
    COLOR_GOOD,
    COLOR_MUTED,
    COLOR_TEXT,
    COLOR_WARN,
    FONT_SIZE_TITLE,
    SPACING_MD,
)
from iva.ui.widgets.chart_widget import ChartWidget

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

        title = QLabel("06 — Profiles")
        title.setStyleSheet(
            f"font-size: {FONT_SIZE_TITLE}pt; font-weight: bold; color: {COLOR_TEXT};"
        )
        layout.addWidget(title)

        subtitle = QLabel("Experiment vs CFD velocity profile comparison")
        subtitle.setStyleSheet(f"color: {COLOR_MUTED}; font-size: 11pt;")
        layout.addWidget(subtitle)

        # File load buttons
        btn_box = QGroupBox("Load Profile Files")
        btn_layout = QHBoxLayout(btn_box)

        self._load_exp_btn = QPushButton("Load Experiment CSV…")
        self._load_exp_btn.setToolTip(
            "Load experimental profile CSV (two columns: coordinate, value)"
        )
        self._load_exp_btn.clicked.connect(self._on_load_experiment)

        self._load_cfd_btn = QPushButton("Load CFD CSV…")
        self._load_cfd_btn.setToolTip("Load CFD profile CSV (two columns: coordinate, value)")
        self._load_cfd_btn.clicked.connect(self._on_load_cfd)

        self._compare_btn = QPushButton("Compare")
        self._compare_btn.setEnabled(False)
        self._compare_btn.clicked.connect(self._on_compare)

        self._exp_file_label = QLabel("No experiment file")
        self._exp_file_label.setStyleSheet(f"color: {COLOR_MUTED}; font-size: 10pt;")

        self._cfd_file_label = QLabel("No CFD file")
        self._cfd_file_label.setStyleSheet(f"color: {COLOR_MUTED}; font-size: 10pt;")

        btn_layout.addWidget(self._load_exp_btn)
        btn_layout.addWidget(self._exp_file_label)
        btn_layout.addWidget(self._load_cfd_btn)
        btn_layout.addWidget(self._cfd_file_label)
        btn_layout.addStretch()
        btn_layout.addWidget(self._compare_btn)
        layout.addWidget(btn_box)

        # Chart
        self._chart = ChartWidget()
        self._chart.setMinimumHeight(250)
        layout.addWidget(self._chart)

        # Validation metrics
        self._validation_box = QGroupBox("Validation Metrics")
        val_layout = QVBoxLayout(self._validation_box)

        self._metrics_table = QTableWidget(0, 2)
        self._metrics_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self._metrics_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._metrics_table.setMinimumHeight(120)
        val_layout.addWidget(self._metrics_table)
        self._validation_box.setVisible(False)
        layout.addWidget(self._validation_box)

        # Status label
        self._status_label = QLabel("")
        self._status_label.setStyleSheet(f"color: {COLOR_MUTED}; font-size: 10pt;")
        layout.addWidget(self._status_label)

        layout.addStretch()

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_load_experiment(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Experiment Profile CSV", "", "CSV Files (*.csv);;All Files (*)"
        )
        if path:
            self._experiment_path = Path(path)
            self._exp_file_label.setText(Path(path).name)
            self._exp_file_label.setStyleSheet(f"color: {COLOR_GOOD}; font-size: 10pt;")
            self._update_compare_btn()

    def _on_load_cfd(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Load CFD Profile CSV", "", "CSV Files (*.csv);;All Files (*)"
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
            self._set_status("Comparison complete.", ok=True)
        except Exception as exc:  # noqa: BLE001
            self._set_status(f"Comparison failed: {exc}", ok=False)
            self._validation_box.setVisible(False)

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
            ("Pearson r", f"{val.pearson_r:.6f}"),
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
            return

        val = result.validation
        self._show_metrics(val)
        self._chart.plot_profiles(
            val.coordinate_array,
            val.experiment_array,
            val.cfd_array,
        )

    def clear(self) -> None:
        """Reset the page."""
        self._metrics_table.setRowCount(0)
        self._validation_box.setVisible(False)
        self._chart.clear()
        self._status_label.setText("")
        self._experiment_path = None
        self._cfd_path = None
        self._exp_file_label.setText("No experiment file")
        self._exp_file_label.setStyleSheet(f"color: {COLOR_MUTED}; font-size: 10pt;")
        self._cfd_file_label.setText("No CFD file")
        self._cfd_file_label.setStyleSheet(f"color: {COLOR_MUTED}; font-size: 10pt;")
        self._compare_btn.setEnabled(False)
