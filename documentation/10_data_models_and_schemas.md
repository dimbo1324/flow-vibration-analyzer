# 10. Модели данных и схемы — Industrial Vibration Analyzer

## Назначение документа

Этот документ описывает все структуры данных, используемые внутри приложения. Каждая модель имеет чётко определённые поля, типы и инварианты. Понимание моделей необходимо для работы с любым модулем приложения.

---

## Принципы работы с данными

Все внутренние модели данных реализованы как классы данных Python (`@dataclass`) или классы Pydantic с валидацией. Модели неизменяемы там, где это возможно: данные создаются один раз и не модифицируются в процессе передачи между слоями. Это исключает ситуацию, когда один модуль неожиданно изменяет данные, используемые другим.

Каждая модель живёт в директории `core/models/`. Инфраструктурный слой и слой приложения используют эти модели, но не создают собственных параллельных структур для одних и тех же данных.

---

## RawFileData

Результат чтения файла до какой-либо проверки и обработки.

```python
@dataclass(frozen=True)
class RawFileData:
    file_path: str                      # Полный путь к исходному файлу
    file_format: str                    # 'csv', 'parquet', 'excel'
    column_names: list[str]             # Имена колонок как в файле
    column_dtypes: dict[str, str]       # Типы данных по имени колонки
    row_count: int                      # Количество строк
    file_size_bytes: int                # Размер файла в байтах
    data: Any                           # Таблица данных (pandas DataFrame)
    read_timestamp: datetime            # Время завершения чтения
```

---

## ColumnRoleAssignment

Назначение ролей колонкам файла пользователем.

```python
@dataclass(frozen=True)
class ColumnRoleAssignment:
    time_column: str                         # Обязательно
    primary_signal_column: str               # Обязательно
    signal_role: SignalRole                  # Перечисление: ACCELERATION_X/Y/Z, PRESSURE, VELOCITY
    additional_columns: dict[str, SignalRole] # Необязательные дополнительные сигналы
    sampling_rate_hz: float                  # Частота дискретизации, Гц
    sensor_conversion_factor: float | None   # Коэффициент преобразования датчика
```

---

## ValidatedSignalData

Данные после проверки структуры и качества, до математической обработки.

```python
@dataclass(frozen=True)
class ValidatedSignalData:
    time_array: np.ndarray              # Временна́я ось, с (float64)
    signal_array: np.ndarray            # Основной сигнал (float64)
    sampling_rate_hz: float             # Подтверждённая частота дискретизации
    duration_seconds: float             # Длительность записи
    sample_count: int                   # Количество отсчётов
    signal_role: SignalRole             # Физическая роль сигнала
    physical_unit: str                  # Единица измерения после преобразования
    missing_fraction: float             # Доля пропусков [0.0–1.0]
    outlier_fraction: float             # Доля выбросов [0.0–1.0]
    warnings: list[ValidationWarning]   # Предупреждения валидации
```

---

## ProcessedSignalData

Данные после предобработки. Содержит обе версии сигнала.

```python
@dataclass(frozen=True)
class ProcessedSignalData:
    time_array: np.ndarray              # Временна́я ось, с
    signal_cleaned: np.ndarray          # После удаления выбросов и пропусков
    signal_filtered: np.ndarray         # После применения фильтра
    preprocessing_log: list[str]        # Описание применённых шагов
    applied_settings: PreprocessingSettings  # Настройки, использованные при обработке
```

---

## PreprocessingSettings

Настройки предобработки сигнала.

```python
@dataclass(frozen=True)
class PreprocessingSettings:
    remove_mean: bool = True
    remove_outliers: bool = True
    outlier_window_samples: int = 21
    outlier_threshold_sigma: float = 4.0
    fill_gaps: bool = True
    max_gap_ms: float = 50.0
    apply_bandpass_filter: bool = True
    filter_low_hz: float = 5.0
    filter_high_hz: float = 250.0
    filter_order: int = 4
```

---

## SpectralSettings

Настройки спектрального анализа.

```python
@dataclass(frozen=True)
class SpectralSettings:
    window_type: WindowType             # Перечисление: HANN, HAMMING, RECTANGULAR
    segment_length_samples: int = 1024
    overlap_fraction: float = 0.5
    peak_detection_threshold_db: float = 10.0   # Порог над медианой
    peak_min_width_hz: float = 0.5
    rms_band_low_hz: float | None = None
    rms_band_high_hz: float | None = None
    rms_window_seconds: float = 1.0
```

