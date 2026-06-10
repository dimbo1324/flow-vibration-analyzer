# INDUSTRIAL VIBRATION ANALYZER
# Чек-лист разработки проекта — версия 2.0

<!--
  КАК ПОЛЬЗОВАТЬСЯ ЭТИМ ФАЙЛОМ
  ─────────────────────────────
  [ ]  задача не начата
  [~]  задача в работе
  [x]  задача завершена

  Этот файл предназначен для трёх аудиторий:
  • Разработчик-человек: читает всё, работает последовательно.
  • ИИ-ассистент (Claude Code, CODEX и др.): получает отдельный этап
    как задание. Важно: передавайте ИИ только один этап за раз.
  • Новый участник команды: начинает с раздела «Введение для нового
    разработчика» ниже.

  ПУТЬ ЧТЕНИЯ ДЛЯ ИИ-АССИСТЕНТА
  ────────────────────────────────
  Перед началом работы ИИ должен прочитать:
    1. docs/02_architecture.md   — структура папок и запреты
    2. docs/10_data_models_and_schemas.md — все модели данных
    3. docs/19_code_style_and_contribution.md — стиль кода
  Затем прочитать цель и конечный результат нужного этапа.
  Только после этого приступать к задачам.
-->

---

## ВВЕДЕНИЕ ДЛЯ НОВОГО РАЗРАБОТЧИКА

Прежде чем открывать любой код, прочитайте эти три документа из папки `docs/`.
Они отвечают на вопросы «что», «зачем» и «как» без слов автора рядом.

| Документ | Что узнаете |
|---|---|
| `00_project_overview.md` | Что такое IVA и зачем он нужен |
| `02_architecture.md` | Как устроен код и какие правила нельзя нарушать |
| `03_scientific_methodology.md` | Физика задачи и математические методы |

После этого возвращайтесь в этот чек-лист и начинайте с этапа 1.

---

## АРХИТЕКТУРНЫЙ ОРИЕНТИР

Приложение разделено на четыре слоя. Зависимости идут строго сверху вниз.

```
ui/             ← вкладки, виджеты, графики, формы
app/            ← координация, состояние сеанса, фоновые задачи
core/           ← все расчёты, алгоритмы, физические модели
infrastructure/ ← файлы, форматы, логи, экспорт
```

**Три запрета, которые нельзя нарушать никогда:**
1. `core/` не импортирует ничего из `ui/`, `app/` или `infrastructure/`.
2. Любая формула, любой числовой расчёт — только в `core/`.
3. Состояние сеанса — только в `app/analysis_session.py`.

---

## СТРУКТУРА ПРОЕКТА (ЭТАЛОН)

Итоговая структура, к которой приводит весь чек-лист:

```
iva/
├─ ui/
│  ├─ main_window.py
│  ├─ pages/
│  │  ├─ overview_page.py
│  │  ├─ import_page.py
│  │  ├─ signal_page.py
│  │  ├─ spectrum_page.py
│  │  ├─ physics_page.py
│  │  ├─ profiles_page.py
│  │  └─ report_page.py
│  ├─ widgets/
│  │  ├─ chart_widget.py
│  │  ├─ metric_card.py
│  │  ├─ parameter_form.py
│  │  └─ log_panel.py
│  └─ styles/
│     └─ theme.py
├─ app/
│  ├─ analysis_session.py
│  ├─ analysis_runner.py
│  ├─ workflow_coordinator.py
│  └─ settings_manager.py
├─ core/
│  ├─ models/
│  │  ├─ signal_data.py
│  │  ├─ analysis_result.py
│  │  └─ flow_parameters.py
│  ├─ signal/
│  │  ├─ preprocessor.py
│  │  ├─ filter.py
│  │  └─ outlier_detector.py
│  ├─ spectrum/
│  │  ├─ psd_calculator.py
│  │  ├─ peak_finder.py
│  │  └─ rms_calculator.py
│  ├─ physics/
│  │  ├─ reynolds_calculator.py
│  │  ├─ strouhal_calculator.py
│  │  ├─ vortex_frequency.py
│  │  └─ lock_in_risk.py
│  └─ validation/
│     ├─ experiment_vs_cfd.py
│     └─ error_metrics.py
├─ infrastructure/
│  ├─ readers/
│  │  ├─ csv_reader.py
│  │  ├─ parquet_reader.py
│  │  └─ excel_reader.py
│  ├─ writers/
│  │  ├─ pdf_report_writer.py
│  │  └─ csv_export_writer.py
│  └─ logging/
│     └─ app_logger.py
├─ tests/
│  ├─ unit/
│  ├─ integration/
│  ├─ system/
│  └─ fixtures/
├─ scripts/
│  ├─ generate_synthetic_data.py
│  ├─ build_installer.py
│  ├─ iva.spec
│  └─ installer.iss
├─ docs/          ← 23 документа проекта (00–22)
├─ config/
│  └─ defaults.toml
├─ main.py
├─ requirements.txt
├─ requirements-dev.txt
├─ pyproject.toml
└─ README.md
```

---

## КРАТКАЯ СХЕМА 10 ЭТАПОВ

```
[ ] Этап 1   Основа проекта и документация
[ ] Этап 2   Архитектура и модели данных (core/models/)
[ ] Этап 3   Инфраструктура: импорт файлов и синтетические данные
[ ] Этап 4   Предобработка сигнала (core/signal/)
[ ] Этап 5   Спектральный анализ (core/spectrum/)
[ ] Этап 6   Физические расчёты и оценка риска (core/physics/)
[ ] Этап 7   Координирующий слой и CLI (app/ + CLI)
[ ] Этап 8   Desktop-интерфейс PySide6 (ui/)
[ ] Этап 9   Графики, отчёты, сессии, сравнение с CFD
[ ] Этап 10  Качество, производительность, сборка и релиз
```

---

================================================================================
## ЭТАП 1. ОСНОВА ПРОЕКТА И ДОКУМЕНТАЦИЯ
================================================================================

### Цель этапа
Создать репозиторий, понятную структуру папок и первичную документацию.
После этого этапа любой человек или ИИ-ассистент должен открыть проект
и сразу понять: что это, как запустить, где что лежит.

### Конечный результат
Репозиторий с базовой структурой папок, README, pyproject.toml, .gitignore,
местом для кода, тестов, данных, скриптов и документации.
Никакого расчётного кода на этом этапе ещё нет.

### Инструкция для ИИ-ассистента
> Создай структуру папок согласно разделу «Структура проекта (эталон)»
> выше. Создай файлы README.md, pyproject.toml, .gitignore, CHANGELOG.md.
> Заполни README.md по шаблону из docs/00_project_overview.md.
> Не создавай расчётный код. Не создавай пустые файлы без причины.
> Целевая версия Python: 3.11+.

---

#### 1.1 Репозиторий и корневая структура

- [ ] Создать репозиторий проекта (Git init или GitHub repo).
- [ ] Создать корневую папку `iva/`.
- [ ] Создать папки верхнего уровня: `ui/`, `app/`, `core/`, `infrastructure/`, `tests/`, `scripts/`, `docs/`, `config/`, `data/`.
- [ ] Создать папку `data/examples/` — для демонстрационных файлов.
- [ ] Создать папку `data/synthetic/` — для сгенерированных тестовых данных.
- [ ] Создать файл `main.py` — точка входа в приложение (пока пустая заглушка).

#### 1.2 Файл README.md

- [ ] Создать `README.md` в корне проекта.
- [ ] Написать раздел «Что такое IVA» (2–3 предложения, суть задачи).
- [ ] Написать раздел «Требования» (Python 3.11+, Windows 11, 4 ГБ RAM).
- [ ] Написать раздел «Установка зависимостей» (`pip install -r requirements.txt`).
- [ ] Написать раздел «Запуск приложения» (`python main.py`).
- [ ] Написать раздел «Запуск тестов» (`pytest`).
- [ ] Написать раздел «Структура проекта» (краткое описание каждой папки).
- [ ] Добавить ссылку на `docs/00_project_overview.md` для подробностей.

