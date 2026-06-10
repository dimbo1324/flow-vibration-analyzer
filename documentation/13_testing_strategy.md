# 13. Стратегия тестирования — Industrial Vibration Analyzer

## Назначение документа

Этот документ описывает подход к тестированию проекта: что тестируется, как тестируется, где хранятся тесты и как они запускаются. Документ отвечает на вопрос «как мы знаем, что приложение работает правильно?».

---

## Принципы тестирования

Тест — это автоматически проверяемое утверждение о поведении кода. Тест имеет ценность только тогда, когда он может упасть: если тест не может провалиться, он не даёт никакой гарантии.

Тесты не заменяют понимание кода и не снимают с разработчика ответственность за правильность алгоритма. Они фиксируют известное правильное поведение и мгновенно сигнализируют, если оно изменилось.

---

## Три уровня тестирования

### Уровень 1 — Модульные тесты

**Что тестируется:** каждая функция и метод в модулях `core/` и `infrastructure/` по отдельности. Зависимости заменяются заглушками.

**Где хранятся:** `tests/unit/`

**Цель:** убедиться, что каждый алгоритм правильно реализован. Подробный перечень тестов для `core/` описан в `12_validation_and_verification.md`.

**Требование к покрытию:** не менее 80% строк кода для `core/`, не менее 60% для `infrastructure/`.

### Уровень 2 — Интеграционные тесты

**Что тестируется:** полный пайплайн от загрузки файла до формирования `AnalysisResult`. Используются реальные тестовые файлы из `tests/fixtures/`.

**Где хранятся:** `tests/integration/`

**Цель:** убедиться, что модули корректно взаимодействуют и данные правильно передаются между этапами конвейера.

**Примеры тестовых сценариев:**
- файл с чистыми данными → полный анализ → результат соответствует эталону;
- файл с пропусками → предупреждения отображены → анализ выполнен на заполненных данных;
- файл с некорректной временно́й осью → `ValidationError` поднят, работа прекращена;
- два файла (эксперимент + CFD) → результат сравнения содержит все метрики.

### Уровень 3 — Системные тесты

**Что тестируется:** работа приложения как единого целого, включая запуск GUI. Используется автоматизация интерфейса через `pytest-qt`.

**Где хранятся:** `tests/system/`

**Цель:** проверить ключевые пользовательские сценарии из `07_user_scenarios.md` в автоматическом режиме.

**Охват:** первые два пользовательских сценария (базовый анализ и сравнение с CFD).

---

## Структура директории тестов

```
tests/
├─ unit/
│  ├─ core/
│  │  ├─ signal/
│  │  │  ├─ test_preprocessor.py
│  │  │  ├─ test_filter.py
│  │  │  └─ test_outlier_detector.py
│  │  ├─ spectrum/
│  │  │  ├─ test_psd_calculator.py
│  │  │  ├─ test_peak_finder.py
│  │  │  └─ test_rms_calculator.py
│  │  ├─ physics/
│  │  │  ├─ test_reynolds_calculator.py
│  │  │  ├─ test_strouhal_calculator.py
│  │  │  ├─ test_vortex_frequency.py
│  │  │  └─ test_lock_in_risk.py
│  │  └─ validation/
│  │     └─ test_error_metrics.py
│  └─ infrastructure/
│     ├─ test_csv_reader.py
│     ├─ test_parquet_reader.py
│     └─ test_excel_reader.py
│
├─ integration/
│  ├─ test_full_pipeline_clean_data.py
│  ├─ test_pipeline_with_gaps.py
│  ├─ test_pipeline_invalid_file.py
│  └─ test_validation_pipeline.py
│
├─ system/
│  ├─ test_scenario_basic_analysis.py
│  └─ test_scenario_cfd_comparison.py
│
└─ fixtures/
   ├─ clean_signal_1000hz_60s.csv
   ├─ signal_with_gaps.csv
   ├─ signal_with_outliers.csv
   ├─ malformed_time_axis.csv
   ├─ cfd_profile.csv
   ├─ dissertation/
   │  └─ experimental_run_anonymized.csv
   ├─ expected_results.json
   └─ generator/
      └─ generate_synthetic_data.py
```

