"""Reusable deterministic synthetic signals and built-in demo scenarios."""

from iva.core.synthetic.demo_scenarios import (
    DemoScenario,
    generate_demo_signal,
    get_demo_scenario,
    list_demo_scenarios,
)
from iva.core.synthetic.generators import (
    generate_clean_sine,
    generate_noisy_sine,
    generate_risk_scenario,
    generate_with_gaps,
    generate_with_harmonics,
    generate_with_outliers,
)

__all__ = [
    "DemoScenario",
    "generate_clean_sine",
    "generate_noisy_sine",
    "generate_with_harmonics",
    "generate_with_outliers",
    "generate_with_gaps",
    "generate_risk_scenario",
    "list_demo_scenarios",
    "get_demo_scenario",
    "generate_demo_signal",
]