#### 1.3 Конфигурация Python-проекта

- [ ] Создать `pyproject.toml`.
- [ ] Указать `name = "industrial-vibration-analyzer"`.
- [ ] Указать `version = "0.1.0"`.
- [ ] Указать `requires-python = ">=3.11"`.
- [ ] Добавить секцию `[tool.black]` с `line-length = 100`.
- [ ] Добавить секцию `[tool.ruff]` с базовыми правилами.
- [ ] Добавить секцию `[tool.mypy]` с `strict = false` (строгость нарастает постепенно).
- [ ] Добавить секцию `[tool.pytest.ini_options]` с `testpaths = ["tests"]`.
- [ ] Создать `requirements.txt` с зависимостями (см. `docs/06_technology_stack.md`).
- [ ] Создать `requirements-dev.txt` с инструментами разработки (black, ruff, mypy, pytest, pytest-cov).

#### 1.4 .gitignore

- [ ] Создать `.gitignore`.
- [ ] Добавить: виртуальные окружения (`venv/`, `.venv/`, `env/`).
- [ ] Добавить: кэши Python (`__pycache__/`, `*.pyc`, `*.pyo`).
- [ ] Добавить: директории сборки (`build/`, `dist/`, `*.egg-info/`).
- [ ] Добавить: временные файлы и журналы (`*.log`, `*.tmp`).
- [ ] Добавить: директории результатов (`data/results/`, `reports/`).
- [ ] Добавить: IDE-файлы (`.idea/`, `.vscode/`).

#### 1.5 Документация

- [ ] Скопировать или создать папку `docs/` с документами 00–22 из пакета документации.
- [ ] Создать `CHANGELOG.md` с первой записью: `## [0.1.0] — начало проекта`.
- [ ] Создать `CONTRIBUTING.md` с одной строкой: `Читайте docs/19_code_style_and_contribution.md`.
- [ ] Создать `config/defaults.toml` с заглушками для настроек по умолчанию.

#### 1.6 Файл версии

- [ ] Создать `iva/__version__.py` с одной строкой: `__version__ = "0.1.0"`.
  > Это единственное место, где хранится версия. Все остальные файлы читают её отсюда.

#### Критерии завершения этапа 1

- [ ] Репозиторий создан, первый коммит сделан.
- [ ] Папки созданы согласно эталонной структуре.
- [ ] README.md понятен без устного объяснения.
- [ ] `pyproject.toml` и `requirements.txt` созданы.
- [ ] `.gitignore` создан.
- [ ] Документация добавлена в `docs/`.

---

================================================================================
## ЭТАП 2. АРХИТЕКТУРА И МОДЕЛИ ДАННЫХ
================================================================================

### Цель этапа
Создать все модели данных в `core/models/` и иерархию исключений.
Это скелет, через который проходят данные на всех последующих этапах.

### Конечный результат
Python-пакет `iva/` с папкой `core/models/`, содержащей все `@dataclass`-модели
из `docs/10_data_models_and_schemas.md`. Расчётного кода ещё нет — только
структуры данных и исключения.

### Инструкция для ИИ-ассистента
> Прочитай docs/10_data_models_and_schemas.md полностью.
> Создай файлы в core/models/ согласно схемам из документа.
> Используй @dataclass(frozen=True) для неизменяемых моделей.
> Все поля аннотируй типами. Не импортируй ничего из ui/ или app/.
> Затем создай infrastructure/logging/app_logger.py и core/models/__init__.py.

---

#### 2.1 Python-пакеты

- [ ] Создать `iva/__init__.py` — делает `iva` Python-пакетом.
- [ ] Создать `iva/core/__init__.py`.
- [ ] Создать `iva/core/models/__init__.py` — экспортирует все модели.
- [ ] Создать `iva/infrastructure/__init__.py`.
- [ ] Создать `iva/app/__init__.py`.
- [ ] Создать `iva/ui/__init__.py`.

#### 2.2 Перечисления (Enums)

Создать `core/models/enums.py` со следующими перечислениями:

- [ ] `SignalRole` — роли сигнала: `ACCELERATION_X`, `ACCELERATION_Y`, `ACCELERATION_Z`, `PRESSURE`, `VELOCITY`.
- [ ] `WindowType` — типы окон: `HANN`, `HAMMING`, `RECTANGULAR`.
- [ ] `PeakInterpretation` — классификация пика: `VORTEX_SHEDDING`, `HARMONIC`, `STRUCTURAL`, `UNKNOWN`.
- [ ] `GeometryType` — конфигурация: `SINGLE_CYLINDER`, `TANDEM`.
- [ ] `RiskLevel` — уровень риска: `SAFE`, `WATCH`, `CRITICAL`.

#### 2.3 Модели входных данных

Создать `core/models/signal_data.py`:

- [ ] Класс `RawFileData` (frozen dataclass) — результат чтения файла «как есть».
  Поля: `file_path`, `file_format`, `column_names`, `column_dtypes`, `row_count`, `file_size_bytes`, `data`, `read_timestamp`.
- [ ] Класс `ColumnRoleAssignment` (frozen dataclass) — назначение ролей колонкам.
  Поля: `time_column`, `primary_signal_column`, `signal_role`, `additional_columns`, `sampling_rate_hz`, `sensor_conversion_factor`.
- [ ] Класс `ValidatedSignalData` (frozen dataclass) — данные после проверки качества.
  Поля: `time_array`, `signal_array`, `sampling_rate_hz`, `duration_seconds`, `sample_count`, `signal_role`, `physical_unit`, `missing_fraction`, `outlier_fraction`, `warnings`.
- [ ] Класс `ProcessedSignalData` (frozen dataclass) — данные после предобработки.
  Поля: `time_array`, `signal_cleaned`, `signal_filtered`, `preprocessing_log`, `applied_settings`.

#### 2.4 Модели настроек

Создать `core/models/settings.py`:

- [ ] Класс `PreprocessingSettings` — настройки предобработки. Все поля со значениями по умолчанию из `docs/10_data_models_and_schemas.md`.
- [ ] Класс `SpectralSettings` — настройки спектрального анализа. Все поля со значениями по умолчанию.
- [ ] Класс `AnalysisSettings` — объединяет `PreprocessingSettings`, `SpectralSettings` и `FlowParameters`.

#### 2.5 Модели физических параметров

Создать `core/models/flow_parameters.py`:

- [ ] Класс `FlowParameters` (frozen dataclass) — параметры течения и геометрии.
  Поля: `cylinder_diameter_m`, `mean_flow_velocity_ms`, `fluid_density_kgm3`, `dynamic_viscosity_pas`, `natural_frequency_hz`, `damping_ratio`, `cylinder_spacing_m`, `geometry_type`.
  > Все поля со значениями `None` по умолчанию, кроме обязательных.

#### 2.6 Модели результатов

Создать `core/models/analysis_result.py`:

- [ ] Класс `SpectralPeak` (frozen dataclass) — один пик в спектре.
  Поля: `frequency_hz`, `amplitude`, `width_hz_3db`, `interpretation`, `confidence`.
- [ ] Класс `SpectrumResult` (frozen dataclass) — результат спектрального анализа.
  Поля: `frequencies`, `psd_values`, `dominant_peak`, `all_peaks`, `rms_total`, `rms_in_band`, `rms_trend`, `applied_settings`.
- [ ] Класс `PhysicsResult` (frozen dataclass) — физические коэффициенты.
  Поля: `reynolds_number`, `strouhal_number`, `calculated_shedding_frequency_hz`, `velocity_ratio`, `frequency_ratio`, `kinematic_viscosity_m2s`.
- [ ] Класс `RiskAssessment` (frozen dataclass) — оценка риска резонанса.
  Поля: `risk_level`, `dominant_frequency_deviation`, `recommendation_text`, `contributing_factors`.
- [ ] Класс `ValidationResult` (frozen dataclass) — сравнение эксперимент vs CFD.
  Поля: `coordinate_array`, `experiment_array`, `cfd_array`, `rmse`, `mae`, `mape`, `pearson_r`, `is_mape_valid`.
