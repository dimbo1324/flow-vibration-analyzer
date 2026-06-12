"""Pure deterministic generators for synthetic vibration signals."""

from __future__ import annotations

import math

import numpy as np
from numpy.typing import NDArray

from iva.core.models.exceptions import ValidationError

__all__ = [
    "generate_clean_sine",
    "generate_noisy_sine",
    "generate_with_harmonics",
    "generate_with_outliers",
    "generate_with_gaps",
    "generate_risk_scenario",
]


def _invalid(message: str, details: str) -> ValidationError:
    return ValidationError(
        user_message=message,
        technical_details=details,
        recovery_hint="Проверьте параметры генерации синтетического сигнала.",
    )


def _validate_signal_parameters(
    frequency_hz: float,
    duration_s: float,
    sampling_rate_hz: float,
    amplitude: float,
) -> int:
    values = (frequency_hz, duration_s, sampling_rate_hz, amplitude)
    if not all(math.isfinite(value) for value in values):
        raise _invalid("Параметры сигнала должны быть конечными числами.", repr(values))
    if frequency_hz <= 0.0:
        raise _invalid("Частота сигнала должна быть больше нуля.", f"frequency_hz={frequency_hz}")
    if duration_s <= 0.0:
        raise _invalid("Длительность сигнала должна быть больше нуля.", f"duration_s={duration_s}")
    if sampling_rate_hz <= 0.0:
        raise _invalid(
            "Частота дискретизации должна быть больше нуля.",
            f"sampling_rate_hz={sampling_rate_hz}",
        )
    if frequency_hz >= sampling_rate_hz / 2.0:
        raise _invalid(
            "Частота сигнала должна быть ниже частоты Найквиста.",
            f"frequency_hz={frequency_hz}, sampling_rate_hz={sampling_rate_hz}",
        )
    if amplitude <= 0.0:
        raise _invalid("Амплитуда сигнала должна быть больше нуля.", f"amplitude={amplitude}")
    sample_count = int(duration_s * sampling_rate_hz)
    if sample_count < 2:
        raise _invalid(
            "Для генерации требуется не менее двух отсчетов.",
            f"sample_count={sample_count}",
        )
    return sample_count


def _time_axis(sample_count: int, sampling_rate_hz: float) -> NDArray[np.float64]:
    return np.arange(sample_count, dtype=np.float64) / sampling_rate_hz


def _rng(seed: int | None) -> np.random.Generator:
    return np.random.default_rng(0 if seed is None else seed)


