"""Page 02 — Import: file selection and column role assignment."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt  # type: ignore[import-untyped]
from PySide6.QtWidgets import (  # type: ignore[import-untyped]
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from iva.core.models.enums import SignalRole
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
        title = QLabel("02 — Import")
        title.setStyleSheet(
            f"font-size: {FONT_SIZE_TITLE}pt; font-weight: bold; color: {COLOR_TEXT};"
        )
        layout.addWidget(title)

        subtitle = QLabel("Select a data file and assign column roles")
        subtitle.setStyleSheet(f"color: {COLOR_MUTED}; font-size: 11pt;")
        layout.addWidget(subtitle)

        # File selection group
        file_box = QGroupBox("Data File")
        file_layout = QVBoxLayout(file_box)

        # Drop zone
        self._drop_zone = QLabel("Drag and drop a file here\nor use 'Open File' (Ctrl+O)")
        self._drop_zone.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._drop_zone.setMinimumHeight(80)
        self._drop_zone.setStyleSheet(
            f"border: 2px dashed {COLOR_BORDER}; border-radius: {RADIUS_LG}px;"
            f" color: {COLOR_MUTED}; font-size: 12pt; padding: {SPACING_LG}px;"
        )
        file_layout.addWidget(self._drop_zone)

        # File path display
        path_row = QHBoxLayout()
        path_label = QLabel("File:")
        path_label.setStyleSheet(f"color: {COLOR_MUTED};")
        self._path_display = QLineEdit()
        self._path_display.setReadOnly(True)
        self._path_display.setPlaceholderText("No file selected")
        path_row.addWidget(path_label)
        path_row.addWidget(self._path_display)
        file_layout.addLayout(path_row)
        layout.addWidget(file_box)

        # Column assignment group
        assign_box = QGroupBox("Column Assignment")
        assign_layout = QFormLayout(assign_box)
        assign_layout.setSpacing(8)

        self._time_column = QLineEdit("time")
        self._time_column.setPlaceholderText("e.g. time or t")
        assign_layout.addRow("Time column:", self._time_column)

        self._signal_column = QLineEdit("signal")
        self._signal_column.setPlaceholderText("e.g. signal or acceleration")
        assign_layout.addRow("Signal column:", self._signal_column)

        # Signal role drop-down
        self._role_form = ParameterForm()
        role_options = [r.value for r in SignalRole]
        self._role_form.add_combo_field(
            "signal_role",
            "Signal role:",
            role_options,
            current=SignalRole.ACCELERATION_X.value,
        )
        assign_layout.addRow(self._role_form)
        layout.addWidget(assign_box)

        # Physical parameters group
        phys_box = QGroupBox("Physical Parameters")
        phys_layout = QFormLayout(phys_box)
        phys_layout.setSpacing(8)

        self._sampling_rate = QDoubleSpinBox()
        self._sampling_rate.setRange(1.0, 1_000_000.0)
        self._sampling_rate.setDecimals(2)
        self._sampling_rate.setValue(1000.0)
        self._sampling_rate.setSuffix(" Hz")
        phys_layout.addRow("Sampling rate:", self._sampling_rate)

        self._conversion_factor = QDoubleSpinBox()
        self._conversion_factor.setRange(0.0, 1e12)
        self._conversion_factor.setDecimals(6)
        self._conversion_factor.setValue(1.0)
        phys_layout.addRow("Sensor conversion factor:", self._conversion_factor)
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
        self._path_display.setText(str(path))
        self._drop_zone.setText(f"Selected: {path.name}")
        self._drop_zone.setStyleSheet(
            f"border: 2px solid {COLOR_ACCENT}; border-radius: {RADIUS_LG}px;"
            f" color: {COLOR_ACCENT}; font-size: 12pt; padding: {SPACING_LG}px;"
            f" background: {COLOR_PANEL};"
        )

    def get_role_assignment(self) -> ColumnRoleAssignment | None:
        """Build and return a :class:`ColumnRoleAssignment` from form values.

        Returns ``None`` if required fields are empty or sampling rate is zero.
        """
        from iva.core.models.signal_data import ColumnRoleAssignment

        time_col = self._time_column.text().strip()
        signal_col = self._signal_column.text().strip()
        if not time_col or not signal_col:
            return None

        role_str = self._role_form.get_values().get("signal_role", "")
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
        """No-op — import page does not update on completed analysis."""

    def clear(self) -> None:
        """Reset the page to its initial state."""
        self._path_display.clear()
        self._drop_zone.setText("Drag and drop a file here\nor use 'Open File' (Ctrl+O)")
