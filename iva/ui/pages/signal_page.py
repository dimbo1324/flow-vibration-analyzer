"""Page 03 — Signal: time-domain signal plots and preprocessing summary."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import (  # type: ignore[import-untyped]
    QGroupBox,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from iva.ui.styles.theme import COLOR_MUTED, COLOR_TEXT, FONT_SIZE_TITLE, SPACING_MD
from iva.ui.widgets.chart_widget import ChartWidget

if TYPE_CHECKING:
    from iva.core.models.analysis_result import AnalysisResult

__all__ = ["SignalPage"]


class SignalPage(QWidget):
    """Time-domain signal visualisation with preprocessing log."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_MD, SPACING_MD, SPACING_MD, SPACING_MD)
        layout.setSpacing(SPACING_MD)

        title = QLabel("03 — Signal")
        title.setStyleSheet(
            f"font-size: {FONT_SIZE_TITLE}pt; font-weight: bold; color: {COLOR_TEXT};"
        )
        layout.addWidget(title)

        subtitle = QLabel("Time-domain signal — cleaned and filtered")
        subtitle.setStyleSheet(f"color: {COLOR_MUTED}; font-size: 11pt;")
        layout.addWidget(subtitle)

        # Chart: cleaned vs filtered
        charts_box = QGroupBox("Signal (cleaned vs filtered)")
        charts_layout = QVBoxLayout(charts_box)
        self._chart = ChartWidget()
        self._chart.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._chart.setMinimumHeight(280)
        charts_layout.addWidget(self._chart)
        layout.addWidget(charts_box)

        # RMS trend chart
        rms_box = QGroupBox("RMS Trend")
        rms_layout = QVBoxLayout(rms_box)
        self._rms_chart = ChartWidget()
        self._rms_chart.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._rms_chart.setMinimumHeight(180)
        rms_layout.addWidget(self._rms_chart)
        layout.addWidget(rms_box)

        # Preprocessing log
        log_box = QGroupBox("Preprocessing Log")
        log_layout = QVBoxLayout(log_box)
        self._log_label = QLabel("No preprocessing log available.")
        self._log_label.setWordWrap(True)
        self._log_label.setStyleSheet(
            f"color: {COLOR_MUTED}; font-family: monospace; font-size: 10pt;"
        )
        log_layout.addWidget(self._log_label)
        layout.addWidget(log_box)

    def on_analysis_completed(self, result: AnalysisResult) -> None:
        """Update charts from a completed analysis result."""
        if result.processed_data is None:
            return

        pd = result.processed_data
        self._chart.plot_two_signals(
            pd.time_array,
            pd.signal_cleaned,
            pd.signal_filtered,
            label_a="Cleaned",
            label_b="Filtered",
        )

        if result.spectrum is not None:
            sp = result.spectrum
            if sp.rms_trend is not None and len(sp.rms_trend) > 0:
                # rms_trend length may differ from time_array; build a matching axis
                import numpy as np

                rms_time = np.linspace(
                    float(pd.time_array[0]),
                    float(pd.time_array[-1]),
                    len(sp.rms_trend),
                )
                self._rms_chart.plot_rms_trend(rms_time, sp.rms_trend)

        log_lines = list(pd.preprocessing_log)
        self._log_label.setText("\n".join(log_lines) if log_lines else "No operations logged.")

    def clear(self) -> None:
        """Reset the page."""
        self._chart.clear()
        self._rms_chart.clear()
        self._log_label.setText("No preprocessing log available.")