- [ ] Класс `AnalysisResult` (frozen dataclass) — главный объект сеанса.
  Поля: `session_id`, `completed_at`, `source_file_path`, `source_file_md5`, `validated_data`, `processed_data`, `spectrum`, `physics`, `risk`, `validation`, `warnings`.

#### 2.7 Иерархия исключений

Создать `core/models/exceptions.py`:

- [ ] Базовый класс `IVAError(Exception)` с полями `user_message`, `technical_details`, `recovery_hint`.
- [ ] `FileReadError(IVAError)` — ошибка чтения файла.
- [ ] `FileNotFoundError(FileReadError)` — файл не найден.
- [ ] `UnsupportedFormatError(FileReadError)` — формат не поддерживается.
- [ ] `FileCorruptedError(FileReadError)` — файл повреждён.
- [ ] `ValidationError(IVAError)` — данные не прошли проверку.
- [ ] `NonMonotonicTimeAxisError(ValidationError)` — немонотонная временна́я ось.
- [ ] `EmptySignalError(ValidationError)` — сигнал пустой или нулевой.
- [ ] `InsufficientDataError(ValidationError)` — слишком мало данных.
- [ ] `ProcessingError(IVAError)` — ошибка расчёта.
- [ ] `FilterConfigurationError(ProcessingError)` — неверные параметры фильтра.
- [ ] `PhysicsInputError(IVAError)` — недопустимые физические параметры.
- [ ] `ExportError(IVAError)` — ошибка при сохранении файла.

#### 2.8 Тесты моделей

- [ ] Создать `tests/unit/core/models/test_enums.py` — проверить, что все перечисления содержат ожидаемые значения.
- [ ] Создать `tests/unit/core/models/test_settings.py` — проверить значения по умолчанию.
- [ ] Создать `tests/unit/core/models/test_exceptions.py` — проверить иерархию и поля исключений.
- [ ] Убедиться, что ни одна модель не импортирует из `ui/`, `app/` или `infrastructure/`.
- [ ] Запустить `mypy core/models/` — убедиться, что аннотации типов корректны.

#### Критерии завершения этапа 2

- [ ] Все модели созданы и аннотированы типами.
- [ ] Иерархия исключений создана.
- [ ] Ни одна модель не зависит от PySide6.
- [ ] Тесты моделей проходят.

---

================================================================================
## ЭТАП 3. ИНФРАСТРУКТУРА: ЧТЕНИЕ ФАЙЛОВ И СИНТЕТИЧЕСКИЕ ДАННЫЕ
================================================================================

### Цель этапа
Научить приложение читать файлы и иметь тестовые данные для разработки.
После этого этапа можно загрузить CSV, проверить его качество и работать
с синтетическими сигналами без реальных данных с датчиков.

### Конечный результат
Модули в `infrastructure/readers/` читают CSV, Parquet и Excel.
Скрипт генерирует синтетические сигналы. Все операции покрыты тестами.

### Инструкция для ИИ-ассистента
> Прочитай docs/04_input_data_specification.md.
> Создай три ридера в infrastructure/readers/.
> Каждый ридер принимает путь к файлу и возвращает объект RawFileData.
> Все исключения Python оборачивай в IVAError-подклассы.
> Не добавляй GUI-код. Не добавляй расчётную логику.

---

#### 3.1 Журналирование

Создать `infrastructure/logging/app_logger.py`:

- [ ] Реализовать функцию `get_logger(name: str) -> logging.Logger`.
- [ ] Настроить запись в файл `%USERPROFILE%/Documents/IVA/logs/iva_{дата}.log`.
- [ ] Формат строки журнала: `%(asctime)s.%(msecs)03d  %(levelname)-8s  %(name)s  %(message)s`.
- [ ] Ротация по дате: новый файл каждый день.
- [ ] Удалять файлы старше 30 дней при запуске.

#### 3.2 Ридер CSV

Создать `infrastructure/readers/csv_reader.py`:

- [ ] Функция `read_csv(file_path: str) -> RawFileData`.
- [ ] Автоматически определять разделитель (запятая, точка с запятой, табуляция).
- [ ] Автоматически определять кодировку (UTF-8, CP1251, Latin-1).
- [ ] Автоматически определять, есть ли строка с заголовками.
- [ ] Пропускать строки-комментарии, начинающиеся с `#`.
- [ ] При успешном чтении: логировать `INFO` с именем файла и количеством строк.
- [ ] Все исключения Python (`OSError`, `UnicodeDecodeError`, и т.д.) оборачивать в `FileReadError`.
- [ ] При `FileNotFoundError` Python — поднимать `FileNotFoundError(IVA)` с понятным `user_message`.

#### 3.3 Ридер Parquet

Создать `infrastructure/readers/parquet_reader.py`:

- [ ] Функция `read_parquet(file_path: str) -> RawFileData`.
- [ ] Использовать `pyarrow` или `pandas` для чтения.
- [ ] Все исключения оборачивать в `FileReadError`.
- [ ] При размере файла > 100 МБ логировать предупреждение `WARNING`.

#### 3.4 Ридер Excel

Создать `infrastructure/readers/excel_reader.py`:

- [ ] Функция `read_excel(file_path: str, sheet_name: str | None = None) -> RawFileData`.
- [ ] Читать через `openpyxl` в режиме `read_only=True` (отключает макросы).
- [ ] Если файл содержит несколько листов — читать первый лист по умолчанию.
- [ ] Все исключения оборачивать в `FileReadError`.
  > Режим read_only обязателен по соображениям безопасности (docs/18_security_and_data_privacy.md).

#### 3.5 Фабрика ридеров

Создать `infrastructure/readers/__init__.py`:

- [ ] Функция `read_file(file_path: str) -> RawFileData`.
- [ ] Определять формат по расширению файла (`.csv` → csv_reader, `.parquet` → parquet_reader, `.xlsx` → excel_reader).
- [ ] При неизвестном расширении поднимать `UnsupportedFormatError`.

#### 3.6 Валидация данных

Создать `infrastructure/validators/data_quality_checker.py`:

- [ ] Функция `check_data_quality(raw_data: RawFileData, assignment: ColumnRoleAssignment) -> ValidatedSignalData`.
- [ ] Проверять: временна́я ось монотонно возрастает.
- [ ] Проверять: интервал дискретизации постоянен (допуск 0,01%).
- [ ] Вычислять: долю пропущенных значений.
- [ ] Оценивать: долю выбросов по правилу 4σ.
- [ ] Проверять: длительность записи ≥ 5 секунд.
- [ ] При критических ошибках поднимать `ValidationError`.
- [ ] При некритических проблемах добавлять `ValidationWarning` в список.
- [ ] Логировать каждую проверку на уровне `DEBUG`.

#### 3.7 Синтетические данные

Создать `scripts/generate_synthetic_data.py`:

- [ ] Функция `generate_clean_sine(frequency_hz, duration_s, sampling_rate_hz, amplitude)` — чистая синусоида.
- [ ] Функция `generate_noisy_sine(frequency_hz, snr_db, ...)` — синусоида с гауссовым шумом.
- [ ] Функция `generate_with_harmonics(fundamental_hz, n_harmonics, ...)` — основной тон + гармоники.
- [ ] Функция `generate_with_outliers(base_signal, n_outliers, ...)` — сигнал с несколькими выбросами.
- [ ] Функция `generate_with_gaps(base_signal, gap_fraction, ...)` — сигнал с пропусками (NaN).
- [ ] Функция `generate_risk_scenario(shedding_hz, natural_hz, ...)` — сигнал близко к резонансу.
- [ ] При запуске скрипта сохранять файлы в `data/synthetic/`.
- [ ] Создать `data/examples/` с 3–4 готовыми демонстрационными файлами.
- [ ] Добавить `data/examples/README.md` с описанием каждого файла.

#### 3.8 Тесты

