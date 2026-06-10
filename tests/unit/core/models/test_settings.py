"""Tests for settings dataclasses and their default values.

Default values are verified against documentation/10_data_models_and_schemas.md.
"""

from __future__ import annotations

from iva.core.models.enums import WindowType
from iva.core.models.settings import AnalysisSettings, PreprocessingSettings, SpectralSettings


class TestPreprocessingSettings:
    def test_default_instantiation(self) -> None:
        s = PreprocessingSettings()
        assert s is not None

    def test_defaults_match_documentation(self) -> None:
        s = PreprocessingSettings()
        assert s.remove_mean is True
        assert s.remove_outliers is True
        assert s.outlier_window_samples == 21
        assert s.outlier_threshold_sigma == 4.0
        assert s.fill_gaps is True
        assert s.max_gap_ms == 50.0
        assert s.apply_bandpass_filter is True
        assert s.filter_low_hz == 5.0
        assert s.filter_high_hz == 250.0
        assert s.filter_order == 4

    def test_is_frozen(self) -> None:
        import pytest

        s = PreprocessingSettings()
        with pytest.raises((AttributeError, TypeError)):
            s.remove_mean = False  # type: ignore[misc]

    def test_custom_values(self) -> None:
        s = PreprocessingSettings(remove_mean=False, filter_order=2)
        assert s.remove_mean is False
        assert s.filter_order == 2


class TestSpectralSettings:
    def test_default_instantiation(self) -> None:
        s = SpectralSettings()
        assert s is not None

    def test_defaults_match_documentation(self) -> None:
        s = SpectralSettings()
        assert s.window_type == WindowType.HANN
        assert s.segment_length_samples == 1024
        assert s.overlap_fraction == 0.5
        assert s.peak_detection_threshold_db == 10.0
        assert s.peak_min_width_hz == 0.5
        assert s.rms_band_low_hz is None
        assert s.rms_band_high_hz is None
        assert s.rms_window_seconds == 1.0

    def test_is_frozen(self) -> None:
        import pytest

        s = SpectralSettings()
        with pytest.raises((AttributeError, TypeError)):
            s.segment_length_samples = 512  # type: ignore[misc]


class TestAnalysisSettings:
    def test_default_instantiation(self) -> None:
        s = AnalysisSettings()
        assert isinstance(s.preprocessing, PreprocessingSettings)
        assert isinstance(s.spectral, SpectralSettings)
        assert s.flow_parameters is None

    def test_nested_defaults_are_separate_objects(self) -> None:
        s1 = AnalysisSettings()
        s2 = AnalysisSettings()
        # Each instance should get its own nested objects
        assert s1.preprocessing is not s2.preprocessing
        assert s1.spectral is not s2.spectral

    def test_is_frozen(self) -> None:
        import pytest

        s = AnalysisSettings()
        with pytest.raises((AttributeError, TypeError)):
            s.flow_parameters = None  # type: ignore[misc]
