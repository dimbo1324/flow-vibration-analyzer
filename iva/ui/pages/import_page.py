"""Page 02 — Import: file selection and column role assignment."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal  # type: ignore[import-untyped]
from PySide6.QtWidgets import (  # type: ignore[import-untyped]
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from iva.app.demo_service import list_available_demo_scenarios
from iva.core.models.enums import SignalRole
from iva.ui.strings_ru import SIGNAL_ROLE_LABELS, source_value, tr
from iva.ui.styles.theme import (
    COLOR_ACCENT,
    COLOR_BORDER,
    COLOR_MUTED,
    COLOR_PANEL,
    COLOR_TEXT,
    FONT_SIZE_TITLE,
    RADIUS_LG,
    SPACING_LG,
    SPACING_MD,
)
from iva.ui.widgets.parameter_form import ParameterForm

if TYPE_CHECKING:
    from iva.core.models.analysis_result import AnalysisResult
    from iva.core.models.signal_data import ColumnRoleAssignment

__all__ = ["ImportPage"]


class ImportPage(QWidget):
    """Data file import and column role assignment page."""

    demo_requested = Signal(str)

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

        # Title
        title = QLabel(tr("02 — Import"))
        title.setStyleSheet(
            f"font-size: {FONT_SIZE_TITLE}pt; font-weight: bold; color: {COLOR_TEXT};"
        )
        layout.addWidget(title)

        subtitle = QLabel(tr("Select a data file and assign column roles"))
        subtitle.setStyleSheet(f"color: {COLOR_MUTED}; font-size: 11pt;")
        layout.addWidget(subtitle)

        # File selection group
        file_box = QGroupBox(tr("Data File"))
        file_layout = QVBoxLayout(file_box)

        # Drop zone
        self._drop_zone = QLabel(tr("Drag and drop a file here\nor use 'Open File' (Ctrl+O)"))
        self._drop_zone.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._drop_zone.setMinimumHeight(80)
        self._drop_zone.setStyleSheet(
            f"border: 2px dashed {COLOR_BORDER}; border-radius: {RADIUS_LG}px;"
            f" color: {COLOR_MUTED}; font-size: 12pt; padding: {SPACING_LG}px;"
        )
        file_layout.addWidget(self._drop_zone)

        # File path display
        path_row = QHBoxLayout()
        path_label = QLabel(tr("File:"))
        path_label.setStyleSheet(f"color: {COLOR_MUTED};")
        self._path_display = QLineEdit()
        self._path_display.setReadOnly(True)
        self._path_display.setPlaceholderText(tr("No file selected"))
        path_row.addWidget(path_label)
        path_row.addWidget(self._path_display)
        file_layout.addLayout(path_row)
        layout.addWidget(file_box)

        demo_box = QGroupBox("Демонстрационные сценарии")
        demo_layout = QVBoxLayout(demo_box)
        self._demo_scenarios = {
            scenario.key: scenario for scenario in list_available_demo_scenarios()
        }
        self._demo_selector = QComboBox()
        self._demo_selector.setObjectName("demoScenarioSelector")
        for scenario in self._demo_scenarios.values():
            self._demo_selector.addItem(scenario.title_ru, scenario.key)
        self._demo_selector.currentIndexChanged.connect(self._update_demo_description)
        demo_layout.addWidget(self._demo_selector)
        self._demo_description = QLabel("")
        self._demo_description.setWordWrap(True)
        self._demo_description.setStyleSheet(f"color: {COLOR_MUTED};")
        demo_layout.addWidget(self._demo_description)
        self._demo_button = QPushButton("Загрузить демо-сценарий")
        self._demo_button.setObjectName("loadDemoScenarioButton")
        self._demo_button.clicked.connect(self._emit_demo_requested)
        demo_layout.addWidget(self._demo_button)
        self._demo_marker = QLabel("")
        self._demo_marker.setObjectName("importDemoMarker")
        self._demo_marker.setWordWrap(True)
        self._demo_marker.setStyleSheet(f"color: {COLOR_ACCENT}; font-weight: bold;")
        self._demo_marker.setVisible(False)
        demo_layout.addWidget(self._demo_marker)
        layout.addWidget(demo_box)
        self._update_demo_description()

        # Column assignment group
        assign_box = QGroupBox(tr("Column Assignment"))
        assign_layout = QFormLayout(assign_box)
        assign_layout.setSpacing(8)

        self._time_column = QLineEdit("time")
        self._time_column.setPlaceholderText("например, time или t")
        assign_layout.addRow(tr("Time column:"), self._time_column)

        self._signal_column = QLineEdit("signal")
        self._signal_column.setPlaceholderText("например, signal или acceleration")
        assign_layout.addRow(tr("Signal column:"), self._signal_column)

        # Signal role drop-down
        self._role_form = ParameterForm()
        role_options = [SIGNAL_ROLE_LABELS[r.value] for r in SignalRole]
        self._role_form.add_combo_field(
            "signal_role",
            tr("Signal role:"),
            role_options,
            current=SIGNAL_ROLE_LABELS[SignalRole.ACCELERATION_X.value],
        )
        assign_layout.addRow(self._role_form)
        layout.addWidget(assign_box)

        # Physical parameters group
        phys_box = QGroupBox(tr("Physical Parameters"))
        phys_layout = QFormLayout(phys_box)
        phys_layout.setSpacing(8)

        self._sampling_rate = QDoubleSpinBox()
        self._sampling_rate.setRange(1.0, 1_000_000.0)
        self._sampling_rate.setDecimals(2)
        self._sampling_rate.setValue(1000.0)
        self._sampling_rate.setSuffix(" Hz")
        phys_layout.addRow(tr("Sampling rate:"), self._sampling_rate)

        self._conversion_factor = QDoubleSpinBox()
        self._conversion_factor.setRange(0.0, 1e12)
        self._conversion_factor.setDecimals(6)
        self._conversion_factor.setValue(1.0)
        phys_layout.addRow(tr("Sensor conversion factor:"), self._conversion_factor)
        layout.addWidget(phys_box)

        layout.addStretch()
        scroll.setWidget(content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    # ------------------------------------------------------------------
    # Public API (called by MainWindow)
    # ------------------------------------------------------------------

    def set_file_path(self, path: Path) -> None:
        """Update the displayed file path."""
        self._demo_marker.setVisible(False)
        self._path_display.setText(str(path))
        self._drop_zone.setText(f"Выбран файл: {path.name}")
        self._drop_zone.setStyleSheet(
            f"border: 2px solid {COLOR_ACCENT}; border-radius: {RADIUS_LG}px;"
            f" color: {COLOR_ACCENT}; font-size: 12pt; padding: {SPACING_LG}px;"
            f" background: {COLOR_PANEL};"
        )

    def selected_demo_key(self) -> str:
        """Return the key selected in the demo scenario combo box."""
        return str(self._demo_selector.currentData() or "clean_40hz")

    def set_demo_session(
        self,
        title: str,
        description: str,
        source_path: Path,
        sampling_rate_hz: float,
        signal_role: SignalRole,
    ) -> None:
        """Show which synthetic scenario prepared the current session."""
        self.set_file_path(source_path)
        self._time_column.setText("time_s")
        self._signal_column.setText("signal")
        self._sampling_rate.setValue(sampling_rate_hz)
        self._conversion_factor.setValue(1.0)
        self._role_form.set_value("signal_role", SIGNAL_ROLE_LABELS[signal_role.value])
        self._demo_marker.setText(f"Демонстрационные синтетические данные — {title}")
        self._demo_marker.setToolTip(description)
        self._demo_marker.setVisible(True)

    def _update_demo_description(self, _index: int = -1) -> None:
        scenario = self._demo_scenarios.get(self.selected_demo_key())
        self._demo_description.setText(scenario.description_ru if scenario else "")

    def _emit_demo_requested(self) -> None:
        self.demo_requested.emit(self.selected_demo_key())

    def get_role_assignment(self) -> ColumnRoleAssignment | None:
        """Build and return a :class:`ColumnRoleAssignment` from form values.

        Returns ``None`` if required fields are empty or sampling rate is zero.
        """
        from iva.core.models.signal_data import ColumnRoleAssignment

        time_col = self._time_column.text().strip()
        signal_col = self._signal_column.text().strip()
        if not time_col or not signal_col:
            return None

        role_label = str(self._role_form.get_values().get("signal_role", ""))
        role_str = source_value(SIGNAL_ROLE_LABELS, role_label)
        try:
            role = SignalRole(str(role_str))
        except ValueError:
            role = SignalRole.ACCELERATION_X

        sampling_rate = self._sampling_rate.value()
        if sampling_rate <= 0:
            return None

        conversion = self._conversion_factor.value()
        sensor_factor = conversion if conversion != 1.0 else None

        return ColumnRoleAssignment(
            time_column=time_col,
            primary_signal_column=signal_col,
            signal_role=role,
            additional_columns={},
            sampling_rate_hz=sampling_rate,
            sensor_conversion_factor=sensor_factor,
        )

    def on_analysis_completed(self, result: AnalysisResult) -> None:
        """Keep the synthetic-data marker synchronized with the result."""
        self._demo_marker.setVisible(result.is_demo)
        if result.is_demo:
            self._demo_marker.setText(
                "Демонстрационные синтетические данные"
                + (f" — {result.demo_title}" if result.demo_title else "")
            )

    def clear(self) -> None:
        """Reset the page to its initial state."""
        self._path_display.clear()
        self._drop_zone.setText(tr("Drag and drop a file here\nor use 'Open File' (Ctrl+O)"))
        self._demo_marker.setVisible(False)
