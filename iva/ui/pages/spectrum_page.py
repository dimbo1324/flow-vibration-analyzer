"""Page 04 — Spectrum: PSD chart and peaks table."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import (  # type: ignore[import-untyped]
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from iva.ui.styles.theme import COLOR_MUTED, COLOR_TEXT, FONT_SIZE_TITLE, SPACING_MD, SPACING_SM
from iva.ui.widgets.chart_widget import ChartWidget

if TYPE_CHECKING:
    from iva.core.models.analysis_result import AnalysisResult

__all__ = ["SpectrumPage"]


class SpectrumPage(QWidget):
    """Spectral analysis page: PSD plot and detected peaks table."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_MD, SPACING_MD, SPACING_MD, SPACING_MD)
        layout.setSpacing(SPACING_MD)

        title = QLabel("04 — Spectrum")
        title.setStyleSheet(
            f"font-size: {FONT_SIZE_TITLE}pt; font-weight: bold; color: {COLOR_TEXT};"
        )
        layout.addWidget(title)

        subtitle = QLabel("Power spectral density — Welch method")
        subtitle.setStyleSheet(f"color: {COLOR_MUTED}; font-size: 11pt;")
        layout.addWidget(subtitle)

        # Main content area
        content_layout = QHBoxLayout()
        content_layout.setSpacing(SPACING_SM)

        # PSD chart
        chart_box = QGroupBox("PSD")
        chart_layout = QVBoxLayout(chart_box)
        self._psd_chart = ChartWidget()
        self._psd_chart.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._psd_chart.setMinimumHeight(300)
        chart_layout.addWidget(self._psd_chart)
        content_layout.addWidget(chart_box, stretch=3)

        # Peaks table
        peaks_box = QGroupBox("Detected Peaks")
        peaks_layout = QVBoxLayout(peaks_box)
        self._peaks_table = QTableWidget(0, 4)
        self._peaks_table.setHorizontalHeaderLabels(
            ["Freq (Hz)", "Amplitude", "Width (Hz)", "Interpretation"]
        )
        header = self._peaks_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._peaks_table.setMinimumWidth(280)
        self._peaks_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        peaks_layout.addWidget(self._peaks_table)
        content_layout.addWidget(peaks_box, stretch=2)

        layout.addLayout(content_layout)

    def on_analysis_completed(self, result: AnalysisResult) -> None:
        """Update PSD chart and peaks table from analysis result."""
        if result.spectrum is None:
            return

        sp = result.spectrum
        peaks = list(sp.all_peaks) if sp.all_peaks else None
        self._psd_chart.plot_psd(sp.frequencies, sp.psd_values, peaks)

        # Populate peaks table
        self._peaks_table.setRowCount(0)
        if peaks:
            self._peaks_table.setRowCount(len(peaks))
            for row, pk in enumerate(peaks):
                self._peaks_table.setItem(row, 0, QTableWidgetItem(f"{pk.frequency_hz:.3f}"))
                self._peaks_table.setItem(row, 1, QTableWidgetItem(f"{pk.amplitude:.4g}"))
                self._peaks_table.setItem(row, 2, QTableWidgetItem(f"{pk.width_hz_3db:.3f}"))
                self._peaks_table.setItem(row, 3, QTableWidgetItem(str(pk.interpretation)))

    def clear(self) -> None:
        """Reset the page."""
        self._psd_chart.clear()
        self._peaks_table.setRowCount(0)