- [ ] Создать `tests/unit/infrastructure/test_csv_reader.py`.
  - [ ] Тест: корректный CSV читается без ошибок.
  - [ ] Тест: CSV без временно́й колонки → понятное предупреждение.
  - [ ] Тест: CSV с нечисловым сигналом → `ValidationError`.
  - [ ] Тест: несуществующий файл → `FileNotFoundError(IVA)`.
- [ ] Создать `tests/unit/infrastructure/test_data_quality_checker.py`.
  - [ ] Тест: немонотонная временна́я ось → `NonMonotonicTimeAxisError`.
  - [ ] Тест: более 30% пропусков → предупреждение в списке.
  - [ ] Тест: нулевой сигнал → `EmptySignalError`.
  - [ ] Тест: запись < 5 секунд → `InsufficientDataError`.
- [ ] Создать `tests/unit/scripts/test_generate_synthetic_data.py`.
  - [ ] Тест: генератор создаёт массив правильной длины.
  - [ ] Тест: частота дискретизации соответствует заданной.

#### Критерии завершения этапа 3

- [ ] CSV, Parquet и Excel читаются без ошибок на корректных файлах.
- [ ] Некорректные файлы дают понятные исключения `IVAError`.
- [ ] Валидатор находит пропуски, выбросы, немонотонную ось.
- [ ] Синтетические данные генерируются.
- [ ] Демонстрационные файлы добавлены в `data/examples/`.
- [ ] Все тесты проходят.

---

================================================================================
## ЭТАП 4. ПРЕДОБРАБОТКА СИГНАЛА
================================================================================

### Цель этапа
Реализовать расчётные алгоритмы предобработки сигнала в `core/signal/`.
После этого этапа сырой сигнал можно очистить, отфильтровать
и подготовить к спектральному анализу.

### Конечный результат
Три модуля в `core/signal/` реализуют полный конвейер предобработки.
Все алгоритмы покрыты тестами с аналитическими решениями.

### Инструкция для ИИ-ассистента
> Прочитай docs/11_algorithms.md, алгоритмы 1–4.
> Прочитай docs/09_processing_pipeline.md, шаг 3.
> Порядок операций в конвейере фиксирован: среднее → выбросы → пропуски → фильтр.
> Нарушать этот порядок нельзя (объяснение — в docs/09_processing_pipeline.md).
> Все функции принимают np.ndarray и возвращают np.ndarray.

---

#### 4.1 Удаление постоянной составляющей

Создать `core/signal/preprocessor.py`:

- [ ] Функция `remove_mean(signal: np.ndarray) -> np.ndarray`.
  - Вычитает `np.mean(signal)` из каждого элемента.
  - Логирует `INFO`: «Постоянная составляющая удалена, смещение было {:.4f}».
  - Сложность O(n), без Python-циклов.

#### 4.2 Заполнение пропусков

В `core/signal/preprocessor.py` добавить:

- [ ] Функция `fill_gaps(signal, time_array, max_gap_seconds, sampling_rate_hz) -> np.ndarray`.
  - Находить непрерывные промежутки NaN.
  - Промежутки ≤ `max_gap_seconds`: линейная интерполяция (scipy.interpolate).
  - Промежутки > `max_gap_seconds`: заполнять нулями.
  - Логировать `WARNING`, если суммарная доля заполненных > 5%.

#### 4.3 Обнаружение и замена выбросов

Создать `core/signal/outlier_detector.py`:

- [ ] Функция `detect_outliers(signal, window_samples, threshold_sigma) -> np.ndarray` (булев массив).
  - Алгоритм из docs/11_algorithms.md (алгоритм 2): скользящая медиана + MAD.
  - Коэффициент MAD: 1.4826.
  - Без Python-циклов — использовать векторизованные операции NumPy.
- [ ] Функция `replace_outliers(signal, outlier_mask) -> np.ndarray`.
  - Заменять выбросы линейной интерполяцией между соседними «чистыми» точками.
  - Логировать `INFO` с количеством заменённых точек.

#### 4.4 Цифровой фильтр Баттерворта

Создать `core/signal/filter.py`:

- [ ] Функция `apply_bandpass_filter(signal, sampling_rate_hz, low_hz, high_hz, order) -> np.ndarray`.
  - Использовать `scipy.signal.butter` + `scipy.signal.filtfilt`.
  - `filtfilt` обязателен (нулевой фазовый сдвиг — см. docs/11_algorithms.md алгоритм 4).
  - Проверять: `0 < low_hz < high_hz < sampling_rate_hz / 2`, иначе `FilterConfigurationError`.
  - Логировать `DEBUG` параметры фильтра.
- [ ] Функция `apply_lowpass_filter(signal, sampling_rate_hz, cutoff_hz, order) -> np.ndarray`.
- [ ] Функция `apply_highpass_filter(signal, sampling_rate_hz, cutoff_hz, order) -> np.ndarray`.

#### 4.5 Главная функция предобработки

В `core/signal/preprocessor.py` добавить:

- [ ] Функция `preprocess_signal(data: ValidatedSignalData, settings: PreprocessingSettings) -> ProcessedSignalData`.
  - Вызывать операции в фиксированном порядке: remove_mean → detect_outliers/replace → fill_gaps → apply_bandpass_filter.
  - Каждую применённую операцию добавлять в `preprocessing_log`.
  - Возвращать `ProcessedSignalData` с обеими версиями сигнала.

#### 4.6 Тесты

- [ ] Создать `tests/unit/core/signal/test_preprocessor.py`.
  - [ ] Тест: `remove_mean` — после применения `|np.mean(result)| < 1e-10`.
  - [ ] Тест: `fill_gaps` — пропуски длиной ≤ порога заполнены, нет NaN.
  - [ ] Тест: `fill_gaps` — пропуски длиннее порога заменены нулями.
- [ ] Создать `tests/unit/core/signal/test_outlier_detector.py`.
  - [ ] Тест: известные выбросы обнаруживаются.
  - [ ] Тест: чистый сигнал не содержит ложных выбросов.
  - [ ] Тест: чистый сигнал с нулевой амплитудой не вызывает деления на ноль.
- [ ] Создать `tests/unit/core/signal/test_filter.py`.
  - [ ] Тест: синусоида вне полосы пропускания подавляется до < 1% амплитуды.
  - [ ] Тест: синусоида в полосе пропускания проходит с амплитудой > 90%.
  - [ ] Тест: `low_hz > nyquist` → `FilterConfigurationError`.
  - [ ] Тест: `low_hz >= high_hz` → `FilterConfigurationError`.
  - [ ] Тест: применение `filtfilt` не сдвигает фазу (RMS разности < 0.01).

#### Критерии завершения этапа 4

- [ ] Все четыре операции предобработки реализованы.
- [ ] Порядок операций в конвейере соблюдён.
- [ ] Нет Python-циклов в расчётных функциях (только NumPy/SciPy).
- [ ] Все тесты проходят, включая граничные случаи.

---

================================================================================
## ЭТАП 5. СПЕКТРАЛЬНЫЙ АНАЛИЗ
================================================================================

### Цель этапа
Реализовать вычисление спектров, поиск пиков и расчёт RMS в `core/spectrum/`.
Это центральная расчётная часть проекта.

### Конечный результат
Три модуля в `core/spectrum/` обеспечивают полный спектральный анализ.
Синтетический сигнал с известной частотой 40 Гц даёт пик в диапазоне 39–41 Гц.

### Инструкция для ИИ-ассистента
> Прочитай docs/11_algorithms.md, алгоритмы 5–8.
> Прочитай docs/03_scientific_methodology.md, раздел «Методы обработки сигналов».
> Функции принимают np.ndarray и возвращают typed dataclasses из core/models/.
> Визуализацию не реализовывать — это задача ui/.

---

#### 5.1 Вычисление спектральной плотности мощности

Создать `core/spectrum/psd_calculator.py`:

- [ ] Функция `calculate_psd(signal, sampling_rate_hz, settings: SpectralSettings) -> tuple[np.ndarray, np.ndarray]`.
  - Использовать `scipy.signal.welch`.
  - Параметр `scaling='density'` (единицы: [физ. ед.]²/Гц).
  - Вычислять и логировать `DEBUG`: частотное разрешение `Δf = fs / nperseg`.
  - Возвращать `(frequencies, psd_values)`.
  - При длине сигнала < `nperseg` поднимать `InsufficientDataError`.

