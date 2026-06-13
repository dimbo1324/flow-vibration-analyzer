"""Schemas for demo endpoints."""

from __future__ import annotations

from pydantic import BaseModel

__all__ = ["DemoRequest", "DemoScenarioItem", "DemoScenariosResponse"]


class DemoRequest(BaseModel):
    scenario_key: str


class DemoScenarioItem(BaseModel):
    key: str
    title_ru: str
    description_ru: str
    expected_peak_hz: float | None


class DemoScenariosResponse(BaseModel):
    items: list[DemoScenarioItem]
