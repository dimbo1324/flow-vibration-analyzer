"""Safe JSON storage for versioned ``.vibproj`` analysis sessions."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from iva.app.analysis_session import AnalysisSession
from iva.core.models.enums import GeometryType, SignalRole, WindowType
from iva.core.models.exceptions import ExportError, ValidationError
from iva.core.models.flow_parameters import FlowParameters
from iva.core.models.settings import AnalysisSettings, PreprocessingSettings, SpectralSettings
from iva.core.models.signal_data import ColumnRoleAssignment
from iva.infrastructure.session.session_serializer import (
    VIBPROJ_SCHEMA_VERSION,
    analysis_result_from_dict,
    analysis_result_to_dict,
)

logger = logging.getLogger(__name__)

__all__ = ["save_project", "load_project"]

_VIBPROJ_SUFFIX = ".vibproj"


def save_project(session: AnalysisSession, file_path: str | Path) -> Path:
    """Save a completed session as UTF-8 JSON, adding the extension if needed."""
    destination = Path(file_path)
    if destination.suffix.lower() != _VIBPROJ_SUFFIX:
        destination = destination.with_suffix(_VIBPROJ_SUFFIX)
    if session.result is None:
        raise ExportError(
            user_message="Cannot save project: the session has no analysis result.",
            technical_details="session.result is None",
            recovery_hint="Run an analysis before saving the project.",
        )

    payload: dict[str, Any] = {
        "_vibproj_version": VIBPROJ_SCHEMA_VERSION,
        "_saved_at": datetime.now(tz=UTC).isoformat(),
        "output_dir": str(session.output_dir) if session.output_dir is not None else None,
        "settings": _settings_to_dict(session.settings),
        "role_assignment": _role_assignment_to_dict(session.role_assignment),
        "result": analysis_result_to_dict(session.result),
    }
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    except (OSError, TypeError, ValueError) as exc:
        raise ExportError(
            user_message=f"Cannot write project file to '{destination.name}'.",
            technical_details=str(exc),
        ) from exc
    logger.info("save_project: written to '%s'", destination)
    return destination


def load_project(file_path: str | Path) -> AnalysisSession:
    """Load and validate a ``.vibproj`` file without executing its contents."""
    source = Path(file_path)
    if not source.exists():
        raise ValidationError(
            user_message=f"Project file not found: '{source.name}'.",
            technical_details=f"Path does not exist: {source}",
            recovery_hint="Check the file path and try again.",
        )
    try:
        raw_payload: Any = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValidationError(
            user_message=f"Cannot read project file '{source.name}': file is corrupted.",
            technical_details=str(exc),
            recovery_hint="Re-create the project file by running a new analysis.",
        ) from exc
    if not isinstance(raw_payload, dict):
        raise ValidationError(
            user_message=f"Project file '{source.name}' has an invalid structure.",
            technical_details="Top-level JSON value is not an object",
        )
    payload: dict[str, Any] = raw_payload
    if payload.get("_vibproj_version") != VIBPROJ_SCHEMA_VERSION:
        raise ValidationError(
            user_message=(
                f"Unsupported project file version: '{payload.get('_vibproj_version', '')}'. "
                f"Expected '{VIBPROJ_SCHEMA_VERSION}'."
            ),
            technical_details=f"_vibproj_version={payload.get('_vibproj_version')!r}",
            recovery_hint="Re-create the project file with the current IVA version.",
        )
    result_raw = payload.get("result")
    if not isinstance(result_raw, dict):
        raise ValidationError(
            user_message=f"Project file '{source.name}' is missing a valid result section.",
            technical_details="payload['result'] is absent or not an object",
        )
    try:
        result = analysis_result_from_dict(result_raw)
        settings = _settings_from_dict(payload.get("settings"))
        role_assignment = _role_assignment_from_dict(payload.get("role_assignment"))
        output_dir_raw = payload.get("output_dir")
        output_dir = Path(str(output_dir_raw)) if output_dir_raw else None
    except ValidationError:
        raise
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        raise ValidationError(
            user_message=f"Project file '{source.name}' is corrupted.",
            technical_details=str(exc),
            recovery_hint="Re-create the project file by running a new analysis.",
        ) from exc
    session = AnalysisSession(
        source_file_path=result.source_file_path,
        role_assignment=role_assignment,
        settings=settings,
        result=result,
        warnings=list(result.warnings),
        output_dir=output_dir,
    )
    logger.info("load_project: loaded session %s from '%s'", result.session_id, source.name)
    return session


def _settings_to_dict(settings: AnalysisSettings) -> dict[str, Any]:
    flow = settings.flow_parameters
    return {
        "preprocessing": {
            name: getattr(settings.preprocessing, name)
            for name in PreprocessingSettings.__dataclass_fields__
        },
        "spectral": {
            **{
                name: getattr(settings.spectral, name)
                for name in SpectralSettings.__dataclass_fields__
                if name != "window_type"
            },
            "window_type": str(settings.spectral.window_type),
        },
        "flow_parameters": (
            {
                **{
                    name: getattr(flow, name)
                    for name in FlowParameters.__dataclass_fields__
                    if name != "geometry_type"
                },
                "geometry_type": str(flow.geometry_type) if flow.geometry_type else None,
            }
            if flow is not None
            else None
        ),
    }


def _settings_from_dict(raw: Any) -> AnalysisSettings:  # noqa: ANN401
    if raw is None:
        return AnalysisSettings()
    if not isinstance(raw, dict):
        raise TypeError("settings must be an object")
    preprocessing_raw = raw.get("preprocessing", {})
    spectral_raw = raw.get("spectral", {})
    if not isinstance(preprocessing_raw, dict) or not isinstance(spectral_raw, dict):
        raise TypeError("settings sections must be objects")
    spectral_values = dict(spectral_raw)
    spectral_values["window_type"] = WindowType(
        str(spectral_values.get("window_type", WindowType.HANN))
    )
    flow_raw = raw.get("flow_parameters")
    flow = None
    if flow_raw is not None:
        if not isinstance(flow_raw, dict):
            raise TypeError("flow_parameters must be an object")
        flow_values = dict(flow_raw)
        geometry = flow_values.get("geometry_type")
        flow_values["geometry_type"] = GeometryType(str(geometry)) if geometry else None
        flow = FlowParameters(**flow_values)
    return AnalysisSettings(
        preprocessing=PreprocessingSettings(**preprocessing_raw),
        spectral=SpectralSettings(**spectral_values),
        flow_parameters=flow,
    )


def _role_assignment_to_dict(
    assignment: ColumnRoleAssignment | None,
) -> dict[str, Any] | None:
    if assignment is None:
        return None
    return {
        "time_column": assignment.time_column,
        "primary_signal_column": assignment.primary_signal_column,
        "signal_role": str(assignment.signal_role),
        "additional_columns": {
            name: str(role) for name, role in assignment.additional_columns.items()
        },
        "sampling_rate_hz": float(assignment.sampling_rate_hz),
        "sensor_conversion_factor": assignment.sensor_conversion_factor,
    }


def _role_assignment_from_dict(raw: Any) -> ColumnRoleAssignment | None:  # noqa: ANN401
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise TypeError("role_assignment must be an object")
    additional_raw = raw.get("additional_columns", {})
    if not isinstance(additional_raw, dict):
        raise TypeError("additional_columns must be an object")
    return ColumnRoleAssignment(
        time_column=str(raw["time_column"]),
        primary_signal_column=str(raw["primary_signal_column"]),
        signal_role=SignalRole(str(raw["signal_role"])),
        additional_columns={
            str(name): SignalRole(str(role)) for name, role in additional_raw.items()
        },
        sampling_rate_hz=float(raw["sampling_rate_hz"]),
        sensor_conversion_factor=(
            float(raw["sensor_conversion_factor"])
            if raw.get("sensor_conversion_factor") is not None
            else None
        ),
    )