#### 5.2 Поиск пиков

Создать `core/spectrum/peak_finder.py`:

- [ ] Функция `find_peaks(frequencies, psd_values, settings: SpectralSettings) -> list[SpectralPeak]`.
  - Алгоритм из docs/11_algorithms.md (алгоритм 6).
  - Переводить PSD в логарифмический масштаб (дБ) для поиска порога.
  - Фильтровать пики по минимальной ширине `settings.peak_min_width_hz`.
  - Вычислять ширину на уровне -3 дБ для каждого пика.
  - Возвращать список `SpectralPeak`, отсортированный по амплитуде (по убыванию).
- [ ] Функция `interpret_peaks(peaks, physics_result) -> list[SpectralPeak]`.
  - Алгоритм из docs/11_algorithms.md (алгоритм 7).
  - Классифицировать каждый пик: `VORTEX_SHEDDING` / `HARMONIC` / `STRUCTURAL` / `UNKNOWN`.
  - Если `physics_result is None` — все пики классифицировать как `UNKNOWN`.

#### 5.3 Расчёт RMS

Создать `core/spectrum/rms_calculator.py`:

- [ ] Функция `calculate_total_rms(signal: np.ndarray) -> float`.
  - Формула: `sqrt(mean(signal**2))`. Без Python-циклов.
- [ ] Функция `calculate_band_rms(frequencies, psd_values, low_hz, high_hz) -> float`.
  - Интегрировать PSD в заданной полосе (теорема Парсеваля).
  - Взять корень из результата.
- [ ] Функция `calculate_rms_trend(signal, sampling_rate_hz, window_seconds) -> np.ndarray`.
  - Алгоритм из docs/11_algorithms.md (алгоритм 8).
  - Использовать `np.convolve` — без Python-цикла.

#### 5.4 Тесты

- [ ] Создать `tests/unit/core/spectrum/test_psd_calculator.py`.
  - [ ] Тест: синусоида 40 Гц → доминирующий пик в диапазоне 39.0–41.0 Гц.
  - [ ] Тест: частотное разрешение `Δf = fs / nperseg` вычисляется правильно.
  - [ ] Тест: сигнал короче `nperseg` → `InsufficientDataError`.
- [ ] Создать `tests/unit/core/spectrum/test_peak_finder.py`.
  - [ ] Тест: синусоида с двумя частотами → найдено два пика.
  - [ ] Тест: чистый шум → пики ниже порога, список пуст или минимален.
  - [ ] Тест: сигнал с гармониками 40 Гц → найдены пики на 80 Гц и 120 Гц, помечены как `HARMONIC`.
- [ ] Создать `tests/unit/core/spectrum/test_rms_calculator.py`.
  - [ ] Тест: RMS синусоиды с амплитудой A = `A / sqrt(2)` (аналитическое решение).
  - [ ] Тест: скользящий RMS имеет правильную длину массива.

#### Критерии завершения этапа 5

- [ ] PSD методом Уэлча вычисляется корректно.
- [ ] Синтетический сигнал 40 Гц: доминирующий пик в диапазоне 39–41 Гц.
- [ ] Гармоники обнаруживаются и классифицируются.
- [ ] RMS вычисляется по аналитическому решению с погрешностью < 0.1%.
- [ ] Все тесты проходят.

---

================================================================================
## ЭТАП 6. ФИЗИЧЕСКИЕ РАСЧЁТЫ И ОЦЕНКА РИСКА
================================================================================

### Цель этапа
Реализовать физические расчёты в `core/physics/` и связать их
с результатами спектрального анализа через оценку риска резонанса.

### Конечный результат
Приложение рассчитывает Re, St, fs, Vr, классифицирует уровень риска
и формирует текстовую рекомендацию инженеру.

### Инструкция для ИИ-ассистента
> Прочитай docs/03_scientific_methodology.md, раздел «Безразмерные критерии».
> Прочитай docs/11_algorithms.md, алгоритмы 9–11.
> Все функции принимают физические параметры с единицами СИ (м, кг, с, Па).
> Проверяй входные данные в начале каждой функции.

---

#### 6.1 Расчёт числа Рейнольдса

Создать `core/physics/reynolds_calculator.py`:

- [ ] Функция `calculate(V, D, rho, mu) -> float`.
  - Формула: `Re = rho * V * D / mu`.
  - Кинематическую вязкость вычислять как `nu = mu / rho`.
  - Проверять: `D > 0`, `rho > 0`, `mu > 0`, иначе `PhysicsInputError`.
  - Логировать `INFO`: `Re = {:.2e}`.

#### 6.2 Расчёт числа Струхаля

Создать `core/physics/strouhal_calculator.py`:

- [ ] Функция `get_strouhal_number(re, geometry_type, spacing_ratio=None) -> float`.
  - Алгоритм из docs/11_algorithms.md (алгоритм 9).
  - Для `SINGLE_CYLINDER`: кусочно-линейная интерполяция по таблице Blevins.
  - Для `TANDEM`: двумерная интерполяция по (Re, L/D) из экспериментальных данных.
  - Таблицы хранить в `config/strouhal_tables.toml`.

#### 6.3 Расчёт частоты срыва вихрей

Создать `core/physics/vortex_frequency.py`:

- [ ] Функция `calculate_shedding_frequency(St, V, D) -> float`.
  - Формула: `fs = St * V / D`.
  - Проверять: `D > 0`, `V > 0`.
- [ ] Функция `calculate_velocity_ratio(V, fn, D) -> float | None`.
  - Формула: `Vr = V / (fn * D)`.
  - Если `fn is None` → возвращать `None`.
- [ ] Функция `calculate_frequency_ratio(fs, fn) -> float | None`.
  - Если `fn is None` → возвращать `None`.

#### 6.4 Оценка риска резонанса

Создать `core/physics/lock_in_risk.py`:

- [ ] Функция `assess_risk(physics_result: PhysicsResult, spectrum_result: SpectrumResult) -> RiskAssessment`.
  - Алгоритм из docs/11_algorithms.md (алгоритм 10).
  - Если `fn` не задана → вернуть `RiskAssessment(risk_level=SAFE, ...)` с пометкой «fn не задана».
  - Вычислить `deviation = |fs − fn| / fn`.
  - Классифицировать: deviation > 0.30 → SAFE; 0.10–0.30 → WATCH; ≤ 0.10 → CRITICAL.
  - Дополнительная проверка амплитуды пика: если пик мал → понизить уровень на один шаг.
  - Добавить в `contributing_factors` перечень причин классификации.
  - Сгенерировать `recommendation_text` на русском языке для каждого уровня.

#### 6.5 Метрики сравнения с CFD

Создать `core/validation/error_metrics.py`:

- [ ] Функция `rmse(experiment, cfd) -> float`.
- [ ] Функция `mae(experiment, cfd) -> float`.
- [ ] Функция `mape(experiment, cfd) -> float | None`. Вернуть `None` если знаменатель ≈ 0.
- [ ] Функция `pearson_r(experiment, cfd) -> float`.
- [ ] Константа `MAPE_DENOMINATOR_THRESHOLD = 1e-6`.

Создать `core/validation/experiment_vs_cfd.py`:

- [ ] Функция `compare(experiment, cfd_data) -> ValidationResult`.
  - Интерполировать оба профиля на общую сетку координат.
  - Вызвать все метрики из `error_metrics.py`.
  - Вернуть `ValidationResult`.

#### 6.6 Тесты

- [ ] Создать `tests/unit/core/physics/test_reynolds_calculator.py`.
  - [ ] Тест: Re(V=2.0, D=0.012, ρ=998, μ=1.002e-3) ≈ 23904 (погрешность < 0.1%).
  - [ ] Тест: D=0 → `PhysicsInputError`.
- [ ] Создать `tests/unit/core/physics/test_vortex_frequency.py`.
  - [ ] Тест: fs(St=0.21, V=2.0, D=0.012) = 35.0 Гц.
