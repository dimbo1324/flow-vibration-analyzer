# 11. Алгоритмы — Industrial Vibration Analyzer

## Назначение документа

Этот документ описывает конкретные алгоритмы, реализованные в расчётных модулях приложения. Для каждого алгоритма указаны: входные данные, выходные данные, псевдокод или описание шагов, ссылка на реализующий модуль и ключевые параметры.

---

## Алгоритм 1 — Устранение постоянной составляющей

**Модуль:** `core/signal/preprocessor.py`  
**Функция:** `remove_mean(signal: np.ndarray) -> np.ndarray`

**Описание:** вычитание арифметического среднего из каждого значения сигнала. Простейшая, но обязательная операция: постоянная составляющая создаёт в спектре огромный пик на частоте 0 Гц, который маскирует полезные пики и искажает оценку RMS.

**Шаги:**
1. Вычислить `mean = np.mean(signal)`.
2. Вернуть `signal - mean`.

**Сложность:** O(n).

---

## Алгоритм 2 — Обнаружение выбросов методом скользящего медианного порога

**Модуль:** `core/signal/outlier_detector.py`  
**Функция:** `detect_outliers(signal, window_samples, threshold_sigma) -> np.ndarray[bool]`

**Описание:** для каждой точки сигнала вычисляется медиана в локальном окне. Точка считается выбросом, если её значение отклоняется от медианы более чем на `threshold_sigma` стандартных отклонений.

Медианный фильтр (а не среднее) выбран намеренно: медиана устойчива к самим выбросам, тогда как скользящее среднее смещается под их влиянием.

**Шаги:**
1. Вычислить скользящую медиану `m(t)` с окном ширины `window_samples`.
2. Вычислить MAD (median absolute deviation): `mad = median(|signal − m|)`.
3. Вычислить устойчивую оценку стандартного отклонения: `sigma_robust = 1.4826 * mad`.
4. Пометить точку как выброс, если `|signal(t) − m(t)| > threshold_sigma * sigma_robust`.
5. Вернуть булев массив с отметками выбросов.

Коэффициент 1.4826 делает MAD-оценку состоятельной относительно нормального распределения.

**Параметры по умолчанию:** `window_samples = 21`, `threshold_sigma = 4.0`.

---

## Алгоритм 3 — Заполнение пропусков линейной интерполяцией

**Модуль:** `core/signal/preprocessor.py`  
**Функция:** `fill_gaps(signal, time_array, max_gap_seconds) -> np.ndarray`

**Шаги:**
1. Найти позиции NaN или отмеченных выбросов в сигнале.
2. Объединить соседние позиции в непрерывные промежутки.
3. Для каждого промежутка:
   - если длина промежутка ≤ `max_gap_seconds * sampling_rate`: заполнить линейной интерполяцией между граничными значениями;
   - иначе: заполнить нулями (выход на линию нуля).
4. Вернуть заполненный массив.

---

## Алгоритм 4 — Цифровой полосовой фильтр Баттерворта

**Модуль:** `core/signal/filter.py`  
**Функция:** `apply_bandpass_filter(signal, sampling_rate_hz, low_hz, high_hz, order) -> np.ndarray`

**Описание:** реализация через `scipy.signal.butter` + `scipy.signal.filtfilt`. Двойная фильтрация (filtfilt) обеспечивает нулевой фазовый сдвиг — временны́е события в сигнале не смещаются.

**Шаги:**
1. Вычислить нормированные частоты Найквиста: `low_norm = low_hz / (sampling_rate_hz / 2)`, аналогично для `high_norm`.
2. Проверить: `0 < low_norm < high_norm < 1`. При нарушении — `FilterConfigurationError`.
3. Получить коэффициенты фильтра: `b, a = scipy.signal.butter(order, [low_norm, high_norm], btype='band')`.
4. Применить: `return scipy.signal.filtfilt(b, a, signal)`.

**Параметры по умолчанию:** `order = 4`, `low_hz = 5.0`, `high_hz = 250.0`.

---

## Алгоритм 5 — Спектральная плотность мощности методом Уэлча

**Модуль:** `core/spectrum/psd_calculator.py`  
**Функция:** `calculate_psd(signal, sampling_rate_hz, settings: SpectralSettings) -> tuple[np.ndarray, np.ndarray]`

**Реализация:** тонкая обёртка над `scipy.signal.welch` с явным управлением параметрами.

**Шаги:**
1. Выбрать оконную функцию по типу из `settings.window_type`.
2. Вычислить количество отсчётов перекрытия: `noverlap = int(settings.segment_length_samples * settings.overlap_fraction)`.
3. Вызвать `scipy.signal.welch(signal, fs=sampling_rate_hz, window=window_function, nperseg=settings.segment_length_samples, noverlap=noverlap, scaling='density')`.
4. Вернуть `(frequencies, psd_values)`.

**Разрешение по частоте:** `delta_f = sampling_rate_hz / segment_length_samples`.

При параметрах по умолчанию (fs = 1000 Гц, nperseg = 1024): `delta_f ≈ 0.98 Гц`.

---

## Алгоритм 6 — Поиск пиков в спектре

**Модуль:** `core/spectrum/peak_finder.py`  
**Функция:** `find_peaks(frequencies, psd_values, settings: SpectralSettings) -> list[SpectralPeak]`

