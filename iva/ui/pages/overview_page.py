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
from iva.ui.strings_ru import RISK_LABELS, display_label, tr
from iva.ui.styles.theme import (
    COLOR_BAD,
    COLOR_GOOD,
    COLOR_MUTED,
    COLOR_TEXT,
    COLOR_WARN,
    FONT_SIZE_TITLE,
    SPACING_MD,
    SPACING_SM,
)
from iva.ui.widgets.chart_widget import ChartWidget
from iva.ui.widgets.metric_card import MetricCard

if TYPE_CHECKING:
    from iva.core.models.analysis_result import AnalysisResult

__all__ = ["OverviewPage"]

_RISK_STATUS: dict[str, str] = {
    RiskLevel.SAFE: "good",
    RiskLevel.WATCH: "warn",
    RiskLevel.CRITICAL: "bad",
}

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
        layout.setContentsMargins(SPACING_MD, SPACING_MD, SPACING_MD, SPACING_MD)
        layout.setSpacing(SPACING_MD)

        # Title
        title = QLabel(tr("01 — Overview"))
        title.setStyleSheet(
            f"font-size: {FONT_SIZE_TITLE}pt; font-weight: bold; color: {COLOR_TEXT};"
        )
        layout.addWidget(title)

        subtitle = QLabel(tr("Analysis summary — dominant metrics at a glance"))
        subtitle.setStyleSheet(f"color: {COLOR_MUTED}; font-size: 11pt;")
        layout.addWidget(subtitle)

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

        self._demo_marker = QLabel("Демонстрационные синтетические данные")
        self._demo_marker.setObjectName("overviewDemoMarker")
        self._demo_marker.setWordWrap(True)
        self._demo_marker.setStyleSheet(f"color: {COLOR_WARN}; font-weight: bold;")
        self._demo_marker.setVisible(False)
        layout.addWidget(self._demo_marker)

        # Metric cards row
        cards_widget = QWidget()
        cards_layout = QGridLayout(cards_widget)
        cards_layout.setSpacing(SPACING_SM)
        cards_layout.setContentsMargins(0, 0, 0, 0)

        self._card_peak_freq = MetricCard(tr("Dominant Peak"))
        self._card_rms = MetricCard(tr("Total RMS"))
        self._card_shedding = MetricCard(tr("Shedding Freq"))
        self._card_risk = MetricCard(tr("Risk Level"))

        cards_layout.addWidget(self._card_peak_freq, 0, 0)
        cards_layout.addWidget(self._card_rms, 0, 1)
        cards_layout.addWidget(self._card_shedding, 0, 2)
        cards_layout.addWidget(self._card_risk, 0, 3)

        layout.addWidget(cards_widget)

        # Charts row
        charts_box = QGroupBox(tr("Signal / Spectrum"))
        charts_layout = QHBoxLayout(charts_box)
        charts_layout.setSpacing(SPACING_SM)

        self._signal_chart = ChartWidget()
        self._signal_chart.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._signal_chart.setMinimumHeight(220)

        self._spectrum_chart = ChartWidget()
        self._spectrum_chart.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self._spectrum_chart.setMinimumHeight(220)

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
            level = str(result.risk.risk_level)
            status = _RISK_STATUS.get(level, None)
            self._card_risk.set_value(display_label(RISK_LABELS, level), "", status)
        else:
            self._card_risk.set_value("N/A", "")

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

    def clear(self) -> None:
        """Reset all widgets to placeholder state."""
        for card in (
            self._card_peak_freq,
            self._card_rms,
            self._card_shedding,
            self._card_risk,
        ):
            card.clear()
        self._signal_chart.clear()
        self._spectrum_chart.clear()
        self._recommendation_label.setText("Результат анализа пока отсутствует.")
        self._demo_marker.setVisible(False)