- [ ] Создать `tests/unit/core/physics/test_lock_in_risk.py`.
  - [ ] Тест: fs близка к fn (deviation < 0.10) → `CRITICAL`.
  - [ ] Тест: fn не задана → `SAFE` с соответствующим сообщением.
  - [ ] Тест: deviation > 0.30 → `SAFE`.
- [ ] Создать `tests/unit/core/validation/test_error_metrics.py`.
  - [ ] Тест: идентичные массивы → RMSE=0, MAE=0, r=1.
  - [ ] Тест: нули в знаменателе MAPE → функция возвращает `None`, а не исключение.

#### Критерии завершения этапа 6

- [ ] Re, St, fs, Vr вычисляются корректно.
- [ ] Риск классифицируется по трём уровням.
- [ ] Рекомендация генерируется на русском языке.
- [ ] Метрики RMSE, MAE, MAPE, r работают корректно.
- [ ] Все тесты проходят.

---

================================================================================
## ЭТАП 7. КООРДИНИРУЮЩИЙ СЛОЙ И CLI
================================================================================

### Цель этапа
Собрать расчётное ядро в единый конвейер в `app/`, добавить CLI-команду.
После этого этапа полный анализ запускается одной командой без GUI.

### Конечный результат
`app/analysis_runner.py` координирует все шаги. CLI-команда принимает файл
и конфигурацию, возвращает результат в JSON, CSV и HTML.

### Инструкция для ИИ-ассистента
> Прочитай docs/09_processing_pipeline.md полностью — это главный ориентир.
> Создай app/workflow_coordinator.py, app/analysis_runner.py и CLI.
> Не трогай core/ — только координация.
> CLI не должен импортировать ничего из ui/.

---

#### 7.1 Сессия анализа

Создать `app/analysis_session.py`:

- [ ] Класс `AnalysisSession` — хранит текущее состояние сеанса.
  Поля: `raw_data`, `role_assignment`, `settings`, `result`.
- [ ] Метод `is_ready_for_analysis() -> bool` — проверяет, что данные загружены и роли назначены.
- [ ] Метод `clear()` — сбрасывает все данные сеанса.
  > Это единственное место для хранения состояния. Нигде больше.

#### 7.2 Координатор рабочего процесса

Создать `app/workflow_coordinator.py`:

- [ ] Функция `run_pipeline(session: AnalysisSession) -> AnalysisResult`.
  - Шаг 1: вызвать `infrastructure.readers.read_file()`.
  - Шаг 2: вызвать `infrastructure.validators.check_data_quality()`.
  - Шаг 3: вызвать `core.signal.preprocessor.preprocess_signal()`.
  - Шаг 4: вызвать `core.spectrum.psd_calculator.calculate_psd()` + `peak_finder.find_peaks()` + `rms_calculator`.
  - Шаг 5: если `settings.flow_parameters` задан → вызвать физические расчёты.
  - Шаг 6: вызвать `lock_in_risk.assess_risk()`.
  - Шаг 7: собрать `AnalysisResult`.
  - Логировать время каждого шага на уровне `INFO`.
  - Любое исключение `IVAError` перехватывать, логировать `ERROR` и пробрасывать выше.

#### 7.3 Асинхронный запуск (для будущего GUI)

Создать `app/analysis_runner.py`:

- [ ] Класс `AnalysisRunner` — обёртка над `workflow_coordinator` для запуска в фоновом потоке.
  > На этапе 7 реализовать как простой синхронный вызов. В этапе 8 — обернуть в QThread.

#### 7.4 Менеджер настроек

Создать `app/settings_manager.py`:

- [ ] Читать и сохранять `AnalysisSettings` из/в `config/defaults.toml`.
- [ ] Метод `load_defaults() -> AnalysisSettings`.
- [ ] Метод `save_settings(settings: AnalysisSettings) -> None`.

#### 7.5 Экспортёры результатов

Создать `infrastructure/writers/csv_export_writer.py`:

- [ ] Функция `export_spectrum_csv(result: AnalysisResult, output_path: str)`.
- [ ] Функция `export_signal_csv(result: AnalysisResult, output_path: str)`.
- [ ] Функция `export_physics_summary_csv(result: AnalysisResult, output_path: str)`.

#### 7.6 CLI

Создать `iva/cli/main.py` и команду `analyze`:

- [ ] Аргументы: `--data` (путь к файлу), `--config` (путь к JSON-конфигу), `--output` (папка для результатов).
- [ ] При запуске: читать конфиг → запускать `run_pipeline()` → сохранять результаты → выводить сводку в консоль.
- [ ] Выводить в консоль: уровень риска, доминирующий пик, Re, St.
- [ ] Добавить в `README.md` пример вызова:
  ```
  python -m iva.cli.main analyze --data data/examples/normal.csv --config config/example.json --output reports/run_001
  ```
- [ ] CLI не импортирует ничего из `ui/`.

#### 7.7 Конфигурационный файл примера

Создать `config/example_config.json`:

- [ ] Включить: выбор сигнала, параметры фильтра, параметры спектра, физические параметры.
- [ ] Добавить комментарии к каждому полю (в формате `"_comment_field": "..."`).

#### 7.8 Тесты

- [ ] Создать `tests/integration/test_full_pipeline_clean_data.py`.
  - [ ] Тест: демонстрационный файл с чистым сигналом 40 Гц → доминирующий пик в диапазоне 39–41 Гц.
- [ ] Создать `tests/integration/test_pipeline_with_gaps.py`.
  - [ ] Тест: файл с пропусками → предупреждения в результате, анализ завершён.
- [ ] Создать `tests/integration/test_pipeline_invalid_file.py`.
  - [ ] Тест: несуществующий файл → `FileNotFoundError(IVA)`, не падает с трейсбэком Python.
- [ ] Создать `tests/integration/test_cli.py`.
  - [ ] Тест: CLI с демонстрационным файлом завершается с кодом 0.
  - [ ] Тест: CLI с несуществующим файлом завершается с кодом не 0.

#### Критерии завершения этапа 7

- [ ] `run_pipeline()` работает от начала до конца на демонстрационных данных.
- [ ] CLI-команда запускается и выводит результат.
- [ ] Результаты сохраняются в CSV и JSON.
- [ ] Интеграционные тесты проходят.
- [ ] CLI не зависит от PySide6.

---

================================================================================
## ЭТАП 8. DESKTOP-ИНТЕРФЕЙС PYSIDE6
================================================================================

### Цель этапа
Создать первое полноценное настольное приложение с 7 вкладками рабочего процесса.

### Конечный результат
Пользователь открывает приложение, перетаскивает файл, нажимает «Запустить анализ»,
видит результат. Интерфейс не зависает. Ошибки отображаются понятно.

### Инструкция для ИИ-ассистента
> Прочитай docs/08_ui_ux_specification.md полностью.
> Все цветовые токены — из ui/styles/theme.py, никаких жёстко заданных RGB.
> Расчёты в ui/ запрещены — только вызовы app/ и отображение AnalysisResult.
> QThread для фонового запуска анализа — обязателен.
> Порядок создания: theme.py → main_window.py → pages по одной.

---

#### 8.1 Цветовая тема

Создать `ui/styles/theme.py`:

- [ ] Определить все цветовые токены из `docs/08_ui_ux_specification.md`.
  Минимальный набор: `COLOR_BG`, `COLOR_SURFACE`, `COLOR_PANEL`, `COLOR_BORDER`,
  `COLOR_TEXT`, `COLOR_MUTED`, `COLOR_DIM`, `COLOR_ACCENT`, `COLOR_GOOD`, `COLOR_WARN`, `COLOR_BAD`.
- [ ] Определить токены типографики: размеры шрифтов, веса.
- [ ] Функция `apply_dark_theme(app: QApplication) -> None` — применяет тему через `QPalette`.
  > Использовать токены, а не прямые hex-значения в компонентах.

#### 8.2 Главное окно

Создать `ui/main_window.py`:

