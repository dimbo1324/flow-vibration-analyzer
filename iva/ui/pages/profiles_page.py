"""Page 06 — Profiles: experiment vs CFD comparison (placeholder for Stage 9)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import (  # type: ignore[import-untyped]
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
    COLOR_MUTED,
    COLOR_TEXT,
    FONT_SIZE_TITLE,
    SPACING_MD,
)

if TYPE_CHECKING:
    from iva.core.models.analysis_result import AnalysisResult

__all__ = ["ProfilesPage"]


class ProfilesPage(QWidget):
    """Experiment vs CFD profiles comparison page."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
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

        # Info banner
        info_box = QGroupBox("CFD Profile Comparison")
        info_layout = QVBoxLayout(info_box)

        info_label = QLabel(
            "CFD profile comparison will be available in Stage 9.\n\n"
            "This page will show:\n"
            "  • Velocity profile: experiment vs CFD\n"
            "  • Validation metrics: RMSE, MAE, MAPE, Pearson r\n"
            "  • Vector field preview\n\n"
            "Use the button below to load a CFD results file."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet(f"color: {COLOR_MUTED}; font-size: 12pt;")
        info_layout.addWidget(info_label)

        btn_row = QHBoxLayout()
        self._load_cfd_btn = QPushButton("Load CFD Profile…")
        self._load_cfd_btn.setEnabled(False)
        self._load_cfd_btn.setToolTip("CFD profile loading is available in Stage 9")
        btn_row.addWidget(self._load_cfd_btn)
        btn_row.addStretch()
        info_layout.addLayout(btn_row)
        layout.addWidget(info_box)

        # Validation metrics (shown if validation result exists)
        self._validation_box = QGroupBox("Validation Metrics")
        val_layout = QVBoxLayout(self._validation_box)

        self._metrics_table = QTableWidget(0, 2)
        self._metrics_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self._metrics_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._metrics_table.setMinimumHeight(120)
        val_layout.addWidget(self._metrics_table)
        self._validation_box.setVisible(False)
        layout.addWidget(self._validation_box)

        layout.addStretch()

    def on_analysis_completed(self, result: AnalysisResult) -> None:
        """Show validation metrics if available."""
        if result.validation is None:
            self._validation_box.setVisible(False)
            return

        val = result.validation
        rows = [
            ("RMSE", f"{val.rmse:.6f}"),
            ("MAE", f"{val.mae:.6f}"),
            ("MAPE", f"{val.mape:.4f} %" if val.is_mape_valid and val.mape is not None else "N/A"),
            ("Pearson r", f"{val.pearson_r:.6f}"),
        ]
        self._metrics_table.setRowCount(len(rows))
        for i, (metric, value) in enumerate(rows):
            self._metrics_table.setItem(i, 0, QTableWidgetItem(metric))
            self._metrics_table.setItem(i, 1, QTableWidgetItem(value))
        self._validation_box.setVisible(True)

    def clear(self) -> None:
        """Reset the page."""
        self._metrics_table.setRowCount(0)
        self._validation_box.setVisible(False)