**Шаги:**
1. Перевести PSD в логарифмический масштаб: `psd_db = 10 * log10(psd_values + epsilon)`.
2. Вычислить базовый уровень: `baseline = median(psd_db)`.
3. Найти кандидаты в пики: локальные максимумы, превышающие `baseline + threshold_db`.
4. Отфильтровать пики по минимальной ширине: ширина пика на уровне baseline + threshold_db / 2 должна быть не менее `peak_min_width_hz`.
5. Для каждого пика вычислить ширину на уровне -3 дБ относительно пика (стандартный метод half-power).
6. Классифицировать пики (алгоритм 7).
7. Вернуть список объектов `SpectralPeak`, отсортированный по амплитуде.

---

## Алгоритм 7 — Интерпретация спектральных пиков

**Модуль:** `core/spectrum/peak_finder.py`  
**Функция:** `interpret_peak(peak_freq, all_peaks, physics_result: PhysicsResult | None) -> PeakInterpretation`

**Правила классификации (применяются последовательно, первое совпадение определяет результат):**

1. **VORTEX_SHEDDING**: если `|peak_freq − physics_result.calculated_shedding_frequency_hz| / physics_result.calculated_shedding_frequency_hz < 0.05` (отклонение менее 5% от расчётной частоты срыва). Применяется только если `physics_result` доступен.

2. **HARMONIC**: если `peak_freq` отличается от другого пика с амплитудой выше в 2 раза не более чем на 2% от кратного значения (2×, 3×, 4×).

3. **STRUCTURAL**: если `physics_result.natural_frequency_hz` задана и отклонение от неё менее 3%.

4. **UNKNOWN**: во всех остальных случаях.

Значение `confidence` вычисляется как `1.0 − (relative_deviation / threshold)` для правил 1 и 3; для правила 2 — фиксировано 0.85.

---

## Алгоритм 8 — Расчёт скользящего RMS

**Модуль:** `core/spectrum/rms_calculator.py`  
**Функция:** `calculate_rms_trend(signal, sampling_rate_hz, window_seconds) -> np.ndarray`

**Шаги:**
1. Вычислить размер окна в отсчётах: `window_samples = int(window_seconds * sampling_rate_hz)`.
2. Вычислить квадрат сигнала: `signal_sq = signal ** 2`.
3. Применить скользящее среднее к `signal_sq` с помощью `np.convolve(signal_sq, np.ones(window_samples) / window_samples, mode='valid')`.
4. Взять квадратный корень: `rms_trend = np.sqrt(moving_mean)`.
5. Дополнить началом: первые `window_samples // 2` значений дублируются от первого вычисленного значения.

Использование `np.convolve` вместо Python-цикла обеспечивает векторизованное выполнение.

---

## Алгоритм 9 — Определение числа Струхаля для тандема цилиндров

**Модуль:** `core/physics/strouhal_calculator.py`  
**Функция:** `get_strouhal_number(re, geometry_type, spacing_ratio) -> float`

**Описание:** число Струхаля зависит от Re и типа конфигурации. Для одиночного цилиндра используется кусочно-линейная аппроксимация по табличным данным Бlevins. Для тандема цилиндров используется таблица значений, полученных в ходе диссертационного исследования.

**Шаги для одиночного цилиндра:**
1. Если `Re < 1000`: возврат значения из таблицы Бlevins (Re = 200–1000).
2. Если `1000 ≤ Re ≤ 100000`: линейная интерполяция по таблице.
3. Если `Re > 100000`: значение 0.20 (плато турбулентного режима).

**Для тандема:** двумерная интерполяция по сетке (Re, spacing_ratio) из таблицы данных диссертации.

---

## Алгоритм 10 — Оценка риска резонанса

**Модуль:** `core/physics/lock_in_risk.py`  
**Функция:** `assess_risk(physics_result, spectrum_result) -> RiskAssessment`

**Шаги:**
1. Если `natural_frequency_hz` не задана — вернуть `RiskAssessment(risk_level=SAFE, ...)` с пометкой «собственная частота не задана».
2. Вычислить `deviation = |fs − fn| / fn`, где `fs = calculated_shedding_frequency_hz`.
3. Определить уровень риска по таблице:
   - `deviation > 0.30` → SAFE
   - `0.10 < deviation ≤ 0.30` → WATCH
   - `deviation ≤ 0.10` → CRITICAL
4. Если уровень WATCH или CRITICAL, дополнительно проверить амплитуду ближайшего пика в спектре. Если амплитуда мала (пик не выделяется над фоном) — понизить уровень на один шаг.
5. Сформировать текст рекомендации на основании уровня риска и `deviation`.
6. Перечислить факторы, повлиявшие на решение.

---

## Алгоритм 11 — Расчёт метрик сравнения

**Модуль:** `core/validation/error_metrics.py`

Все метрики требуют одинаковой длины массивов `experiment` и `cfd`. Интерполяция на общую сетку координат выполняется в `core/validation/experiment_vs_cfd.py` до вызова этих функций.

```python
def rmse(experiment, cfd):
    return np.sqrt(np.mean((experiment - cfd) ** 2))

def mae(experiment, cfd):
    return np.mean(np.abs(experiment - cfd))

def mape(experiment, cfd):
    mask = np.abs(experiment) > MAPE_DENOMINATOR_THRESHOLD
    if not np.any(mask):
        return None  # невозможно вычислить
    return 100.0 * np.mean(np.abs((experiment[mask] - cfd[mask]) / experiment[mask]))

def pearson_r(experiment, cfd):
    return np.corrcoef(experiment, cfd)[0, 1]
```

Константа `MAPE_DENOMINATOR_THRESHOLD = 1e-6` (в физических единицах измеряемой величины) защищает от деления на ноль.

---

*Версия документа: 1.0. Дата: 2025. Ответственный: автор проекта.*
