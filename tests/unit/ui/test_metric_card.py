"""Unit tests for MetricCard widget."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _qapp():  # type: ignore[no-untyped-def]
    from PySide6.QtWidgets import QApplication  # type: ignore[import-untyped]

    return QApplication.instance() or QApplication([])


def test_metric_card_instantiates() -> None:
    _qapp()
    from iva.ui.widgets.metric_card import MetricCard

    card = MetricCard("Test Label")
    assert card is not None


def test_metric_card_set_value() -> None:
    _qapp()
    from iva.ui.widgets.metric_card import MetricCard

    card = MetricCard("Frequency")
    card.set_value("40.04", "Hz", "good")
    assert card._value_label.text() == "40.04"
    assert card._unit_label.text() == "Hz"


def test_metric_card_clear() -> None:
    _qapp()
    from iva.ui.widgets.metric_card import MetricCard

    card = MetricCard("RMS")
    card.set_value("1.234", "", "bad")
    card.clear()
    assert card._value_label.text() == "—"
    assert card._unit_label.text() == ""


def test_metric_card_status_none() -> None:
    _qapp()
    from iva.ui.widgets.metric_card import MetricCard

    card = MetricCard("X")
    card.set_value("99", "", None)  # should not raise
    assert card._value_label.text() == "99"


def test_metric_card_all_statuses() -> None:
    _qapp()
    from iva.ui.widgets.metric_card import MetricCard

    card = MetricCard("Risk")
    for status in ("good", "warn", "bad", None):
        card.set_value("test", "", status)  # should not raise
