"""Schemas for analysis response."""

from __future__ import annotations

from pydantic import BaseModel

__all__ = [
    "PeakData",
    "SignalData",
    "SpectrumData",
    "SummaryData",
    "AnalysisResponse",
]


class PeakData(BaseModel):
    frequency_hz: float
    amplitude_db: float
    type: str


class SignalData(BaseModel):
    time_s: list[float]
    raw: list[float]
    filtered: list[float]
    rms_trend: list[float]


class SpectrumData(BaseModel):
    frequencies_hz: list[float]
    psd: list[float]
    peaks: list[PeakData]


class SummaryData(BaseModel):
    risk_level: str | None
    risk_label_ru: str | None
    dominant_peak_hz: float | None
    rms_total: float | None
    reynolds_number: float | None
    strouhal_number: float | None


class AnalysisResponse(BaseModel):
    analysis_id: str
    is_demo: bool
    demo_title: str | None
    summary: SummaryData
    signal: SignalData
    spectrum: SpectrumData
    warnings: list[str]