- [ ] Класс `MainWindow(QMainWindow)`.
- [ ] Создать `QStackedWidget` — центральная рабочая область.
- [ ] Создать боковую панель навигации (`QListWidget`) с 7 пунктами.
- [ ] Создать панель инструментов (`QToolBar`) с кнопками: «Открыть файл», «Запустить анализ», «Сохранить отчёт».
- [ ] Создать правую панель инспектора (`QDockWidget`), скрытую по умолчанию.
- [ ] Подключить сигнал навигации к переключению страниц.

#### 8.3 Фоновый запуск анализа

В `app/analysis_runner.py` добавить:

- [ ] Класс `AnalysisWorker(QRunnable)` — запускает `run_pipeline()` в пуле потоков Qt.
- [ ] Сигналы: `progress_updated(int)`, `analysis_completed(AnalysisResult)`, `error_occurred(IVAError)`.
  > `QRunnable` предпочтительнее `QThread` для разовых задач.
- [ ] `MainWindow` при нажатии «Запустить анализ»:
  - Блокировать кнопку.
  - Запустить `AnalysisWorker` через `QThreadPool`.
  - Показать прогресс-бар.
  - При сигнале `analysis_completed` → разблокировать кнопку, обновить страницы.
  - При сигнале `error_occurred` → показать баннер с ошибкой.

#### 8.4 Страницы

Создать в `ui/pages/`:

- [ ] `overview_page.py` — 4 карточки метрик (пик, RMS, fs, риск). Сводные графики.
- [ ] `import_page.py` — drag-and-drop зона. Таблица колонок. Форма назначения ролей.
- [ ] `signal_page.py` — два графика (исходный/фильтрованный). Панель настроек фильтра.
- [ ] `spectrum_page.py` — график PSD с отмеченными пиками. Таблица пиков. Настройки Уэлча.
- [ ] `physics_page.py` — форма ввода параметров течения. 4 метрики (Re, St, fn, зона риска).
- [ ] `profiles_page.py` — два графика профилей (эксперимент vs CFD). Кнопка загрузки CFD-файла.
- [ ] `report_page.py` — предпросмотр отчёта. Кнопки «PDF», «CSV». Чекбоксы разделов.
  > Каждая страница подписывается на сигнал `analysis_completed` и обновляет своё содержимое.

#### 8.5 Переиспользуемые виджеты

Создать в `ui/widgets/`:

- [ ] `chart_widget.py` — `FigureCanvasQTAgg` с методами `plot_signal()`, `plot_psd()`, `clear()`.
- [ ] `metric_card.py` — виджет с меткой, большим числом и единицей измерения.
- [ ] `parameter_form.py` — динамическая форма с числовыми полями и валидацией диапазонов.
- [ ] `log_panel.py` — виджет `QTextEdit` (только чтение) с автопрокруткой вниз.

#### 8.6 Обработка ошибок в интерфейсе

- [ ] Создать метод `show_error_banner(error: IVAError)` в `MainWindow`.
  - Отображать `error.user_message` в нижней части окна.
  - Кнопка «Подробнее» → показывать `error.technical_details` в диалоге.
  - Не использовать `QMessageBox` для некритических ошибок.
- [ ] Критические ошибки (неперехваченные) → аварийный дамп + `QMessageBox.critical()`.

#### 8.7 Горячие клавиши

- [ ] `Ctrl+O` → «Открыть файл».
- [ ] `F5` → «Запустить анализ».
- [ ] `Ctrl+S` → «Сохранить отчёт».
- [ ] `L` → свернуть/развернуть навигацию.
- [ ] `R` → показать/скрыть инспектор.

#### 8.8 Проверка приложения

- [ ] Запустить приложение вручную (`python main.py`).
- [ ] Убедиться: файл открывается, анализ запускается, результат отображается.
- [ ] Убедиться: интерфейс не зависает во время расчёта.
- [ ] Убедиться: некорректный файл показывает баннер, а не падает.
- [ ] Написать smoke-тест: `pytest tests/system/test_app_launches.py`.

#### Критерии завершения этапа 8

- [ ] Приложение запускается без ошибок.
- [ ] Все 7 страниц переключаются.
- [ ] Анализ запускается в фоне, интерфейс отзывчив.
- [ ] Результаты отображаются на всех страницах.
- [ ] Ошибки отображаются в виде баннера, не трейсбэка.

---

================================================================================
## ЭТАП 9. ГРАФИКИ, ОТЧЁТЫ, СЕССИИ И СРАВНЕНИЕ С CFD
================================================================================

### Цель этапа
Превратить приложение в полноценную инженерную рабочую станцию.

### Конечный результат
Интерактивные графики с зумом и экспортом. PDF-отчёт. Сохранение сессии.
Сравнение экспериментальных данных с CFD-расчётом.

### Инструкция для ИИ-ассистента
> Прочитай docs/05_output_data_specification.md — структура PDF-отчёта.
> Прочитай docs/08_ui_ux_specification.md — поведение графиков.
> PDF генерировать через ReportLab. Светлый фон в отчёте (не тёмный).
> Сессия сохраняется как JSON. Для сравнения CFD — отдельная кнопка в profiles_page.py.

---

#### 9.1 Интерактивные графики

В `ui/widgets/chart_widget.py`:

- [ ] Зум при прокрутке колесом мыши.
- [ ] Панорамирование при перетаскивании.
- [ ] Кнопка «Сбросить масштаб» (возврат к исходному виду).
- [ ] Кнопка «Сохранить как PNG» — сохранять в `data/results/`.
- [ ] При зуме на сигнале > 10 000 точек — перерасчёт децимации для видимой области.
- [ ] Отмечать пики на PSD-графике вертикальными линиями с подписью частоты.
- [ ] Скользящий RMS отображать на отдельной оси под основным графиком сигнала.

#### 9.2 PDF-отчёт

Создать `infrastructure/writers/pdf_report_writer.py`:

- [ ] Функция `generate_pdf_report(result: AnalysisResult, output_path: str) -> None`.
- [ ] Структура отчёта из `docs/05_output_data_specification.md`:
  - [ ] Титульная страница: название, файл, дата, версия.
  - [ ] Раздел 1: параметры анализа (таблица).
  - [ ] Раздел 2: качество данных (пропуски, выбросы).
  - [ ] Раздел 3: временна́я область (графики + статистика).
  - [ ] Раздел 4: спектральный анализ (PSD + таблица пиков).
  - [ ] Раздел 5: физические коэффициенты (Re, St, fs, Vr).
  - [ ] Раздел 6: сравнение с CFD (если есть `ValidationResult`).
  - [ ] Раздел 7: итоговое заключение и рекомендация.
  - [ ] Приложение: журнал расчёта.
- [ ] Цветовая схема PDF: **светлый фон** (противоположно интерфейсу).
- [ ] Графики в PDF: разрешение 150 dpi.
- [ ] Метаданные в PDF: MD5-хэш исходного файла, версия IVA, дата.

#### 9.3 Сохранение сессии

- [ ] Формат файла сессии: JSON с расширением `.vibproj`.
- [ ] Добавить метод `save(path: str)` в `AnalysisSession`:
  - Сохранять: путь к исходному файлу, `AnalysisSettings`, краткие результаты.
  - Не сохранять: сырые массивы данных (воспроизвести при открытии).
- [ ] Добавить метод `load(path: str) -> AnalysisSession`.
- [ ] В `MainWindow`: «Сохранить проект» / «Открыть проект» в меню File.
- [ ] При открытии сессии: автоматически перечитывать исходный файл и перезапускать анализ.

#### 9.4 Сравнение с CFD на странице «Профили»

В `ui/pages/profiles_page.py`:

- [ ] Кнопка «Загрузить расчётный профиль» → открывает диалог выбора файла.
- [ ] После загрузки: показывать совмещённый график (эксперимент vs CFD).
- [ ] Таблица метрик: RMSE, MAE, MAPE, r.
- [ ] Цвет линий: эксперимент — `COLOR_ACCENT`, CFD — `COLOR_WARN`.

