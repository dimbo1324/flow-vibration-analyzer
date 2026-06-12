"""Оценка PSD методом Уэлча по алгоритму 5.

``scipy.signal.welch`` вызывается с ``scaling='density'``, поэтому результат
имеет размерность [физическая величина]²/Hz. Длина сегмента и перекрытие берутся
из настроек анализа и являются частью воспроизводимого расчёта.
"""

from __future__ import annotations

import logging

import numpy as np
from scipy.signal import welch

from iva.core.models.exceptions import InsufficientDataError
from iva.core.models.settings import SpectralSettings

logger = logging.getLogger(__name__)

# Отдельное отображение сохраняет стабильные enum-значения проекта, даже если
# SciPy использует другое имя окна во внешнем API.
_WINDOW_MAP: dict[str, str] = {
    "hann": "hann",
    "hamming": "hamming",
    "rectangular": "boxcar",
}


def calculate_psd(
    signal: np.ndarray,
    sampling_rate_hz: float,
    settings: SpectralSettings,
) -> tuple[np.ndarray, np.ndarray]:
    """Рассчитать спектральную плотность мощности методом Уэлча.

    Args:
        signal: 1-D float signal array (should be preprocessed / filtered).
        sampling_rate_hz: Sampling frequency in Hz.
        settings: Spectral analysis configuration.

    Returns:
        ``(frequencies, psd_values)`` where *frequencies* is a 1-D array of
        frequency bins in Hz and *psd_values* is the corresponding PSD in
        [signal_unit]²/Hz.

    Raises:
        InsufficientDataError: If the signal is shorter than
            ``settings.segment_length_samples``.
    """
    nperseg = settings.segment_length_samples
    if len(signal) < nperseg:
        raise InsufficientDataError(
            user_message=(
                f"Длина сигнала ({len(signal)} отсчетов) меньше длины сегмента "
                f"Уэлча ({nperseg} отсчетов)."
            ),
            technical_details=f"len(signal)={len(signal)}, nperseg={nperseg}",
            recovery_hint="Используйте более длинную запись или уменьшите segment_length_samples.",
        )

    noverlap = int(nperseg * settings.overlap_fraction)
    window = _WINDOW_MAP.get(str(settings.window_type), "hann")

    frequencies, psd_values = welch(
        signal,
        fs=sampling_rate_hz,
        window=window,
        nperseg=nperseg,
        noverlap=noverlap,
        scaling="density",
    )

    df = sampling_rate_hz / nperseg
    logger.debug(
        "calculate_psd: nperseg=%d, noverlap=%d, window=%s, df=%.4f Hz, %d freq points",
        nperseg,
        noverlap,
        window,
        df,
        len(frequencies),
    )
    logger.info(
        "PSD calculated: %d frequency points, df=%.2f Hz",
        len(frequencies),
        df,
    )

    return frequencies.astype(np.float64), psd_values.astype(np.float64)
