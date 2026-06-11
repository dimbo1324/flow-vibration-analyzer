"""Settings manager — loads and saves :class:`AnalysisSettings` from disk.

Two entry points:
- ``load_defaults`` — reads ``config/defaults.toml`` (application defaults).
- ``load_analysis_config_json`` — reads a user-supplied JSON config file that
  specifies column roles AND analysis settings for the CLI workflow.
- ``save_settings`` — writes settings to a TOML file.

Architecture rule: this module must NOT import from ``iva.ui`` or ``PySide6``.
"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

from iva.core.models.enums import GeometryType, SignalRole, WindowType
from iva.core.models.exceptions import ExportError, ProcessingError
from iva.core.models.flow_parameters import FlowParameters
from iva.core.models.settings import AnalysisSettings, PreprocessingSettings, SpectralSettings
from iva.core.models.signal_data import ColumnRoleAssignment
from iva.infrastructure.logging.app_logger import get_logger

logger = get_logger(__name__)

__all__ = [
    "load_defaults",
    "load_analysis_config_json",
    "save_settings",
]

_DEFAULT_CONFIG_PATH = Path("config") / "defaults.toml"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load_defaults(config_path: str | Path = _DEFAULT_CONFIG_PATH) -> AnalysisSettings:
    """Load default :class:`AnalysisSettings` from a TOML file.

    The file is expected to follow the layout of ``config/defaults.toml``.
    Missing keys fall back to dataclass defaults.

    Args:
        config_path: Path to the TOML config file.

    Returns:
        An :class:`AnalysisSettings` populated from the file.

    Raises:
        ProcessingError: If the file cannot be read or parsed.
    """
    config_path = Path(config_path)
    logger.debug("load_defaults: reading '%s'", config_path)

    if not config_path.exists():
        logger.warning("Defaults file '%s' not found — using built-in defaults.", config_path)
        return AnalysisSettings()

    try:
        with open(config_path, "rb") as fh:
            data = tomllib.load(fh)
    except Exception as exc:
        raise ProcessingError(
            user_message=f"Cannot read settings file '{config_path.name}'.",
            technical_details=str(exc),
            recovery_hint="Ensure the file is valid TOML.",
        ) from exc

    preprocessing = _parse_preprocessing(data.get("preprocessing", {}))
    spectral = _parse_spectral(data.get("spectral", {}))

    logger.info("load_defaults: settings loaded from '%s'", config_path.name)
    return AnalysisSettings(preprocessing=preprocessing, spectral=spectral, flow_parameters=None)


def load_analysis_config_json(
    config_path: str | Path,
) -> tuple[ColumnRoleAssignment, AnalysisSettings]:
    """Parse a JSON analysis config file into domain objects.

    Expected top-level keys: ``columns``, ``preprocessing``, ``spectral``,
    ``flow_parameters`` (optional / nullable).

    Args:
        config_path: Path to the JSON config file.

    Returns:
        A ``(ColumnRoleAssignment, AnalysisSettings)`` tuple.

    Raises:
        IVAError: If the file is missing, unreadable, or structurally invalid.
    """
    config_path = Path(config_path)
    logger.debug("load_analysis_config_json: reading '%s'", config_path)

    if not config_path.exists():
        from iva.core.models.exceptions import IVAFileNotFoundError

        raise IVAFileNotFoundError(
            user_message=f"Config file not found: '{config_path.name}'.",
            technical_details=f"Full path: {config_path}",
            recovery_hint="Check the --config argument.",
        )

    try:
        with open(config_path, encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        raise ProcessingError(
            user_message=f"Config file '{config_path.name}' contains invalid JSON.",
            technical_details=str(exc),
            recovery_hint="Validate the JSON syntax (e.g. with jsonlint).",
        ) from exc
    except OSError as exc:
        raise ProcessingError(
            user_message=f"Cannot read config file '{config_path.name}'.",
            technical_details=str(exc),
        ) from exc

    # --- columns section ---------------------------------------------------
    col_section = data.get("columns", {})
    try:
        role_assignment = _parse_column_assignment(col_section)
    except (KeyError, ValueError) as exc:
        raise ProcessingError(
            user_message="Config file 'columns' section is incomplete or invalid.",
            technical_details=str(exc),
            recovery_hint="Check that 'time_column', 'primary_signal_column', "
            "'signal_role', and 'sampling_rate_hz' are present.",
        ) from exc

    # --- settings sections -------------------------------------------------
    preprocessing = _parse_preprocessing(data.get("preprocessing", {}))
    spectral = _parse_spectral(data.get("spectral", {}))
    flow_parameters = _parse_flow_parameters(data.get("flow_parameters"))

    settings = AnalysisSettings(
        preprocessing=preprocessing,
        spectral=spectral,
        flow_parameters=flow_parameters,
    )
    logger.info(
        "load_analysis_config_json: loaded from '%s', flow_params=%s",
        config_path.name,
        "present" if flow_parameters is not None else "absent",
    )
    return role_assignment, settings


def save_settings(settings: AnalysisSettings, config_path: str | Path) -> None:
    """Write *settings* to a TOML file.

    Only the preprocessing and spectral sections are written (flow_parameters
    are not persisted here — they are entered per-session).

    Args:
        settings: Settings to persist.
        config_path: Destination path.

    Raises:
        ExportError: If the file cannot be written.
    """
    config_path = Path(config_path)
    logger.debug("save_settings: writing to '%s'", config_path)

    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as fh:
            fh.write(_settings_to_toml(settings))
    except OSError as exc:
        raise ExportError(
            user_message=f"Cannot write settings to '{config_path.name}'.",
            technical_details=str(exc),
        ) from exc

    logger.info("save_settings: written to '%s'", config_path.name)


# ---------------------------------------------------------------------------
# Internal parsers
# ---------------------------------------------------------------------------


def _parse_column_assignment(col: dict) -> ColumnRoleAssignment:  # type: ignore[type-arg]
    """Build a :class:`ColumnRoleAssignment` from the ``columns`` dict."""
    raw_role = col["signal_role"]
    try:
        role = SignalRole(raw_role)
    except ValueError as exc:
        valid = [r.value for r in SignalRole]
        raise ValueError(f"Unknown signal_role '{raw_role}'. Valid values: {valid}") from exc

    additional_raw: list[dict] = col.get("additional_columns", []) or []  # type: ignore[assignment]
    additional: dict[str, SignalRole] = {}
    for item in additional_raw:
        if isinstance(item, dict):
            col_name = item.get("column", "")
            col_role_str = item.get("role", "")
            if col_name and col_role_str:
                try:
                    additional[col_name] = SignalRole(col_role_str)
                except ValueError:
                    pass

    sensor_factor = col.get("sensor_conversion_factor")
    if sensor_factor is not None:
        sensor_factor = float(sensor_factor)

    return ColumnRoleAssignment(
        time_column=str(col["time_column"]),
        primary_signal_column=str(col["primary_signal_column"]),
        signal_role=role,
        additional_columns=additional,
        sampling_rate_hz=float(col["sampling_rate_hz"]),
        sensor_conversion_factor=sensor_factor,
    )


def _parse_preprocessing(pp: dict) -> PreprocessingSettings:  # type: ignore[type-arg]
    """Build :class:`PreprocessingSettings` from a dict, with defaults."""
    defaults = PreprocessingSettings()

    def _get(key: str, default):  # type: ignore[no-untyped-def]
        val = pp.get(key)
        return val if val is not None else default

    # Map JSON key names from the example config to dataclass field names
    # JSON uses "filter_cutoff_low_hz" / "filter_cutoff_high_hz" / "filter_type"
    # Dataclass uses filter_low_hz / filter_high_hz / apply_bandpass_filter
    apply_filter = defaults.apply_bandpass_filter
    filter_type = pp.get("filter_type")
    if filter_type is not None:
        apply_filter = filter_type.lower() not in ("none", "off", "disabled")

    return PreprocessingSettings(
        remove_mean=bool(_get("remove_mean", defaults.remove_mean)),
        remove_outliers=bool(_get("detect_outliers", defaults.remove_outliers)),
        outlier_window_samples=int(_get("outlier_window_samples", defaults.outlier_window_samples)),
        outlier_threshold_sigma=float(
            _get("outlier_threshold_sigma", defaults.outlier_threshold_sigma)
        ),
        fill_gaps=bool(_get("fill_gaps", defaults.fill_gaps)),
        max_gap_ms=float(_get("max_gap_ms", defaults.max_gap_ms)),
        apply_bandpass_filter=apply_filter,
        filter_low_hz=float(
            _get(
                "filter_cutoff_low_hz",
                _get("filter_low_hz", defaults.filter_low_hz),
            )
        ),
        filter_high_hz=float(
            _get(
                "filter_cutoff_high_hz",
                _get("filter_high_hz", defaults.filter_high_hz),
            )
        ),
        filter_order=int(_get("filter_order", defaults.filter_order)),
    )


def _parse_spectral(sp: dict) -> SpectralSettings:  # type: ignore[type-arg]
    """Build :class:`SpectralSettings` from a dict, with defaults."""
    defaults = SpectralSettings()

    def _get(key: str, default):  # type: ignore[no-untyped-def]
        val = sp.get(key)
        return val if val is not None else default

    raw_window = _get("window_type", defaults.window_type)
    try:
        window = WindowType(raw_window)
    except ValueError:
        window = defaults.window_type

    # JSON uses "nperseg" and "noverlap" (absolute samples)
    # Dataclass uses segment_length_samples and overlap_fraction
    nperseg = int(_get("nperseg", _get("segment_length_samples", defaults.segment_length_samples)))
    noverlap_raw = sp.get("noverlap")
    if noverlap_raw is not None:
        overlap_fraction = float(noverlap_raw) / float(nperseg) if nperseg > 0 else 0.5
    else:
        overlap_fraction = float(_get("overlap_fraction", defaults.overlap_fraction))

    # JSON threshold is absolute dB; dataclass is relative dB above baseline
    # The peak_finder computes baseline = median(psd_db) and threshold = baseline + offset
    # The JSON field "peak_threshold_db" may be an absolute or relative value.
    # We store as-is since it maps to peak_detection_threshold_db (offset from baseline).
    threshold_db = float(
        _get(
            "peak_detection_threshold_db",
            _get("peak_threshold_db", defaults.peak_detection_threshold_db),
        )
    )
    # If user supplied a large negative absolute value (e.g. -40 dB) treat as
    # offset magnitude; peak_finder adds it to baseline so keep it positive.
    if threshold_db < 0:
        threshold_db = abs(threshold_db)

    band_low = sp.get("rms_band_low_hz") or sp.get("freq_min_hz") or defaults.rms_band_low_hz
    band_high = sp.get("rms_band_high_hz") or sp.get("freq_max_hz") or defaults.rms_band_high_hz

    return SpectralSettings(
        window_type=window,
        segment_length_samples=nperseg,
        overlap_fraction=overlap_fraction,
        peak_detection_threshold_db=threshold_db,
        peak_min_width_hz=float(_get("peak_min_width_hz", defaults.peak_min_width_hz)),
        rms_band_low_hz=float(band_low) if band_low is not None else None,
        rms_band_high_hz=float(band_high) if band_high is not None else None,
        rms_window_seconds=float(_get("rms_window_seconds", defaults.rms_window_seconds)),
    )


def _parse_flow_parameters(fp: dict | None) -> FlowParameters | None:  # type: ignore[type-arg]
    """Build a :class:`FlowParameters` from the ``flow_parameters`` dict.

    Returns ``None`` if *fp* is ``None`` or empty.
    """
    if not fp:
        return None

    raw_geom = fp.get("geometry_type")
    geometry: GeometryType | None = None
    if raw_geom is not None:
        try:
            geometry = GeometryType(raw_geom)
        except ValueError:
            logger.warning("Unknown geometry_type '%s' — defaulting to SINGLE_CYLINDER", raw_geom)
            geometry = GeometryType.SINGLE_CYLINDER

    def _opt_float(key: str) -> float | None:
        val = fp.get(key)
        return float(val) if val is not None else None

    return FlowParameters(
        cylinder_diameter_m=_opt_float("cylinder_diameter_m"),
        mean_flow_velocity_ms=_opt_float("mean_flow_velocity_ms"),
        fluid_density_kgm3=_opt_float("fluid_density_kgm3"),
        dynamic_viscosity_pas=_opt_float("dynamic_viscosity_pas"),
        natural_frequency_hz=_opt_float("natural_frequency_hz"),
        damping_ratio=_opt_float("damping_ratio"),
        cylinder_spacing_m=_opt_float("cylinder_spacing_m"),
        geometry_type=geometry,
    )


def _settings_to_toml(settings: AnalysisSettings) -> str:
    """Serialise *settings* to a TOML-formatted string (no third-party lib)."""
    pp = settings.preprocessing
    sp = settings.spectral

    lines = [
        "# IVA analysis settings — generated by settings_manager",
        "",
        "[preprocessing]",
        f"remove_mean = {str(pp.remove_mean).lower()}",
        f"remove_outliers = {str(pp.remove_outliers).lower()}",
        f"outlier_window_samples = {pp.outlier_window_samples}",
        f"outlier_threshold_sigma = {pp.outlier_threshold_sigma}",
        f"fill_gaps = {str(pp.fill_gaps).lower()}",
        f"max_gap_ms = {pp.max_gap_ms}",
        f"apply_bandpass_filter = {str(pp.apply_bandpass_filter).lower()}",
        f"filter_low_hz = {pp.filter_low_hz}",
        f"filter_high_hz = {pp.filter_high_hz}",
        f"filter_order = {pp.filter_order}",
        "",
        "[spectral]",
        f'window_type = "{sp.window_type}"',
        f"segment_length_samples = {sp.segment_length_samples}",
        f"overlap_fraction = {sp.overlap_fraction}",
        f"peak_detection_threshold_db = {sp.peak_detection_threshold_db}",
        f"peak_min_width_hz = {sp.peak_min_width_hz}",
        f"rms_band_low_hz = {sp.rms_band_low_hz if sp.rms_band_low_hz is not None else 'null'}",
        f"rms_band_high_hz = {sp.rms_band_high_hz if sp.rms_band_high_hz is not None else 'null'}",
        f"rms_window_seconds = {sp.rms_window_seconds}",
        "",
    ]
    return "\n".join(lines)
