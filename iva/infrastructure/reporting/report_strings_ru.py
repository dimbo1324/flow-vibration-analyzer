"""Russian strings used by report builders and renderers."""

from __future__ import annotations

from collections.abc import Mapping

__all__ = [
    "PEAK_INTERPRETATION_LABELS",
    "RISK_LABELS",
    "SIGNAL_ROLE_LABELS",
    "display_label",
]

RISK_LABELS: dict[str, str] = {
    "safe": "БЕЗОПАСНО",
    "watch": "НАБЛЮДЕНИЕ",
    "critical": "КРИТИЧЕСКИЙ",
}

PEAK_INTERPRETATION_LABELS: dict[str, str] = {
    "vortex_shedding": "Срыв вихрей",
    "harmonic": "Гармоника",
    "structural": "Конструкционная частота",
    "unknown": "Не определено",
}

SIGNAL_ROLE_LABELS: dict[str, str] = {
    "acceleration_x": "Ускорение X",
    "acceleration_y": "Ускорение Y",
    "acceleration_z": "Ускорение Z",
    "pressure": "Давление",
    "velocity": "Скорость",
}


def display_label(labels: Mapping[str, str], value: object) -> str:
    """Return a localized report label for a stable enum/string value."""
    key = str(value).lower()
    return labels.get(key, str(value))
