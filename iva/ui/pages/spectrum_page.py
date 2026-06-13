"""Page 04 — Spectrum: PSD chart and peaks table."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt  # type: ignore[import-untyped]
from PySide6.QtWidgets import (  # type: ignore[import-untyped]
    QGroupBox,
    QHeaderView,
    QSizePolicy,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from iva.ui.strings_ru import PEAK_INTERPRETATION_LABELS, display_label, tr
from iva.ui.styles.theme import SPACING_MD
from iva.ui.widgets.chart_widget import ChartWidget
from iva.ui.widgets.page_header import PageHeader
from iva.ui.widgets.page_state import PageStateBanner

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

        self._header = PageHeader("Спектр", "Спектральная плотность мощности — метод Уэлча")
        layout.addWidget(self._header)

        self._state_banner = PageStateBanner()
        layout.addWidget(self._state_banner)

        # Main content area
        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setObjectName("spectrumPageSplitter")
        self._splitter.setChildrenCollapsible(False)

        # PSD chart
        chart_box = QGroupBox("PSD")
        chart_layout = QVBoxLayout(chart_box)
        self._psd_chart = ChartWidget()
        self._psd_chart.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._psd_chart.setMinimumHeight(300)
        chart_layout.addWidget(self._psd_chart)
        self._splitter.addWidget(chart_box)

        # Peaks table
        peaks_box = QGroupBox(tr("Detected Peaks"))
        peaks_layout = QVBoxLayout(peaks_box)
        self._peaks_table = QTableWidget(0, 4)
        self._peaks_table.setHorizontalHeaderLabels(
            [tr("Freq (Hz)"), tr("Amplitude"), tr("Width (Hz)"), tr("Interpretation")]
        )
        header = self._peaks_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._peaks_table.setMinimumWidth(280)
        self._peaks_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        peaks_layout.addWidget(self._peaks_table)
        self._splitter.addWidget(peaks_box)
        self._splitter.setStretchFactor(0, 3)
        self._splitter.setStretchFactor(1, 2)
        self._splitter.setSizes([760, 360])

        layout.addWidget(self._splitter, stretch=1)

    def on_analysis_completed(self, result: AnalysisResult) -> None:
        """Update PSD chart and peaks table from analysis result."""
        if result.spectrum is None:
            self.set_error_state("Не удалось построить спектральные данные.")
            return

        self.set_result_state()

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
                self._peaks_table.setItem(
                    row,
                    3,
                    QTableWidgetItem(display_label(PEAK_INTERPRETATION_LABELS, pk.interpretation)),
                )

    def set_empty_state(self) -> None:
        """Show the initial page state."""
        self._state_banner.show_empty()

    def set_running_state(self, message: str = "") -> None:
        """Show that spectral analysis is in progress."""
        self._state_banner.show_running(message)

    def set_error_state(self, message: str) -> None:
        """Show a spectral-page error."""
        self._state_banner.show_error(message)

    def set_result_state(self) -> None:
        """Hide the state banner when PSD data is ready."""
        self._state_banner.show_result()

    def clear(self) -> None:
        """Reset the page."""
        self._psd_chart.clear()
        self._peaks_table.setRowCount(0)
        self.set_empty_state()
