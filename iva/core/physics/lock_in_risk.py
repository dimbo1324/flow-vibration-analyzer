"""Lock-in resonance risk assessment (Algorithm 10).

Classifies the current flow regime into one of three risk levels based on
the proximity of the vortex shedding frequency to the structural natural
frequency, with an optional amplitude downgrade step.
"""

from __future__ import annotations

import logging

from iva.core.models.analysis_result import PhysicsResult, RiskAssessment, SpectrumResult
from iva.core.models.enums import RiskLevel

logger = logging.getLogger(__name__)

__all__ = ["assess_risk"]

# Amplitude threshold: if the dominant spectral peak PSD is below this fraction
# of the median PSD, the peak is considered "small" and the risk level is
# downgraded by one step.  Value is dimensionless (ratio, not dB).
_AMPLITUDE_DOWNGRADE_RATIO: float = 2.0

# Deviation thresholds (dimensionless)
_THRESHOLD_CRITICAL: float = 0.10
_THRESHOLD_WATCH: float = 0.30

# ---------------------------------------------------------------------------
# Russian recommendation texts
# ---------------------------------------------------------------------------
_TEXT_SAFE = (
    "Риск резонанса низкий. Частота срыва вихрей достаточно удалена от "
    "собственной частоты конструкции. Рекомендуется продолжить штатный мониторинг."
)
_TEXT_WATCH = (
    "Обнаружена зона наблюдения. Частота срыва вихрей приближается к "
    "собственной частоте конструкции. Рекомендуется уточнить параметры модели, "
    "проверить амплитуды вибрации и усилить мониторинг."
)
_TEXT_CRITICAL = (
    "Высокий риск резонанса. Частота срыва вихрей близка к собственной частоте "
    "конструкции. Рекомендуется проверить режим течения, изменить скорость потока "
    "или геометрию, а также выполнить дополнительную инженерную проверку."
)
_TEXT_NO_FN = (
    "Собственная частота конструкции не задана. Полная оценка риска резонанса "
    "невозможна; выполнена только базовая проверка параметров течения."
)

_RISK_TEXTS = {
    RiskLevel.SAFE: _TEXT_SAFE,
    RiskLevel.WATCH: _TEXT_WATCH,
    RiskLevel.CRITICAL: _TEXT_CRITICAL,
}

_DOWNGRADE = {
    RiskLevel.CRITICAL: RiskLevel.WATCH,
    RiskLevel.WATCH: RiskLevel.SAFE,
    RiskLevel.SAFE: RiskLevel.SAFE,
}


def assess_risk(
    physics_result: PhysicsResult,
    spectrum_result: SpectrumResult,
) -> RiskAssessment:
    """Classify the resonance risk and generate a Russian engineering recommendation.

    Algorithm 10 from ``docs/11_algorithms.md``.

    Steps
    -----
    1. If no natural frequency is available (``frequency_ratio`` is ``None``
       or ``velocity_ratio`` is ``None``), return SAFE with a note that fn
       was not specified.
    2. Compute ``deviation = |frequency_ratio - 1.0|``.
    3. Classify:

       - deviation > 0.30  → SAFE
       - 0.10 < deviation ≤ 0.30 → WATCH
       - deviation ≤ 0.10  → CRITICAL

    4. Amplitude downgrade: if the dominant spectral peak amplitude is below
       ``_AMPLITUDE_DOWNGRADE_RATIO × median(psd_values)``, downgrade one
       level (CRITICAL→WATCH, WATCH→SAFE, SAFE stays SAFE).

    Parameters
    ----------
    physics_result:
        Result from ``build_physics_result``.
    spectrum_result:
        Result from the spectral analysis step.

    Returns
    -------
    RiskAssessment
        Frozen dataclass with risk level, deviation, recommendation text,
        and contributing factors.
    """
    import numpy as np

    # --- Step 1: check if fn is available --------------------------------
    fr = physics_result.frequency_ratio
    vr = physics_result.velocity_ratio

    if fr is None or vr is None:
        logger.info("Natural frequency not set — returning SAFE with informational note.")
        return RiskAssessment(
            risk_level=RiskLevel.SAFE,
            dominant_frequency_deviation=0.0,
            recommendation_text=_TEXT_NO_FN,
            contributing_factors=(
                "Собственная частота конструкции не задана; полная оценка риска недоступна.",
            ),
        )

    # --- Step 2: deviation -----------------------------------------------
    deviation: float = abs(fr - 1.0)

    # --- Step 3: classify ------------------------------------------------
    factors: list[str] = [
        f"Отношение частот fs/fn = {fr:.4f}",
        f"Отклонение от единицы |fs/fn − 1| = {deviation:.4f}",
        f"Приведённая скорость Vr = {vr:.4f}",
    ]

    if deviation > _THRESHOLD_WATCH:
        base_risk = RiskLevel.SAFE
        factors.append(f"Отклонение {deviation:.4f} > {_THRESHOLD_WATCH} → уровень SAFE")
    elif deviation > _THRESHOLD_CRITICAL:
        base_risk = RiskLevel.WATCH
        factors.append(
            f"Отклонение {deviation:.4f} ∈ ({_THRESHOLD_CRITICAL},"
            f" {_THRESHOLD_WATCH}] → уровень WATCH"
        )
    else:
        base_risk = RiskLevel.CRITICAL
        factors.append(f"Отклонение {deviation:.4f} ≤ {_THRESHOLD_CRITICAL} → уровень CRITICAL")

    # --- Step 4: amplitude downgrade -------------------------------------
    risk = base_risk
    if base_risk in (RiskLevel.WATCH, RiskLevel.CRITICAL):
        dominant = spectrum_result.dominant_peak
        psd = spectrum_result.psd_values
        if dominant is not None and len(psd) > 0:
            median_psd = float(np.median(psd))
            threshold_amplitude = _AMPLITUDE_DOWNGRADE_RATIO * median_psd
            if dominant.amplitude < threshold_amplitude:
                risk = _DOWNGRADE[base_risk]
                factors.append(
                    f"Амплитуда доминирующего пика ({dominant.amplitude:.4g}) "
                    f"ниже порога ({threshold_amplitude:.4g}); "
                    f"уровень понижен {base_risk.upper()} → {risk.upper()}"
                )

    recommendation = _RISK_TEXTS[risk]
    logger.info(
        "Risk assessment: deviation=%.4f, base=%s, final=%s",
        deviation,
        base_risk,
        risk,
    )

    return RiskAssessment(
        risk_level=risk,
        dominant_frequency_deviation=deviation,
        recommendation_text=recommendation,
        contributing_factors=tuple(factors),
    )
