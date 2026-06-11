"""Cross-module integration test for the core analysis chain.

Wires the already-implemented Stage 3-5 modules together directly to verify
they interoperate end to end:

    validate (infrastructure) -> preprocess (core.signal) ->
    PSD + peaks + RMS (core.spectrum)

This intentionally does NOT use any app/CLI orchestration (a later stage); it
exercises the existing modules through their public functions only.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from iva.core.models.enums import SignalRole
from iva.core.models.settings import PreprocessingSettings, SpectralSettings
from iva.core.models.signal_data import ColumnRoleAssignment, RawFileData
from iva.core.signal.preprocessor import preprocess_signal
from iva.core.spectrum.peak_finder import find_peaks
from iva.core.spectrum.psd_calculator import calculate_psd
from iva.core.spectrum.rms_calculator import calculate_total_rms
from iva.infrastructure.validators.data_quality_checker import check_data_quality

FS = 1000.0
DURATION = 10.0
FREQ = 40.0
AMPLITUDE = 1.0


def _raw_clean_sine() -> RawFileData:
    n = int(FS * DURATION)
    t = np.linspace(0.0, DURATION, n, endpoint=False)
    signal = AMPLITUDE * np.sin(2.0 * np.pi * FREQ * t)
    df = pd.DataFrame({"time_s": t, "signal": signal})
    return RawFileData(
        file_path=Path("integration_clean_sine.csv"),
        file_format="csv",
        column_names=("time_s", "signal"),
        column_dtypes={"time_s": "float64", "signal": "float64"},
        row_count=len(df),
        file_size_bytes=0,
        data=df,
        read_timestamp=datetime.now(),
    )


def _assignment() -> ColumnRoleAssignment:
    return ColumnRoleAssignment(
        time_column="time_s",
        primary_signal_column="signal",
        signal_role=SignalRole.ACCELERATION_X,
        additional_columns={},
        sampling_rate_hz=FS,
    )


def test_core_chain_clean_sine_end_to_end():
    """A clean 40 Hz sine flows through validate -> preprocess -> spectrum cleanly."""
    validated = check_data_quality(_raw_clean_sine(), _assignment())
    assert validated.sample_count == int(FS * DURATION)
    assert validated.warnings == ()

    processed = preprocess_signal(validated, PreprocessingSettings())

    # The preprocessing pipeline order is fixed (docs/09):
    # remove_mean -> outlier replacement -> fill_gaps -> bandpass filter.
    log_keys = [entry.split(":")[0] for entry in processed.preprocessing_log]
    assert log_keys == [
        "remove_mean",
        "replace_outliers",
        "fill_gaps",
        "apply_bandpass_filter",
    ]

    freqs, psd = calculate_psd(processed.signal_filtered, FS, SpectralSettings())
    peaks = find_peaks(freqs, psd, SpectralSettings())
    assert peaks, "expected at least one spectral peak"
    assert 39.0 <= peaks[0].frequency_hz <= 41.0

    rms = calculate_total_rms(processed.signal_filtered)
    expected = AMPLITUDE / np.sqrt(2.0)
    assert abs(rms - expected) / expected < 0.05
