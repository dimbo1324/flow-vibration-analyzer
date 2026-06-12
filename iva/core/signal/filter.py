"""Цифровые фильтры Баттерворта с нулевым фазовым сдвигом, алгоритм 4.

``filtfilt`` выполняет прямой и обратный проход и устраняет фазовое искажение.
Замена на ``lfilter`` сдвинула бы события по времени, что недопустимо для
интерпретации вибрационного сигнала.
"""

from __future__ import annotations

import logging

import numpy as np
from scipy.signal import butter, filtfilt

from iva.core.models.exceptions import FilterConfigurationError

logger = logging.getLogger(__name__)


def _nyquist(sampling_rate_hz: float) -> float:
    return sampling_rate_hz / 2.0


def apply_bandpass_filter(
    signal: np.ndarray,
    sampling_rate_hz: float,
    low_hz: float,
    high_hz: float,
    order: int = 4,
) -> np.ndarray:
    """Применить полосовой фильтр Баттерворта без фазового сдвига.

    Args:
        signal: 1-D signal array.
        sampling_rate_hz: Sampling frequency in Hz.
        low_hz: Lower cutoff frequency in Hz.
        high_hz: Upper cutoff frequency in Hz.
        order: Filter order (default 4).

    Returns:
        Filtered signal array of the same shape.

    Raises:
        FilterConfigurationError: If ``low_hz`` or ``high_hz`` are outside
            the valid range ``0 < low_hz < high_hz < Nyquist``.
    """
    nyq = _nyquist(sampling_rate_hz)
    if not (0.0 < low_hz < high_hz < nyq):
        raise FilterConfigurationError(
            user_message=(
                f"Некорректные границы полосового фильтра [{low_hz}, {high_hz}] Hz: "
                f"требуется 0 < нижняя < верхняя < Найквист={nyq:.1f} Hz."
            ),
            technical_details=(
                f"low_hz={low_hz}, high_hz={high_hz}, "
                f"sampling_rate_hz={sampling_rate_hz}, nyquist={nyq}"
            ),
            recovery_hint="Исправьте filter_low_hz и filter_high_hz в настройках предобработки.",
        )

    logger.debug(
        "apply_bandpass_filter: order=%d, low=%.2f Hz, high=%.2f Hz, fs=%.2f Hz",
        order,
        low_hz,
        high_hz,
        sampling_rate_hz,
    )
    b, a = butter(order, [low_hz / nyq, high_hz / nyq], btype="bandpass")
    return filtfilt(b, a, signal).astype(np.float64)


def apply_lowpass_filter(
    signal: np.ndarray,
    sampling_rate_hz: float,
    cutoff_hz: float,
    order: int = 4,
) -> np.ndarray:
    """Применить ФНЧ Баттерворта без фазового сдвига.

    Args:
        signal: 1-D signal array.
        sampling_rate_hz: Sampling frequency in Hz.
        cutoff_hz: Cutoff frequency in Hz.
        order: Filter order (default 4).

    Returns:
        Filtered signal array.

    Raises:
        FilterConfigurationError: If cutoff is outside ``(0, Nyquist)``.
    """
    nyq = _nyquist(sampling_rate_hz)
    if not (0.0 < cutoff_hz < nyq):
        raise FilterConfigurationError(
            user_message=(
                f"Некорректная граница ФНЧ {cutoff_hz} Hz: "
                f"значение должно находиться в интервале (0, {nyq:.1f}) Hz."
            ),
            technical_details=f"cutoff_hz={cutoff_hz}, nyquist={nyq}",
        )

    logger.debug(
        "apply_lowpass_filter: order=%d, cutoff=%.2f Hz, fs=%.2f Hz",
        order,
        cutoff_hz,
        sampling_rate_hz,
    )
    b, a = butter(order, cutoff_hz / nyq, btype="low")
    return filtfilt(b, a, signal).astype(np.float64)


def apply_highpass_filter(
    signal: np.ndarray,
    sampling_rate_hz: float,
    cutoff_hz: float,
    order: int = 4,
) -> np.ndarray:
    """Применить ФВЧ Баттерворта без фазового сдвига.

    Args:
        signal: 1-D signal array.
        sampling_rate_hz: Sampling frequency in Hz.
        cutoff_hz: Cutoff frequency in Hz.
        order: Filter order (default 4).

    Returns:
        Filtered signal array.

    Raises:
        FilterConfigurationError: If cutoff is outside ``(0, Nyquist)``.
    """
    nyq = _nyquist(sampling_rate_hz)
    if not (0.0 < cutoff_hz < nyq):
        raise FilterConfigurationError(
            user_message=(
                f"Некорректная граница ФВЧ {cutoff_hz} Hz: "
                f"значение должно находиться в интервале (0, {nyq:.1f}) Hz."
            ),
            technical_details=f"cutoff_hz={cutoff_hz}, nyquist={nyq}",
        )

    logger.debug(
        "apply_highpass_filter: order=%d, cutoff=%.2f Hz, fs=%.2f Hz",
        order,
        cutoff_hz,
        sampling_rate_hz,
    )
    b, a = butter(order, cutoff_hz / nyq, btype="high")
    return filtfilt(b, a, signal).astype(np.float64)
