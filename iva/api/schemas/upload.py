"""Pydantic schemas for file upload and upload-based analysis."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

__all__ = [
    "UploadedFileResponse",
    "UploadAnalysisRequest",
    "FilePreviewResponse",
]


class UploadedFileResponse(BaseModel):
    """Response for a successful file upload."""

    file_id: str
    original_name: str
    size_bytes: int
    extension: str
    uploaded_at: str


class RoleAssignmentRequest(BaseModel):
    """Column role and sampling configuration."""

    time_column: str = "time_s"
    primary_signal_column: str = "signal"
    signal_role: str = "acceleration_y"
    sampling_rate_hz: float = Field(default=1000.0, gt=0)
    sensor_conversion_factor: float | None = None


class FlowParametersRequest(BaseModel):
    """Physical flow parameters (all optional)."""

    cylinder_diameter_m: float | None = None
    mean_flow_velocity_ms: float | None = None
    fluid_density_kgm3: float | None = None
    dynamic_viscosity_pas: float | None = None
    natural_frequency_hz: float | None = None
    damping_ratio: float | None = None
    cylinder_spacing_m: float | None = None
    geometry_type: str | None = None


class SettingsRequest(BaseModel):
    """Analysis settings (all optional, defaults applied server-side)."""

    preprocessing: dict[str, Any] = Field(default_factory=dict)
    spectral: dict[str, Any] = Field(default_factory=dict)
    flow_parameters: FlowParametersRequest | None = None


class UploadAnalysisRequest(BaseModel):
    """Request body for POST /api/analysis/upload."""

    file_id: str
    role_assignment: RoleAssignmentRequest = Field(default_factory=lambda: RoleAssignmentRequest())
    settings: SettingsRequest = Field(default_factory=lambda: SettingsRequest())


class FilePreviewResponse(BaseModel):
    """Response for GET /api/files/{file_id}/preview."""

    columns: list[str]
    rows: list[dict[str, Any]]
    total_preview_rows: int
