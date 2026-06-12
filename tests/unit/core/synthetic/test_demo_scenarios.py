"""Tests for typed built-in demonstration scenarios."""

from __future__ import annotations

import numpy as np
import pytest

from iva.core.models.exceptions import ValidationError
from iva.core.synthetic.demo_scenarios import (
    generate_demo_signal,
    get_demo_scenario,
    list_demo_scenarios,
)

REQUIRED_KEYS = {
    "clean_40hz",
    "noisy_40hz",
    "harmonics_40hz",
    "outliers_40hz",
    "gaps_40hz",
    "critical_risk",
}


def test_scenario_catalog_is_complete_unique_and_russian() -> None:
    scenarios = list_demo_scenarios()
    keys = [scenario.key for scenario in scenarios]
    assert len(scenarios) >= 6
    assert len(keys) == len(set(keys))
    assert REQUIRED_KEYS <= set(keys)
    for scenario in scenarios:
        assert scenario.title_ru and scenario.description_ru
        assert any("а" <= char.lower() <= "я" or char.lower() == "ё" for char in scenario.title_ru)


@pytest.mark.parametrize("key", sorted(REQUIRED_KEYS))
def test_generated_demo_has_standard_columns(key: str) -> None:
    scenario, columns = generate_demo_signal(key)
    assert scenario.key == key
    assert set(columns) == {"time_s", "signal"}
    assert len(columns["time_s"]) == len(columns["signal"])
    assert len(columns["signal"]) > 500
    if key == "gaps_40hz":
        assert np.isnan(columns["signal"]).any()


def test_unknown_scenario_is_user_facing_error() -> None:
    with pytest.raises(ValidationError, match="Неизвестный"):
        get_demo_scenario("missing")
