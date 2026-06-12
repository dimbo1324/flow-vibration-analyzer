"""Page 05 — Physics: flow parameters form and physics result metrics."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import (  # type: ignore[import-untyped]
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from iva.core.models.enums import GeometryType, RiskLevel
from iva.ui.strings_ru import (
    GEOMETRY_LABELS,
    RISK_LABELS,
    display_label,
    source_value,
    tr,
)
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
from iva.ui.widgets.metric_card import MetricCard
from iva.ui.widgets.parameter_form import ParameterForm

if TYPE_CHECKING:
    from iva.core.models.analysis_result import AnalysisResult
    from iva.core.models.flow_parameters import FlowParameters

__all__ = ["PhysicsPage"]

_RISK_COLOR: dict[str, str] = {
    RiskLevel.SAFE: COLOR_GOOD,
    RiskLevel.WATCH: COLOR_WARN,
    RiskLevel.CRITICAL: COLOR_BAD,
}

_RISK_STATUS: dict[str, str] = {
    RiskLevel.SAFE: "good",
    RiskLevel.WATCH: "warn",
    RiskLevel.CRITICAL: "bad",
}


class PhysicsPage(QWidget):
    """Physics parameters input and computed results display."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(SPACING_MD, SPACING_MD, SPACING_MD, SPACING_MD)
        layout.setSpacing(SPACING_MD)

        title = QLabel(tr("05 — Physics"))
        title.setStyleSheet(
            f"font-size: {FONT_SIZE_TITLE}pt; font-weight: bold; color: {COLOR_TEXT};"
        )
        layout.addWidget(title)

        subtitle = QLabel(tr("Flow and geometry parameters — dimensionless criteria"))
        subtitle.setStyleSheet(f"color: {COLOR_MUTED}; font-size: 11pt;")
        layout.addWidget(subtitle)

        # Main row: form left, results right
        main_row = QHBoxLayout()
        main_row.setSpacing(SPACING_MD)

        # Parameter form
        form_box = QGroupBox(tr("Flow Parameters (SI units)"))
        form_layout = QVBoxLayout(form_box)
        self._form = ParameterForm()
        self._form.add_float_field(
            "cylinder_diameter_m",
            tr("Cylinder diameter (m):"),
            value=0.012,
            min_val=1e-5,
            max_val=10.0,
            decimals=4,
        )
        self._form.add_float_field(
            "mean_flow_velocity_ms",
            tr("Mean flow velocity (m/s):"),
            value=2.0,
            min_val=0.0,
            max_val=1000.0,
            decimals=4,
        )
        self._form.add_float_field(
            "fluid_density_kgm3",
            tr("Fluid density (kg/m³):"),
            value=998.0,
            min_val=0.1,
            max_val=20000.0,
            decimals=2,
        )
        self._form.add_float_field(
            "dynamic_viscosity_pas",
            tr("Dynamic viscosity (Pa·s):"),
            value=1.002e-3,
            min_val=1e-10,
            max_val=1000.0,
            decimals=8,
        )
        self._form.add_float_field(
            "natural_frequency_hz",
            tr("Natural frequency fn (Hz):"),
            value=0.0,
            min_val=0.0,
            max_val=100000.0,
            decimals=3,
        )
        self._form.add_float_field(
            "damping_ratio",
            tr("Damping ratio ζ:"),
            value=0.0,
            min_val=0.0,
            max_val=1.0,
            decimals=4,
        )
        self._form.add_float_field(
            "cylinder_spacing_m",
            tr("Cylinder spacing (m):"),
            value=0.0,
            min_val=0.0,
            max_val=100.0,
            decimals=4,
        )
        geom_options = [GEOMETRY_LABELS[g.value] for g in GeometryType]
        self._form.add_combo_field(
            "geometry_type",
            tr("Geometry type:"),
            geom_options,
            current=GEOMETRY_LABELS[GeometryType.SINGLE_CYLINDER.value],
        )
        form_layout.addWidget(self._form)
        main_row.addWidget(form_box, stretch=1)

        # Results panel
        results_box = QGroupBox(tr("Computed Results"))
        results_layout = QVBoxLayout(results_box)

        metrics_widget = QWidget()
        metrics_layout = QGridLayout(metrics_widget)
        metrics_layout.setSpacing(SPACING_SM)

        self._card_re = MetricCard(tr("Reynolds Number"))
        self._card_st = MetricCard(tr("Strouhal Number"))
        self._card_fs = MetricCard(tr("Shedding Freq"))
        self._card_vr = MetricCard(tr("Velocity Ratio"))
        self._card_fr = MetricCard(tr("Frequency Ratio"))
        self._card_risk = MetricCard(tr("Risk Level"))

        metrics_layout.addWidget(self._card_re, 0, 0)
        metrics_layout.addWidget(self._card_st, 0, 1)
        metrics_layout.addWidget(self._card_fs, 1, 0)
        metrics_layout.addWidget(self._card_vr, 1, 1)
        metrics_layout.addWidget(self._card_fr, 2, 0)
        metrics_layout.addWidget(self._card_risk, 2, 1)
        results_layout.addWidget(metrics_widget)

        self._recommendation_label = QLabel(
            "Введите параметры потока и запустите анализ для расчета результатов."
        )
        self._recommendation_label.setWordWrap(True)
        self._recommendation_label.setStyleSheet(f"color: {COLOR_MUTED}; font-size: 11pt;")
        results_layout.addWidget(self._recommendation_label)
        main_row.addWidget(results_box, stretch=1)

        layout.addLayout(main_row)
        layout.addStretch()
        scroll.setWidget(content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def get_flow_parameters(self) -> FlowParameters | None:
        """Build a :class:`FlowParameters` from the form values.

        Returns ``None`` if required fields are zero/invalid.
        """
        from iva.core.models.flow_parameters import FlowParameters

        vals = self._form.get_values()

        def _opt(key: str) -> float | None:
            v = vals.get(key)
            if isinstance(v, float) and v > 0:
                return v
            return None

        geom_label = str(vals.get("geometry_type", ""))
        geom_str = source_value(GEOMETRY_LABELS, geom_label)
        geometry = None
        if isinstance(geom_str, str):
            try:
                geometry = GeometryType(geom_str)
            except ValueError:
                geometry = None

        return FlowParameters(
            cylinder_diameter_m=_opt("cylinder_diameter_m"),
            mean_flow_velocity_ms=_opt("mean_flow_velocity_ms"),
            fluid_density_kgm3=_opt("fluid_density_kgm3"),
            dynamic_viscosity_pas=_opt("dynamic_viscosity_pas"),
            natural_frequency_hz=_opt("natural_frequency_hz"),
            damping_ratio=_opt("damping_ratio"),
            cylinder_spacing_m=_opt("cylinder_spacing_m"),
            geometry_type=geometry,
        )

    def set_flow_parameters(self, parameters: FlowParameters) -> None:
        """Populate the form from a prepared analysis scenario."""
        for key in (
            "cylinder_diameter_m",
            "mean_flow_velocity_ms",
            "fluid_density_kgm3",
            "dynamic_viscosity_pas",
            "natural_frequency_hz",
            "damping_ratio",
            "cylinder_spacing_m",
        ):
            value = getattr(parameters, key)
            if value is not None:
                self._form.set_value(key, value)
        if parameters.geometry_type is not None:
            self._form.set_value("geometry_type", GEOMETRY_LABELS[parameters.geometry_type.value])

    def on_analysis_completed(self, result: AnalysisResult) -> None:
        """Update metric cards from a completed analysis result."""
        if result.physics is None:
            return

        ph = result.physics
        self._card_re.set_value(f"{ph.reynolds_number:.3e}", "")
        self._card_st.set_value(f"{ph.strouhal_number:.4f}", "")
        self._card_fs.set_value(f"{ph.calculated_shedding_frequency_hz:.3f}", "Hz")

        if ph.velocity_ratio is not None:
            self._card_vr.set_value(f"{ph.velocity_ratio:.3f}", "")
        else:
            self._card_vr.set_value("N/A", "")

        if ph.frequency_ratio is not None:
            self._card_fr.set_value(f"{ph.frequency_ratio:.3f}", "")
        else:
            self._card_fr.set_value("N/A", "")

        if result.risk is not None:
            level = str(result.risk.risk_level)
            self._card_risk.set_value(
                display_label(RISK_LABELS, level), "", _RISK_STATUS.get(level)
            )
            color = _RISK_COLOR.get(level, COLOR_MUTED)
            self._recommendation_label.setText(result.risk.recommendation_text)
            self._recommendation_label.setStyleSheet(f"color: {color}; font-size: 11pt;")

    def clear(self) -> None:
        """Reset all metric cards."""
        for card in (
            self._card_re,
            self._card_st,
            self._card_fs,
            self._card_vr,
            self._card_fr,
            self._card_risk,
        ):
            card.clear()
        self._recommendation_label.setText(
            "Введите параметры потока и запустите анализ для расчета результатов."
        )
