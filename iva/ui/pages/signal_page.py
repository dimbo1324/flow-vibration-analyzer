"""Page 03 — Signal: time-domain signal plots and preprocessing summary."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt  # type: ignore[import-untyped]
from PySide6.QtWidgets import (  # type: ignore[import-untyped]
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from iva.ui.strings_ru import tr
from iva.ui.styles.theme import COLOR_MUTED, SPACING_MD
from iva.ui.widgets.chart_widget import ChartWidget
from iva.ui.widgets.page_header import PageHeader
from iva.ui.widgets.page_state import PageStateBanner

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

        self._header = PageHeader(
            "Сигнал", "Временная область — очищенный и отфильтрованный сигнал"
        )
        layout.addWidget(self._header)

        self._state_banner = PageStateBanner()
        layout.addWidget(self._state_banner)

        self._splitter = QSplitter(Qt.Orientation.Vertical)
        self._splitter.setObjectName("signalPageSplitter")
        self._splitter.setChildrenCollapsible(False)

        # Chart: cleaned vs filtered
        charts_box = QGroupBox(tr("Signal (cleaned vs filtered)"))
        charts_layout = QVBoxLayout(charts_box)
        self._chart = ChartWidget()
        self._chart.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._chart.setMinimumHeight(280)
        charts_layout.addWidget(self._chart)
        self._splitter.addWidget(charts_box)

        details_widget = QWidget()
        details_layout = QHBoxLayout(details_widget)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(SPACING_MD)

        # RMS trend chart
        rms_box = QGroupBox(tr("RMS Trend"))
        rms_layout = QVBoxLayout(rms_box)
        self._rms_chart = ChartWidget()
        self._rms_chart.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._rms_chart.setMinimumHeight(180)
        rms_layout.addWidget(self._rms_chart)
        details_layout.addWidget(rms_box, stretch=2)

        # Preprocessing log
        log_box = QGroupBox(tr("Preprocessing Log"))
        log_layout = QVBoxLayout(log_box)
        self._log_label = QLabel(tr("No preprocessing log available."))
        self._log_label.setWordWrap(True)
        self._log_label.setStyleSheet(
            f"color: {COLOR_MUTED}; font-family: monospace; font-size: 10pt;"
        )
        log_layout.addWidget(self._log_label)
        details_layout.addWidget(log_box, stretch=1)

        self._splitter.addWidget(details_widget)
        self._splitter.setStretchFactor(0, 3)
        self._splitter.setStretchFactor(1, 2)
        self._splitter.setSizes([480, 260])
        layout.addWidget(self._splitter, stretch=1)

    def on_analysis_completed(self, result: AnalysisResult) -> None:
        """Update charts from a completed analysis result."""
        if result.processed_data is None:
            self.set_error_state("Не удалось построить данные временного сигнала.")
            return

        self.set_result_state()

        pd = result.processed_data
        self._chart.plot_two_signals(
            pd.time_array,
            pd.signal_cleaned,
            pd.signal_filtered,
            label_a=tr("Cleaned"),
            label_b=tr("Filtered"),
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
        self._log_label.setText("\n".join(log_lines) if log_lines else tr("No operations logged."))

    def set_empty_state(self) -> None:
        """Show the initial page state."""
        self._state_banner.show_empty()

    def set_running_state(self, message: str = "") -> None:
        """Show that signal processing is in progress."""
        self._state_banner.show_running(message)

    def set_error_state(self, message: str) -> None:
        """Show a signal-page error without replacing the application banner."""
        self._state_banner.show_error(message)

    def set_result_state(self) -> None:
        """Reveal result content after successful analysis."""
        self._state_banner.show_result()

    def clear(self) -> None:
        """Reset the page."""
        self._chart.clear()
        self._rms_chart.clear()
        self._log_label.setText(tr("No preprocessing log available."))
        self.set_empty_state()
