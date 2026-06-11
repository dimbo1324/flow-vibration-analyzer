"""ParameterForm — a dynamic form widget for numeric and enum fields."""

from __future__ import annotations

from PySide6.QtWidgets import (  # type: ignore[import-untyped]
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QWidget,
)

__all__ = ["ParameterForm"]


class ParameterForm(QWidget):
    """A form that holds numeric (float) and combo-box (enum) input fields.

    Fields are registered by key.  :meth:`get_values` returns the current
    snapshot as a plain ``dict``.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._layout = QFormLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(6)
        self._fields: dict[str, QWidget] = {}

    # ------------------------------------------------------------------
    # Field registration
    # ------------------------------------------------------------------

    def add_float_field(
        self,
        key: str,
        label: str,
        value: float = 0.0,
        min_val: float = 0.0,
        max_val: float = 1e9,
        decimals: int = 6,
    ) -> None:
        """Add a floating-point spinbox field."""
        spin = QDoubleSpinBox()
        spin.setRange(min_val, max_val)
        spin.setDecimals(decimals)
        spin.setValue(value)
        spin.setSingleStep(10 ** (-decimals))
        self._layout.addRow(label, spin)
        self._fields[key] = spin

    def add_combo_field(
        self,
        key: str,
        label: str,
        options: list[str],
        current: str = "",
    ) -> None:
        """Add a combo-box (drop-down) field."""
        combo = QComboBox()
        combo.addItems(options)
        if current and current in options:
            combo.setCurrentText(current)
        self._layout.addRow(label, combo)
        self._fields[key] = combo

    # ------------------------------------------------------------------
    # Value access
    # ------------------------------------------------------------------

    def get_values(self) -> dict[str, float | str | None]:
        """Return a snapshot of all field values keyed by registration key."""
        result: dict[str, float | str | None] = {}
        for key, widget in self._fields.items():
            if isinstance(widget, QDoubleSpinBox):
                result[key] = widget.value()
            elif isinstance(widget, QComboBox):
                result[key] = widget.currentText()
        return result

    def set_value(self, key: str, value: float | str) -> None:
        """Set a field value by key.

        Silently ignored if the key does not exist or the type is incompatible.
        """
        widget = self._fields.get(key)
        if isinstance(widget, QDoubleSpinBox) and isinstance(value, (int, float)):
            widget.setValue(float(value))
        elif isinstance(widget, QComboBox) and isinstance(value, str):
            widget.setCurrentText(value)

    def clear_values(self) -> None:
        """Reset all fields to their minimum (or first) value."""
        for widget in self._fields.values():
            if isinstance(widget, QDoubleSpinBox):
                widget.setValue(widget.minimum())
            elif isinstance(widget, QComboBox):
                widget.setCurrentIndex(0)