---

## Именование тестов

Имя каждого тестового файла начинается с `test_`. Имя каждой тестовой функции также начинается с `test_` и описывает конкретное утверждение:

```python
def test_remove_mean_returns_zero_mean_signal():
    ...

def test_apply_bandpass_filter_suppresses_out_of_band_frequency():
    ...

def test_full_pipeline_detects_expected_peak_frequency():
    ...
```

Именование в форме «что должно произойти» позволяет читать список тестов как спецификацию поведения.

---

## Параметризованные тесты

Для проверки нескольких похожих случаев используется параметризация через `@pytest.mark.parametrize`, а не дублирование кода:

```python
@pytest.mark.parametrize("input_velocity, input_diameter, expected_re", [
    (1.0, 0.010, 9960),
    (2.0, 0.012, 23904),
    (5.0, 0.050, 249000),
])
def test_reynolds_number_calculation(input_velocity, input_diameter, expected_re):
    result = reynolds_calculator.calculate(
        V=input_velocity, D=input_diameter, rho=998.0, mu=1.002e-3
    )
    assert abs(result - expected_re) / expected_re < 0.001
```

---

## Тестирование граничных случаев

Для каждого расчётного модуля обязательно наличие тестов на граничные случаи:

- сигнал из одного отсчёта;
- сигнал с нулевой амплитудой;
- частота срыва равна собственной частоте (риск = критический);
- частота среза фильтра равна нулю или частоте Найквиста;
- пустой файл;
- файл только с заголовком без данных;
- массивы эксперимента и CFD разной длины при сравнении.

---

## Тестирование обработки ошибок

Тесты на обработку ошибок проверяют, что конкретное исключение поднимается при конкретном плохом вводе:

```python
def test_bandpass_filter_raises_error_when_low_freq_exceeds_nyquist():
    signal = np.random.randn(1000)
    with pytest.raises(FilterConfigurationError):
        filter_module.apply_bandpass_filter(signal, sampling_rate_hz=100, low_hz=60, high_hz=90, order=4)
```

---

## Фикстуры

Общие тестовые данные вынесены в фикстуры `conftest.py` и не дублируются в каждом тесте:

```python
@pytest.fixture
def clean_signal_1hz():
    """Синусоида 1 Гц, 10 секунд, частота дискретизации 100 Гц."""
    t = np.linspace(0, 10, 1000)
    return np.sin(2 * np.pi * 1 * t), t, 100.0
```

---

## Запуск тестов

```bash
# Все тесты
pytest

# Только модульные тесты
pytest tests/unit/

# Только тесты расчётного ядра
pytest tests/unit/core/

# С отчётом о покрытии
pytest --cov=core --cov-report=html tests/unit/

# Конкретный тест
pytest tests/unit/core/spectrum/test_psd_calculator.py::test_welch_detects_known_frequency
```

---

## Автоматический запуск тестов

Тесты запускаются автоматически в двух случаях:

1. **Перед каждым коммитом** — хук `pre-commit` запускает быстрые модульные тесты (`tests/unit/`) и отклоняет коммит при падении любого теста.

2. **При сборке релиза** — скрипт `scripts/build_installer.py` запускает все тесты (unit + integration) до начала сборки. Если тесты не пройдены — сборка не запускается.

---

## Баги превращаются в тесты

При обнаружении бага разработчик обязан:
1. Написать тест, который воспроизводит баг (тест должен упасть на текущем коде).
2. Исправить баг.
3. Убедиться, что тест прошёл.
4. Оставить тест в репозитории навсегда.

Это гарантирует, что исправленные ошибки не возвращаются при последующих изменениях кода.

---

*Версия документа: 1.0. Дата: 2025. Ответственный: автор проекта.*
