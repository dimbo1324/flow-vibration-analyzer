"""Оценка риска резонансного lock-in по алгоритму 10.

Режим относится к одному из трёх уровней по близости частоты срыва вихрей к
собственной частоте конструкции. Слабая амплитуда может понизить уровень на
одну ступень, чтобы одно частотное совпадение не создавало ложную тревогу.
"""

from __future__ import annotations

import logging

from iva.core.models.analysis_result import PhysicsResult, RiskAssessment, SpectrumResult
from iva.core.models.enums import RiskLevel

logger = logging.getLogger(__name__)

__all__ = ["assess_risk"]

# Порог амплитуды безразмерный: сравнивается отношение PSD, а не значение dB.
_AMPLITUDE_DOWNGRADE_RATIO: float = 2.0

# Безразмерные границы отклонения закреплены инженерной методикой.
_THRESHOLD_CRITICAL: float = 0.10
_THRESHOLD_WATCH: float = 0.30

# ---------------------------------------------------------------------------
# Русские тексты инженерных рекомендаций
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

_RISK_LABELS = {
    RiskLevel.SAFE: "БЕЗОПАСНО",
    RiskLevel.WATCH: "НАБЛЮДЕНИЕ",
    RiskLevel.CRITICAL: "КРИТИЧЕСКИЙ",
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
    """Классифицировать риск и сформировать русскую инженерную рекомендацию.

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

    # Без fn полная оценка lock-in невозможна; возвращаем безопасный уровень с
    # явным предупреждением, а не придумываем отсутствующий параметр.
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

    # Отклонение отношения частот от единицы является основной метрикой риска.
    deviation: float = abs(fr - 1.0)

    # Базовая классификация не учитывает амплитуду и следует алгоритму 10.
    factors: list[str] = [
        f"Отношение частот fs/fn = {fr:.4f}",
        f"Отклонение от единицы |fs/fn − 1| = {deviation:.4f}",
        f"Приведённая скорость Vr = {vr:.4f}",
    ]

    if deviation > _THRESHOLD_WATCH:
        base_risk = RiskLevel.SAFE
        factors.append(
            f"Отклонение {deviation:.4f} > {_THRESHOLD_WATCH} → "
            f"уровень {_RISK_LABELS[RiskLevel.SAFE]}"
        )
    elif deviation > _THRESHOLD_CRITICAL:
        base_risk = RiskLevel.WATCH
        factors.append(
            f"Отклонение {deviation:.4f} ∈ ({_THRESHOLD_CRITICAL},"
            f" {_THRESHOLD_WATCH}] → уровень {_RISK_LABELS[RiskLevel.WATCH]}"
        )
    else:
        base_risk = RiskLevel.CRITICAL
        factors.append(
            f"Отклонение {deviation:.4f} ≤ {_THRESHOLD_CRITICAL} → "
            f"уровень {_RISK_LABELS[RiskLevel.CRITICAL]}"
        )

    # Слабый доминирующий пик понижает риск только на одну ступень: амплитуда
    # уточняет, но не отменяет физическое совпадение частот.
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
                    f"уровень понижен {_RISK_LABELS[base_risk]} → {_RISK_LABELS[risk]}"
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
