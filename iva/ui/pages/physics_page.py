"""Page 05 — Physics: flow parameters form and physics result metrics."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt  # type: ignore[import-untyped]
from PySide6.QtWidgets import (  # type: ignore[import-untyped]
    QGridLayout,
    QGroupBox,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from iva.core.models.enums import GeometryType
from iva.ui.strings_ru import (
    GEOMETRY_LABELS,
    source_value,
    tr,
)
from iva.ui.styles.theme import (
    SPACING_MD,
    SPACING_SM,
)
from iva.ui.widgets.metric_card import MetricCard
from iva.ui.widgets.page_header import PageHeader
from iva.ui.widgets.page_state import PageStateBanner
from iva.ui.widgets.parameter_form import ParameterForm
from iva.ui.widgets.risk_card import RiskCard

if TYPE_CHECKING:
    from iva.core.models.analysis_result import AnalysisResult
    from iva.core.models.flow_parameters import FlowParameters

__all__ = ["PhysicsPage"]


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

        self._header = PageHeader("Физика", "Параметры потока и геометрии — безразмерные критерии")
        layout.addWidget(self._header)

        self._state_banner = PageStateBanner()
        layout.addWidget(self._state_banner)

        # Main row: form left, results right
        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setObjectName("physicsPageSplitter")
        self._splitter.setChildrenCollapsible(False)

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
        self._splitter.addWidget(form_box)

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

        metrics_layout.addWidget(self._card_re, 0, 0)
        metrics_layout.addWidget(self._card_st, 0, 1)
        metrics_layout.addWidget(self._card_fs, 1, 0)
        metrics_layout.addWidget(self._card_vr, 1, 1)
        metrics_layout.addWidget(self._card_fr, 2, 0, 1, 2)
        results_layout.addWidget(metrics_widget)

        self._risk_card = RiskCard()
        results_layout.addWidget(self._risk_card)
        results_layout.addStretch()
        self._splitter.addWidget(results_box)
        self._splitter.setStretchFactor(0, 2)
        self._splitter.setStretchFactor(1, 3)
        self._splitter.setSizes([440, 680])

        layout.addWidget(self._splitter, stretch=1)
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
            self._state_banner.show_empty(
                "Параметры течения не заданы. Заполните форму для физических расчётов."
            )
            return

        self.set_result_state()
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
            self._risk_card.set_risk(
                result.risk.risk_level,
                result.risk.recommendation_text,
            )

    def set_empty_state(self) -> None:
        """Show the initial physics-page state."""
        self._state_banner.show_empty(
            "Введите параметры потока и запустите анализ для расчёта физических показателей."
        )

    def set_running_state(self, message: str = "") -> None:
        """Show that physical result calculation is in progress."""
        self._state_banner.show_running(message)

    def set_error_state(self, message: str) -> None:
        """Show a physics-page error."""
        self._state_banner.show_error(message)

    def set_result_state(self) -> None:
        """Hide the state banner when physics data is ready."""
        self._state_banner.show_result()

    def clear(self) -> None:
        """Reset all metric cards."""
        for card in (
            self._card_re,
            self._card_st,
            self._card_fs,
            self._card_vr,
            self._card_fr,
        ):
            card.clear()
        self._risk_card.clear()
        self.set_empty_state()
