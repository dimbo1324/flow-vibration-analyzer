# 15. Журналирование и аудит — Industrial Vibration Analyzer

## Назначение документа

Этот документ описывает систему записи событий приложения: что фиксируется, в каком формате, где хранится и как используется для диагностики проблем.

---

## Цели журналирования

Журнал решает три задачи одновременно.

**Для инженера-пользователя** — журнал в панели инспектора показывает ход выполнения анализа в реальном времени: какой файл загружен, какие шаги выполнены, что найдено, есть ли предупреждения. Это создаёт уверенность в том, что приложение работает корректно.

**Для разработчика** — файл журнала содержит подробную техническую информацию, достаточную для воспроизведения ошибки: входные параметры, стек вызовов, значения промежуточных результатов.

**Для воспроизводимости** — журнал к каждому сеансу анализа сохраняется вместе с результатами, позволяя через любое время восстановить полный контекст расчёта.

---

## Уровни журналирования

| Уровень | Назначение | Видимость |
|---|---|---|
| `DEBUG` | Детали реализации, промежуточные значения | Только файл журнала |
| `INFO` | Ключевые события рабочего процесса | Панель инспектора + файл |
| `WARNING` | Некритические проблемы с данными | Баннер в интерфейсе + файл |
| `ERROR` | Ошибки, прервавшие текущую операцию | Диалог/баннер + файл |
| `CRITICAL` | Необработанные исключения | Файл + аварийный дамп |

По умолчанию в панели инспектора отображаются уровни `INFO` и выше. Уровень `DEBUG` доступен только в файле журнала.

---

## Конфигурация журналирования

**Модуль:** `infrastructure/logging/app_logger.py`

```python
import logging
from pathlib import Path
from datetime import datetime

LOG_DIR = Path.home() / "Documents" / "IVA" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

log_filename = LOG_DIR / f"iva_{datetime.now().strftime('%Y-%m-%d')}.log"

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s.%(msecs)03d  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.FileHandler(log_filename, encoding="utf-8"),
    ]
)

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
```

Каждый модуль получает собственный именованный логгер:

```python
from infrastructure.logging.app_logger import get_logger
logger = get_logger("core.spectrum.psd_calculator")
```

Это позволяет фильтровать журнал по компоненту при диагностике.

---

## Что фиксируется в журнале

### События уровня INFO

```
12:01:04.012  INFO     infrastructure.readers.csv_reader   File read started: stend_run_047.csv
12:01:05.847  INFO     infrastructure.readers.csv_reader   File read completed: 60000 rows, 1835 ms
12:01:05.863  INFO     core.signal.preprocessor             Mean removed: offset was 0.034 m/s²
12:01:05.920  INFO     core.signal.outlier_detector         Outliers removed: 2 points replaced
12:01:06.143  INFO     core.spectrum.psd_calculator         PSD calculated: 513 frequency points, df=0.98 Hz
12:01:06.145  INFO     core.spectrum.peak_finder            Peaks found: 3 (dominant: 40.7 Hz)
12:01:06.148  INFO     core.physics.reynolds_calculator     Re = 2.39e4
12:01:06.149  INFO     core.physics.vortex_frequency        Shedding frequency: 35.0 Hz (St=0.21)
12:01:06.150  INFO     core.physics.lock_in_risk            Risk level: WATCH (deviation=14.7%)
12:01:06.152  INFO     app.analysis_runner                  Analysis completed: session abc123, 1140 ms total
```

### События уровня WARNING

```
12:01:05.848  WARNING  core.signal.preprocessor             Gap fraction 0.8% exceeds 0.5% threshold, interpolation applied
12:01:05.920  WARNING  core.signal.outlier_detector         Outlier fraction 1.2% is high, consider checking sensor
```

### События уровня ERROR

```
12:01:04.015  ERROR    infrastructure.readers.csv_reader    Non-monotonic time axis at row 12450
12:01:04.015  ERROR    app.workflow_coordinator             Validation failed: ValidationError('Non-monotonic time axis')
```

### События уровня DEBUG

```
12:01:06.100  DEBUG    core.spectrum.psd_calculator         nperseg=1024, noverlap=512, window=hann
12:01:06.110  DEBUG    core.spectrum.peak_finder            Baseline PSD (median): -42.3 dB, threshold: -32.3 dB
12:01:06.115  DEBUG    core.spectrum.peak_finder            Candidate peaks before width filter: 7
```

---

## Что не фиксируется в журнале

Журнал никогда не содержит:
- пути к файлам, содержащие персональную информацию (полный путь заменяется именем файла);
- числовые данные из загруженных файлов (только агрегированные характеристики);
- любые данные, которые пользователь мог бы считать конфиденциальными.

---

## Ротация файлов журнала

Журнал ведётся посуточно. Новый файл создаётся в полночь или при первом запуске приложения в новый день. Файлы старше 30 дней удаляются автоматически при запуске приложения.

Максимальный размер одного файла журнала: 50 МБ. При превышении создаётся новый файл с суффиксом `_2`, `_3` и т.д.

---

## Журнал сеанса анализа

Помимо общего журнала приложения, для каждого завершённого анализа создаётся отдельный файл журнала сеанса:

```
%USERPROFILE%\Documents\IVA\results\{имя_файла}_{дата}_{время}_session.log
```

Этот файл содержит только события, относящиеся к данному анализу, и сохраняется рядом с результатами. Он включается в PDF-отчёт как приложение.

---

## Аварийный дамп

При необработанном исключении (уровень CRITICAL) приложение:
1. Записывает полный стек вызовов в файл `iva_crash_{timestamp}.log` в папке журналов.
2. Выводит пользователю диалог с сообщением: «Произошла неожиданная ошибка. Приложение будет закрыто. Файл диагностики сохранён по адресу: {путь}».
3. Корректно завершает работу.

Аварийный дамп не содержит данных пользователя — только стек вызовов и системную информацию (версия ОС, версия приложения, объём свободной памяти).

---

*Версия документа: 1.0. Дата: 2025. Ответственный: автор проекта.*