---

## SpectralPeak

Описание одного найденного пика в спектре.

```python
@dataclass(frozen=True)
class SpectralPeak:
    frequency_hz: float
    amplitude: float                    # Значение PSD в пике
    width_hz_3db: float                 # Ширина на уровне -3 дБ
    interpretation: PeakInterpretation  # Перечисление: VORTEX_SHEDDING, HARMONIC, STRUCTURAL, UNKNOWN
    confidence: float                   # Уверенность в интерпретации [0.0–1.0]
```

---

## SpectrumResult

Полный результат спектрального анализа.

```python
@dataclass(frozen=True)
class SpectrumResult:
    frequencies: np.ndarray             # Массив частот, Гц
    psd_values: np.ndarray              # Массив значений PSD
    dominant_peak: SpectralPeak | None  # Пик с наибольшей амплитудой
    all_peaks: list[SpectralPeak]       # Все найденные пики
    rms_total: float                    # RMS по полосе анализа
    rms_in_band: float | None           # RMS в заданной пользователем полосе
    rms_trend: np.ndarray               # Скользящий RMS во времени
    applied_settings: SpectralSettings
```

---

## FlowParameters

Параметры течения и геометрии, введённые пользователем.

```python
@dataclass(frozen=True)
class FlowParameters:
    cylinder_diameter_m: float          # Диаметр цилиндра, м
    mean_flow_velocity_ms: float        # Средняя скорость потока, м/с
    fluid_density_kgm3: float           # Плотность среды, кг/м³
    dynamic_viscosity_pas: float        # Динамическая вязкость, Па·с
    natural_frequency_hz: float | None  # Собственная частота конструкции, Гц
    damping_ratio: float | None         # Коэффициент демпфирования
    cylinder_spacing_m: float | None    # Расстояние между цилиндрами (для тандема)
    geometry_type: GeometryType         # Перечисление: SINGLE_CYLINDER, TANDEM
```

---

## PhysicsResult

Результат физических расчётов.

```python
@dataclass(frozen=True)
class PhysicsResult:
    reynolds_number: float
    strouhal_number: float
    calculated_shedding_frequency_hz: float
    velocity_ratio: float | None        # Приведённая скорость
    frequency_ratio: float | None       # Отношение fs / fn
    kinematic_viscosity_m2s: float      # Производная величина
```

---

## RiskAssessment

Результат оценки риска резонанса.

```python
@dataclass(frozen=True)
class RiskAssessment:
    risk_level: RiskLevel               # Перечисление: SAFE, WATCH, CRITICAL
    dominant_frequency_deviation: float # Отклонение от собственной частоты [0.0–1.0]
    recommendation_text: str            # Текстовая рекомендация для инженера
    contributing_factors: list[str]     # Факторы, повлиявшие на классификацию
```

---

## ValidationResult

Результат сравнения эксперимента с расчётом.

```python
@dataclass(frozen=True)
class ValidationResult:
    coordinate_array: np.ndarray
    experiment_array: np.ndarray
    cfd_array: np.ndarray
    rmse: float
    mae: float
    mape: float | None
    pearson_r: float
    is_mape_valid: bool                 # False, если в знаменателе есть нули
```

---

## AnalysisResult

Главный объект, объединяющий все результаты одного сеанса анализа.

```python
@dataclass(frozen=True)
class AnalysisResult:
    session_id: str                         # UUID сеанса
    completed_at: datetime
    source_file_path: str
    source_file_md5: str
    validated_data: ValidatedSignalData
    processed_data: ProcessedSignalData
    spectrum: SpectrumResult
    physics: PhysicsResult | None           # None, если параметры не введены
    risk: RiskAssessment | None             # None, если fn не задана
    validation: ValidationResult | None     # None, если нет CFD-файла
    warnings: list[str]                     # Все предупреждения из всех этапов
```

---

## AnalysisSettings

Совокупность всех настроек, использованных в одном сеансе анализа.

```python
@dataclass(frozen=True)
class AnalysisSettings:
    preprocessing: PreprocessingSettings
    spectral: SpectralSettings
    flow_parameters: FlowParameters | None
```

---

*Версия документа: 1.0. Дата: 2025. Ответственный: автор проекта.*
