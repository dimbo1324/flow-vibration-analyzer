"""Page 01 — Overview: key metric cards and analysis summary."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal  # type: ignore[import-untyped]
from PySide6.QtWidgets import (  # type: ignore[import-untyped]
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from iva.core.models.enums import RiskLevel
from iva.ui.strings_ru import tr
from iva.ui.styles.theme import (
    COLOR_BAD,
    COLOR_GOOD,
    COLOR_MUTED,
    COLOR_WARN,
    SPACING_LG,
    SPACING_MD,
    SPACING_SM,
)
from iva.ui.widgets.chart_widget import ChartWidget
from iva.ui.widgets.metric_card import MetricCard
from iva.ui.widgets.page_header import PageHeader
from iva.ui.widgets.page_state import PageStateBanner
from iva.ui.widgets.risk_card import RiskCard

if TYPE_CHECKING:
    from iva.core.models.analysis_result import AnalysisResult

__all__ = ["OverviewPage"]

_RISK_COLOR: dict[str, str] = {
    RiskLevel.SAFE: COLOR_GOOD,
    RiskLevel.WATCH: COLOR_WARN,
    RiskLevel.CRITICAL: COLOR_BAD,
}


class OverviewPage(QWidget):
    """Overview dashboard showing the four key metrics and summary charts."""

    open_file_requested = Signal()
    demo_requested = Signal()
    open_project_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        layout.setSpacing(SPACING_MD)

        # Единый заголовок страницы (титул + акцент + подзаголовок + чип).
        self._header = PageHeader(
            "Обзор",
            "Сводка анализа — ключевые показатели режима с первого взгляда",
        )
        layout.addWidget(self._header)

        quick_box = QGroupBox("Быстрый старт")
        quick_layout = QVBoxLayout(quick_box)
        quick_text = QLabel(
            "Начните с демонстрационных данных, чтобы увидеть полный расчетный цикл "
            "без подготовки файла."
        )
        quick_text.setWordWrap(True)
        quick_text.setStyleSheet(f"color: {COLOR_MUTED};")
        quick_layout.addWidget(quick_text)
        quick_buttons = QHBoxLayout()
        self._quick_open_button = QPushButton("Открыть файл данных")
        self._quick_open_button.setObjectName("quickOpenFileButton")
        self._quick_demo_button = QPushButton("Запустить демо-анализ")
        self._quick_demo_button.setObjectName("quickDemoButton")
        # Primary call-to-action: filled accent style from the app stylesheet.
        self._quick_demo_button.setProperty("accent", True)
        self._quick_project_button = QPushButton("Открыть проект .vibproj")
        self._quick_project_button.setObjectName("quickOpenProjectButton")
        self._quick_open_button.clicked.connect(self.open_file_requested.emit)
        self._quick_demo_button.clicked.connect(self.demo_requested.emit)
        self._quick_project_button.clicked.connect(self.open_project_requested.emit)
        quick_buttons.addWidget(self._quick_open_button)
        quick_buttons.addWidget(self._quick_demo_button)
        quick_buttons.addWidget(self._quick_project_button)
        quick_buttons.addStretch()
        quick_layout.addLayout(quick_buttons)
        layout.addWidget(quick_box)

        self._state_banner = PageStateBanner()
        layout.addWidget(self._state_banner)

        self._demo_marker = QLabel("Демонстрационные синтетические данные")
        self._demo_marker.setObjectName("overviewDemoMarker")
        self._demo_marker.setWordWrap(True)
        self._demo_marker.setStyleSheet(f"color: {COLOR_WARN}; font-weight: bold;")
        self._demo_marker.setVisible(False)
        layout.addWidget(self._demo_marker)

        # Metric cards row
        cards_widget = QWidget()
        cards_layout = QGridLayout(cards_widget)
        cards_layout.setSpacing(SPACING_MD)
        cards_layout.setContentsMargins(0, 0, 0, 0)

        self._card_peak_freq = MetricCard(tr("Dominant Peak"))
        self._card_rms = MetricCard(tr("Total RMS"))
        self._card_shedding = MetricCard(tr("Shedding Freq"))
        self._risk_card = RiskCard()

        cards_layout.addWidget(self._card_peak_freq, 0, 0)
        cards_layout.addWidget(self._card_rms, 0, 1)
        cards_layout.addWidget(self._card_shedding, 0, 2)
        cards_layout.addWidget(self._risk_card, 0, 3)

        layout.addWidget(cards_widget)

        # Charts row
        charts_box = QGroupBox(tr("Signal / Spectrum"))
        charts_layout = QHBoxLayout(charts_box)
        charts_layout.setSpacing(SPACING_SM)

        self._signal_chart = ChartWidget()
        self._signal_chart.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._signal_chart.setMinimumHeight(300)

        self._spectrum_chart = ChartWidget()
        self._spectrum_chart.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self._spectrum_chart.setMinimumHeight(300)

        charts_layout.addWidget(self._signal_chart)
        charts_layout.addWidget(self._spectrum_chart)
        layout.addWidget(charts_box)

        # Recommendation text
        rec_box = QGroupBox(tr("Assessment"))
        rec_layout = QVBoxLayout(rec_box)
        self._recommendation_label = QLabel(
            "Результат анализа пока отсутствует.\n\nОткройте файл данных и запустите анализ."
        )
        self._recommendation_label.setWordWrap(True)
        self._recommendation_label.setStyleSheet(f"color: {COLOR_MUTED}; font-size: 12pt;")
        rec_layout.addWidget(self._recommendation_label)
        layout.addWidget(rec_box)

        layout.addStretch()
        scroll.setWidget(content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def on_analysis_completed(self, result: AnalysisResult) -> None:
        """Update cards and charts from a completed analysis result."""
        self.set_result_state()
        self._demo_marker.setVisible(result.is_demo)
        if result.is_demo:
            self._demo_marker.setText(
                "Демонстрационные синтетические данные"
                + (f" — {result.demo_title}" if result.demo_title else "")
            )
        # Dominant peak
        if result.spectrum and result.spectrum.dominant_peak:
            pk = result.spectrum.dominant_peak
            self._card_peak_freq.set_value(f"{pk.frequency_hz:.2f}", "Hz")
        else:
            self._card_peak_freq.set_value("N/A", "Hz")

        # RMS
        if result.spectrum:
            self._card_rms.set_value(f"{result.spectrum.rms_total:.4g}", "")
        else:
            self._card_rms.set_value("N/A", "")

        # Shedding frequency
        if result.physics:
            self._card_shedding.set_value(
                f"{result.physics.calculated_shedding_frequency_hz:.2f}", "Hz"
            )
        else:
            self._card_shedding.set_value("N/A", "Hz")

        # Risk level
        if result.risk:
            self._risk_card.set_risk(
                result.risk.risk_level,
                result.risk.recommendation_text,
            )
        else:
            self._risk_card.clear()

        # Charts
        if result.processed_data is not None:
            pd = result.processed_data
            self._signal_chart.plot_signal(pd.time_array, pd.signal_filtered, tr("Filtered"))

        if result.spectrum is not None:
            sp = result.spectrum
            peaks = list(sp.all_peaks) if sp.all_peaks else None
            self._spectrum_chart.plot_psd(sp.frequencies, sp.psd_values, peaks)

        # Recommendation
        if result.risk:
            color = _RISK_COLOR.get(str(result.risk.risk_level), COLOR_MUTED)
            self._recommendation_label.setText(result.risk.recommendation_text)
            self._recommendation_label.setStyleSheet(f"color: {color}; font-size: 12pt;")
        elif result.warnings:
            self._recommendation_label.setText("\n".join(result.warnings))
            self._recommendation_label.setStyleSheet(f"color: {COLOR_MUTED}; font-size: 12pt;")

    def set_empty_state(self) -> None:
        """Show the initial overview state while keeping quick start available."""
        self._state_banner.show_empty()

    def set_running_state(self, message: str = "") -> None:
        """Show analysis progress on the overview page."""
        self._state_banner.show_running(message)

    def set_error_state(self, message: str) -> None:
        """Show a concise overview error state."""
        self._state_banner.show_error(message)

    def set_result_state(self) -> None:
        """Hide the state banner once a result is ready."""
        self._state_banner.show_result()

    def clear(self) -> None:
        """Reset all widgets to placeholder state."""
        for card in (
            self._card_peak_freq,
            self._card_rms,
            self._card_shedding,
        ):
            card.clear()
        self._risk_card.clear()
        self._signal_chart.clear()
        self._spectrum_chart.clear()
        self._recommendation_label.setText("Результат анализа пока отсутствует.")
        self._demo_marker.setVisible(False)
        self.set_empty_state()
