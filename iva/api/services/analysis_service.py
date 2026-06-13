"""Web analysis service — runs the pipeline from an uploaded file.

Thin orchestration layer between the API routes and the existing
iva.app.analysis_runner.  All calculations remain in iva.core.

Architecture rules:
- No PySide6 imports.
- No scientific calculations.
- Results stored under out/web/results/{analysis_id}/.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Any

from iva.api.serializers.analysis_serializer import serialize_analysis_result
from iva.api.services.upload_store import upload_store
from iva.app.analysis_runner import AnalysisRunner
from iva.app.analysis_session import AnalysisSession
from iva.core.models.analysis_result import AnalysisResult
from iva.core.models.enums import GeometryType, SignalRole
from iva.core.models.flow_parameters import FlowParameters
from iva.core.models.settings import AnalysisSettings, PreprocessingSettings, SpectralSettings
from iva.core.models.signal_data import ColumnRoleAssignment
from iva.infrastructure.logging.app_logger import get_logger

logger = get_logger(__name__)

__all__ = ["analysis_service", "StoredAnalysis"]

_RESULTS_DIR = Path("out") / "web" / "results"


@dataclass
class StoredAnalysis:
    """Holds a completed analysis result and associated metadata."""

    analysis_id: str
    file_id: str | None
    result: AnalysisResult
    payload: dict  # type: ignore[type-arg]  # pre-serialised JSON-safe dict
    output_dir: Path
    session: AnalysisSession


class _AnalysisService:
    """Thread-safe store for completed web analyses."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._store: dict[str, StoredAnalysis] = {}

    def run_from_upload(
        self,
        file_id: str,
        role_assignment_dict: dict[str, Any],
        settings_dict: dict[str, Any],
    ) -> StoredAnalysis:
        """Build a session from *file_id* and run the pipeline.

        Args:
            file_id: ID from upload_store.
            role_assignment_dict: JSON-parsed role assignment fields.
            settings_dict: JSON-parsed settings fields.

        Returns:
            A :class:`StoredAnalysis` with the serialised result payload.

        Raises:
            ValueError: Unknown file_id.
            IVAError: Pipeline error (propagated to route layer).
        """
        meta = upload_store.get(file_id)
        if meta is None:
            raise ValueError(f"Неизвестный идентификатор файла: {file_id!r}")

        role = _build_role_assignment(role_assignment_dict)
        settings = _build_settings(settings_dict)

        analysis_id = str(uuid.uuid4())
        output_dir = (_RESULTS_DIR / analysis_id).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        session = AnalysisSession(
            source_file_path=meta.saved_path,
            role_assignment=role,
            settings=settings,
            output_dir=output_dir,
            is_demo=False,
        )

        logger.info("analysis_service: running pipeline for file_id=%s", file_id)
        result = AnalysisRunner().run(session)
        session.result = result

        payload = serialize_analysis_result(result)
        # Override analysis_id with the web-assigned UUID
        payload["analysis_id"] = analysis_id
        payload["file_id"] = file_id
        payload["original_name"] = meta.original_name

        stored = StoredAnalysis(
            analysis_id=analysis_id,
            file_id=file_id,
            result=result,
            payload=payload,
            output_dir=output_dir,
            session=session,
        )
        with self._lock:
            self._store[analysis_id] = stored

        logger.info("analysis_service: stored analysis_id=%s", analysis_id)
        return stored

    def get(self, analysis_id: str) -> StoredAnalysis | None:
        with self._lock:
            return self._store.get(analysis_id)


# Module-level singleton
analysis_service = _AnalysisService()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_role_assignment(d: dict[str, Any]) -> ColumnRoleAssignment:
    """Construct ColumnRoleAssignment from a request dict."""
    role_str = d.get("signal_role", "acceleration_y")
    try:
        role = SignalRole(role_str)
    except ValueError:
        role = SignalRole.ACCELERATION_Y

    return ColumnRoleAssignment(
        time_column=str(d.get("time_column", "time_s")),
        primary_signal_column=str(d.get("primary_signal_column", "signal")),
        signal_role=role,
        additional_columns={},
        sampling_rate_hz=float(d.get("sampling_rate_hz", 1000.0)),
        sensor_conversion_factor=_opt_float(d.get("sensor_conversion_factor")),
    )


def _build_settings(d: dict[str, Any]) -> AnalysisSettings:
    """Construct AnalysisSettings from a request dict."""
    pre_d = d.get("preprocessing", {}) or {}
    spec_d = d.get("spectral", {}) or {}
    flow_d = d.get("flow_parameters") or {}

    preprocessing = PreprocessingSettings(
        remove_mean=bool(pre_d.get("remove_mean", True)),
        remove_outliers=bool(pre_d.get("remove_outliers", True)),
        apply_bandpass_filter=bool(pre_d.get("apply_bandpass_filter", True)),
        filter_low_hz=float(pre_d.get("filter_low_hz", 5.0)),
        filter_high_hz=float(pre_d.get("filter_high_hz", 250.0)),
    )

    spectral = SpectralSettings(
        peak_detection_threshold_db=float(spec_d.get("peak_detection_threshold_db", 10.0)),
    )

    flow_parameters: FlowParameters | None = None
    if flow_d:
        geom_str = flow_d.get("geometry_type")
        geom: GeometryType | None = None
        if geom_str:
            try:
                geom = GeometryType(geom_str)
            except ValueError:
                geom = None

        flow_parameters = FlowParameters(
            cylinder_diameter_m=_opt_float(flow_d.get("cylinder_diameter_m")),
            mean_flow_velocity_ms=_opt_float(flow_d.get("mean_flow_velocity_ms")),
            fluid_density_kgm3=_opt_float(flow_d.get("fluid_density_kgm3")),
            dynamic_viscosity_pas=_opt_float(flow_d.get("dynamic_viscosity_pas")),
            natural_frequency_hz=_opt_float(flow_d.get("natural_frequency_hz")),
            damping_ratio=_opt_float(flow_d.get("damping_ratio")),
            cylinder_spacing_m=_opt_float(flow_d.get("cylinder_spacing_m")),
            geometry_type=geom,
        )

    return AnalysisSettings(
        preprocessing=preprocessing,
        spectral=spectral,
        flow_parameters=flow_parameters,
    )


def _opt_float(v: Any) -> float | None:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None