#### 9.5 Тесты

- [ ] `tests/integration/test_pdf_report.py` — PDF генерируется и содержит > 0 байт.
- [ ] `tests/integration/test_session_save_load.py` — сессия сохраняется и открывается без потери настроек.
- [ ] `tests/integration/test_validation_pipeline.py` — сравнение двух синтетических профилей → RMSE < 0.001.

#### Критерии завершения этапа 9

- [ ] PDF-отчёт генерируется со светлым фоном и всеми разделами.
- [ ] Графики поддерживают зум и сохранение.
- [ ] Сессия сохраняется в `.vibproj` и открывается заново.
- [ ] Сравнение с CFD работает и отображает метрики.

---

================================================================================
## ЭТАП 10. КАЧЕСТВО, ПРОИЗВОДИТЕЛЬНОСТЬ, СБОРКА И РЕЛИЗ
================================================================================

### Цель этапа
Довести проект до состояния, когда его можно устанавливать, показывать
работодателю и передавать другим разработчикам.

### Конечный результат
`IVA_Setup_1.0.0.exe` — установщик для Windows 11. Все тесты проходят.
Сборка и релиз автоматизированы одним скриптом.

### Инструкция для ИИ-ассистента
> Прочитай docs/17_build_release_and_installer.md полностью.
> Создай scripts/iva.spec и scripts/installer.iss по шаблонам из этого документа.
> Сборка через PyInstaller требует Windows-окружения.
> Версию брать только из iva/__version__.py.

---

#### 10.1 Финальные тесты

- [ ] Расширить тесты `core/` до ≥ 80% покрытия (проверить через `pytest --cov=core`).
- [ ] Добавить тест производительности: полный анализ 60 000 строк завершается < 3 с.
- [ ] Проверить все граничные случаи из `docs/12_validation_and_verification.md`.
- [ ] Добавить системные тесты двух сценариев из `docs/07_user_scenarios.md`.
- [ ] Убедиться: все тесты проходят в CI (или локально на Windows).

#### 10.2 Автоматизация качества кода

- [ ] Настроить `pre-commit` (файл `.pre-commit-config.yaml`):
  - `black` с `--line-length 100`.
  - `ruff` с базовыми правилами.
  - `mypy` для `core/` и `app/`.
- [ ] Создать `scripts/lint.ps1` — запускает `black`, `ruff`, `mypy` последовательно.
- [ ] Создать `scripts/test.ps1` — запускает `pytest` с отчётом о покрытии.
- [ ] Создать `scripts/quality.ps1` — запускает сначала `lint.ps1`, затем `test.ps1`.

#### 10.3 Обновление версии

- [ ] Обновить `iva/__version__.py`: `__version__ = "1.0.0"`.
- [ ] Добавить запись в `CHANGELOG.md`: `## [1.0.0] — первый публичный релиз`.
  > Версия в одном месте. PyInstaller spec и Inno Setup читают её автоматически.

#### 10.4 Сборка PyInstaller

Создать `scripts/iva.spec`:

- [ ] Точка входа: `main.py`.
- [ ] Включить `config/defaults.toml` в дистрибутив.
- [ ] Включить `data/examples/` в дистрибутив.
- [ ] Включить иконку `assets/iva_icon.ico`.
- [ ] `console=False` (без консольного окна).
- [ ] Добавить `hiddenimports` для scipy и pandas, если PyInstaller их не найдёт автоматически.

- [ ] Собрать командой: `pyinstaller scripts/iva.spec`.
- [ ] Проверить: `dist/IVA.exe` запускается на машине разработчика.
- [ ] Проверить (если возможно): `dist/IVA.exe` запускается на чистой Windows 11 без Python.

#### 10.5 Создание установщика Inno Setup

Создать `scripts/installer.iss`:

- [ ] Имя: `Industrial Vibration Analyzer`.
- [ ] Версия: читается из `iva/__version__.py` (передать как параметр).
- [ ] Папка установки: `{pf64}\IVA\`.
- [ ] Ярлык на рабочем столе.
- [ ] Запись в «Программах и компонентах» для корректного удаления.
- [ ] `PrivilegesRequired=lowest` — установка без прав администратора.
- [ ] Включить демонстрационные файлы в установщик.

- [ ] Собрать установщик: `ISCC scripts/installer.iss`.
- [ ] Проверить: `IVA_Setup_1.0.0.exe` устанавливается.
- [ ] Проверить: установленное приложение запускается и открывает демонстрационный файл.
- [ ] Проверить: удаление через «Программы и компоненты» работает чисто.

#### 10.6 Скрипт релиза

Создать `scripts/build_installer.py`:

- [ ] Запускает тесты (`pytest tests/unit/ tests/integration/`).
- [ ] При провале тестов — останавливается.
- [ ] Запускает `pyinstaller scripts/iva.spec`.
- [ ] Запускает `ISCC scripts/installer.iss`.
- [ ] Копирует `IVA_Setup_{версия}.exe` в `dist/release/`.
- [ ] Выводит итог: путь к установщику, размер файла.
  > Полная инструкция — в docs/17_build_release_and_installer.md.

#### 10.7 Чеклист релиза

Выполнить перед каждым публичным релизом:

- [ ] Все тесты проходят (`scripts/test.ps1`).
- [ ] Качество кода проверено (`scripts/lint.ps1`).
- [ ] Версия обновлена в `iva/__version__.py`.
- [ ] `CHANGELOG.md` обновлён.
- [ ] `docs/20_roadmap.md` обновлён (известные ограничения версии).
- [ ] Глоссарий `docs/21_glossary.md` дополнен новыми терминами, если добавлялись.
- [ ] Установщик проверен на установку и удаление.
- [ ] Демонстрационный анализ на демо-файле прошёл успешно.
- [ ] `dist/release/archive/` содержит предыдущий установщик (на случай отката).

#### 10.8 Финальная документация

- [ ] Обновить `README.md` — добавить раздел «Установка и запуск».
- [ ] Обновить `docs/00_project_overview.md` — актуализировать описание первой версии.
- [ ] Подготовить `docs/22_portfolio_case_study.md` — кейс для портфолио.
- [ ] Сделать скриншоты приложения и добавить в `docs/screenshots/`.

#### Критерии завершения этапа 10

- [ ] Все тесты проходят. Покрытие `core/` ≥ 80%.
- [ ] `scripts/build_installer.py` завершается без ошибок.
- [ ] `IVA_Setup_1.0.0.exe` создан в `dist/release/`.
- [ ] Установленное приложение запускается на Windows 11.
- [ ] Демонстрационный анализ работает после установки.
- [ ] Документация актуальна.

---

================================================================================
## ФИНАЛЬНЫЙ РЕЗУЛЬТАТ ПРОЕКТА
================================================================================

После завершения всех 10 этапов:

- [ ] Исходный код организован по четырём слоям согласно `docs/02_architecture.md`.
- [ ] Расчётное ядро (`core/`) полностью независимо от GUI.
- [ ] Все входные данные проверяются на границе системы.
- [ ] Сигналы обрабатываются в детерминированном фиксированном порядке.
- [ ] Спектральный анализ корректен (верифицирован на синтетических данных).
- [ ] Физические коэффициенты рассчитываются с погрешностью < 0.1%.
- [ ] Риск резонанса оценивается объяснимо, с текстовой рекомендацией.
- [ ] Интерфейс работает на Windows 11, не зависает во время расчётов.
- [ ] PDF-отчёт включает все разделы из `docs/05_output_data_specification.md`.
- [ ] Сессия сохраняется и открывается без потери данных.
- [ ] Тесты покрывают ≥ 80% кода `core/`.
- [ ] Сборка и релиз автоматизированы одним скриптом.
- [ ] Установщик `IVA_Setup_1.0.0.exe` работает на чистой Windows 11.
- [ ] Документация из 23 файлов описывает проект со всех сторон.
- [ ] Проект можно показать работодателю, передать команде и использовать
      в реальных инженерных задачах.

---

*Версия чек-листа: 2.0. Основан на docs/00–22 проекта IVA.*