def generate_clean_sine(
    frequency_hz: float,
    duration_s: float,
    sampling_rate_hz: float,
    amplitude: float,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Generate a pure sine wave and its time axis without file I/O."""
    sample_count = _validate_signal_parameters(
        frequency_hz, duration_s, sampling_rate_hz, amplitude
    )
    time_s = _time_axis(sample_count, sampling_rate_hz)
    signal = amplitude * np.sin(2.0 * np.pi * frequency_hz * time_s)
    return time_s, signal.astype(np.float64, copy=False)


def generate_noisy_sine(
    frequency_hz: float,
    duration_s: float,
    sampling_rate_hz: float,
    amplitude: float,
    snr_db: float,
    seed: int | None = None,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Generate a sine wave with deterministic additive Gaussian noise."""
    if not math.isfinite(snr_db):
        raise _invalid("Отношение сигнал/шум должно быть конечным числом.", f"snr_db={snr_db}")
    time_s, clean_signal = generate_clean_sine(
        frequency_hz, duration_s, sampling_rate_hz, amplitude
    )
    signal_power = amplitude**2 / 2.0
    noise_power = signal_power / (10.0 ** (snr_db / 10.0))
    noise = _rng(seed).normal(0.0, np.sqrt(noise_power), len(clean_signal))
    return time_s, (clean_signal + noise).astype(np.float64, copy=False)


def generate_with_harmonics(
    fundamental_hz: float,
    duration_s: float,
    sampling_rate_hz: float,
    amplitude: float,
    n_harmonics: int,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Generate a fundamental tone and harmonics with a ``1 / k`` roll-off."""
    if n_harmonics < 1:
        raise _invalid(
            "Количество гармоник должно быть не меньше одной.",
            f"n_harmonics={n_harmonics}",
        )
    highest_frequency = fundamental_hz * n_harmonics
    sample_count = _validate_signal_parameters(
        highest_frequency, duration_s, sampling_rate_hz, amplitude
    )
    time_s = _time_axis(sample_count, sampling_rate_hz)
    harmonic_numbers = np.arange(1, n_harmonics + 1, dtype=np.float64)[:, np.newaxis]
    components = (amplitude / harmonic_numbers) * np.sin(
        2.0 * np.pi * harmonic_numbers * fundamental_hz * time_s[np.newaxis, :]
    )
    signal = np.asarray(np.sum(components, axis=0, dtype=np.float64), dtype=np.float64)
    return time_s, signal


def generate_with_outliers(
    base_signal: NDArray[np.float64],
    n_outliers: int,
    magnitude: float,
    seed: int | None = None,
) -> NDArray[np.float64]:
    """Return a copy of a signal with isolated signed spikes inserted."""
    signal = np.asarray(base_signal, dtype=np.float64)
    if signal.ndim != 1 or signal.size == 0:
        raise _invalid(
            "Базовый сигнал должен быть непустым одномерным массивом.", str(signal.shape)
        )
    if n_outliers < 0 or n_outliers > signal.size:
        raise _invalid(
            "Количество выбросов должно находиться в пределах длины сигнала.",
            f"n_outliers={n_outliers}, signal_size={signal.size}",
        )
    if not math.isfinite(magnitude) or magnitude <= 0.0:
        raise _invalid("Амплитуда выбросов должна быть больше нуля.", f"magnitude={magnitude}")
    result = signal.copy()
    if n_outliers:
        rng = _rng(seed)
        indices = rng.choice(signal.size, size=n_outliers, replace=False)
        signs = rng.choice(np.array([-1.0, 1.0]), size=n_outliers)
        result[indices] += magnitude * signs
    return result


def generate_with_gaps(
    base_signal: NDArray[np.float64],
    gap_fraction: float,
    seed: int | None = None,
) -> NDArray[np.float64]:
    """Return a copy of a signal with a deterministic fraction replaced by NaN."""
    signal = np.asarray(base_signal, dtype=np.float64)
    if signal.ndim != 1 or signal.size == 0:
        raise _invalid(
            "Базовый сигнал должен быть непустым одномерным массивом.", str(signal.shape)
        )
    if not math.isfinite(gap_fraction) or not 0.0 <= gap_fraction <= 1.0:
        raise _invalid(
            "Доля пропусков должна находиться в диапазоне от 0 до 1.",
            f"gap_fraction={gap_fraction}",
        )
    result = signal.copy()
    gap_count = int(signal.size * gap_fraction)
    if gap_count:
        indices = _rng(seed).choice(signal.size, size=gap_count, replace=False)
        result[indices] = np.nan
    return result


def generate_risk_scenario(
    shedding_hz: float,
    natural_hz: float,
    duration_s: float,
    sampling_rate_hz: float,
    amplitude: float,
    seed: int | None = None,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Generate close shedding and structural components for a risk demonstration."""
    sample_count = _validate_signal_parameters(
        max(shedding_hz, natural_hz), duration_s, sampling_rate_hz, amplitude
    )
    if shedding_hz <= 0.0 or natural_hz <= 0.0:
        raise _invalid(
            "Частоты срыва и конструкции должны быть больше нуля.",
            f"shedding_hz={shedding_hz}, natural_hz={natural_hz}",
        )
    time_s = _time_axis(sample_count, sampling_rate_hz)
    shedding = amplitude * np.sin(2.0 * np.pi * shedding_hz * time_s)
    structural = amplitude * 0.5 * np.sin(2.0 * np.pi * natural_hz * time_s)
    noise = _rng(seed).normal(0.0, amplitude * 0.05, sample_count)
    return time_s, (shedding + structural + noise).astype(np.float64, copy=False)
