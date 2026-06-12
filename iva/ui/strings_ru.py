"""Russian user-interface strings and display-label helpers.

This module deliberately has no Qt or file-system dependencies so it can be
imported by UI tests without initialising the desktop runtime.
"""

from __future__ import annotations

from collections.abc import Mapping

__all__ = [
    "GEOMETRY_LABELS",
    "PEAK_INTERPRETATION_LABELS",
    "RISK_LABELS",
    "SIGNAL_ROLE_LABELS",
    "display_label",
    "source_value",
    "tr",
]


UI_STRINGS: dict[str, str] = {
    "Industrial Vibration Analyzer (IVA)": "Анализатор вибраций потока (IVA)",
    "Main Toolbar": "Главная панель инструментов",
    "01  Overview": "01  Сводка",
    "02  Import": "02  Импорт",
    "03  Signal": "03  Сигнал",
    "04  Spectrum": "04  Спектр",
    "05  Physics": "05  Физика",
    "06  Profiles": "06  Профили",
    "07  Report": "07  Отчёт",
    "01 — Overview": "01 — Сводка",
    "02 — Import": "02 — Импорт",
    "03 — Signal": "03 — Сигнал",
    "04 — Spectrum": "04 — Спектр",
    "05 — Physics": "05 — Физика",
    "06 — Profiles": "06 — Профили",
    "07 — Report": "07 — Отчёт",
    "Open File  (Ctrl+O)": "Открыть файл  (Ctrl+O)",
    "Open a data file (Ctrl+O)": "Открыть файл данных (Ctrl+O)",
    "Run Analysis  (F5)": "Запустить анализ  (F5)",
    "Run the full analysis pipeline (F5)": "Запустить полный анализ (F5)",
    "Save Project  (Ctrl+S)": "Сохранить проект  (Ctrl+S)",
    "Save project session as .vibproj file (Ctrl+S)": "Сохранить сеанс в файл .vibproj (Ctrl+S)",
    "Save Project As…  (Ctrl+Shift+S)": "Сохранить проект как…  (Ctrl+Shift+S)",
    "Save project session with a new name (Ctrl+Shift+S)": (
        "Сохранить сеанс проекта под новым именем (Ctrl+Shift+S)"
    ),
    "Open Project  (Ctrl+Shift+O)": "Открыть проект  (Ctrl+Shift+O)",
    "Open a saved .vibproj session file (Ctrl+Shift+O)": (
        "Открыть сохраненный сеанс .vibproj (Ctrl+Shift+O)"
    ),
    "New Session  (Ctrl+N)": "Новый сеанс  (Ctrl+N)",
    "Clear current session (Ctrl+N)": "Очистить текущий сеанс (Ctrl+N)",
    "Export Report Bundle…": "Экспортировать комплект отчетов…",
    "Export PDF, HTML, JSON and CSV reports to a directory": (
        "Экспортировать отчеты PDF, HTML, JSON и CSV в папку"
    ),
    "Inspector  (R)": "Инспектор  (R)",
    "Toggle inspector panel (R)": "Показать или скрыть панель инспектора (R)",
    "Ready": "Готово",
    "Inspector": "Инспектор",
    "Open Data File": "Открыть файл данных",
    "Data Files (*.csv *.parquet *.xlsx);;CSV Files (*.csv);;All Files (*)": (
        "Файлы данных (*.csv *.parquet *.xlsx);;" "Файлы CSV (*.csv);;Все файлы (*)"
    ),
    "IVA Project Files (*.vibproj);;All Files (*)": "Проекты IVA (*.vibproj);;Все файлы (*)",
    "CSV Files (*.csv);;All Files (*)": "Файлы CSV (*.csv);;Все файлы (*)",
    "Running analysis…": "Выполняется анализ…",
    "Analysis complete": "Анализ завершен",
    "Analysis failed": "Ошибка анализа",
    "Unexpected Error": "Непредвиденная ошибка",
    "Error — see banner": "Ошибка — подробности в верхней панели",
    "Error Details": "Сведения об ошибке",
    "New session started": "Новый сеанс создан",
    "Nothing to save — run an analysis first": "Нечего сохранять — сначала выполните анализ",
    "Save Project As": "Сохранить проект как",
    "Open Project": "Открыть проект",
    "Nothing to export — run an analysis first": "Нечего экспортировать — сначала выполните анализ",
    "Select Output Directory for Report Bundle": "Выберите папку для комплекта отчетов",
    "Analysis summary — dominant metrics at a glance": "Сводка анализа и основные показатели",
    "Dominant Peak": "Доминирующий пик",
    "Total RMS": "Общий RMS",
    "Shedding Freq": "Частота срыва",
    "Risk Level": "Уровень риска",
    "Signal / Spectrum": "Сигнал / Спектр",
    "Assessment": "Оценка",
    "Select a data file and assign column roles": "Выберите файл данных и назначьте роли столбцов",
    "Data File": "Файл данных",
    "Drag and drop a file here\nor use 'Open File' (Ctrl+O)": (
        "Перетащите файл сюда\nили нажмите «Открыть файл» (Ctrl+O)"
    ),
    "File:": "Файл:",
    "No file selected": "Файл не выбран",
    "Column Assignment": "Назначение столбцов",
    "Time column:": "Столбец времени:",
    "Signal column:": "Столбец сигнала:",
    "Signal role:": "Роль сигнала:",
    "Physical Parameters": "Физические параметры",
    "Sampling rate:": "Частота дискретизации:",
    "Sensor conversion factor:": "Коэффициент преобразования датчика:",
    "Time-domain signal — cleaned and filtered": "Сигнал во времени — очищенный и отфильтрованный",
    "Signal (cleaned vs filtered)": "Сигнал: очищенный и отфильтрованный",
    "RMS Trend": "Динамика RMS",
    "Preprocessing Log": "Журнал предобработки",
    "No preprocessing log available.": "Журнал предобработки отсутствует.",
    "No operations logged.": "Операции не зарегистрированы.",
    "Cleaned": "Очищенный",
    "Filtered": "Отфильтрованный",
    "Power spectral density — Welch method": "Спектральная плотность мощности — метод Уэлча",
    "Detected Peaks": "Обнаруженные пики",
    "Freq (Hz)": "Частота (Hz)",
    "Amplitude": "Амплитуда",
    "Width (Hz)": "Ширина (Hz)",
    "Interpretation": "Интерпретация",
    "Flow and geometry parameters — dimensionless criteria": (
        "Параметры потока и геометрии — безразмерные критерии"
    ),
    "Flow Parameters (SI units)": "Параметры потока (СИ)",
    "Cylinder diameter (m):": "Диаметр цилиндра (m):",
    "Mean flow velocity (m/s):": "Средняя скорость потока (m/s):",
    "Fluid density (kg/m³):": "Плотность жидкости (kg/m³):",
    "Dynamic viscosity (Pa·s):": "Динамическая вязкость (Pa·s):",
    "Natural frequency fn (Hz):": "Собственная частота fn (Hz):",
    "Damping ratio ζ:": "Коэффициент демпфирования ζ:",
    "Cylinder spacing (m):": "Шаг цилиндров (m):",
    "Geometry type:": "Тип геометрии:",
    "Computed Results": "Результаты расчета",
    "Reynolds Number": "Число Рейнольдса",
    "Strouhal Number": "Число Струхаля",
    "Velocity Ratio": "Приведенная скорость",
    "Frequency Ratio": "Отношение частот",
    "Experiment vs CFD velocity profile comparison": (
        "Сравнение профилей скорости эксперимента и CFD"
    ),
    "Load Profile Files": "Загрузка файлов профилей",
    "Load Experiment CSV…": "Загрузить CSV эксперимента…",
    "Load CFD CSV…": "Загрузить CSV CFD…",
    "Compare": "Сравнить",
    "No experiment file": "Файл эксперимента не выбран",
    "No CFD file": "Файл CFD не выбран",
    "Validation Metrics": "Метрики сравнения",
    "Metric": "Метрика",
    "Value": "Значение",
    "Load Experiment Profile CSV": "Загрузить CSV профиля эксперимента",
    "Load CFD Profile CSV": "Загрузить CSV профиля CFD",
    "Comparison complete.": "Сравнение завершено.",
    "Export analysis results as PDF, HTML, JSON or CSV": (
        "Экспорт результатов анализа в PDF, HTML, JSON или CSV"
    ),
    "No analysis result available.": "Результат анализа отсутствует.",
    "Export": "Экспорт",
    "Export PDF": "Экспорт PDF",
    "Export HTML": "Экспорт HTML",
    "Export JSON Summary": "Экспорт сводки JSON",
    "Export CSV Package": "Экспорт комплекта CSV",
    "Spectrum CSV": "CSV спектра",
    "Signal CSV": "CSV сигнала",
    "Physics CSV": "CSV физических параметров",
    "Analysis Summary": "Сводка анализа",
    "Select Output Directory for CSV Package": "Выберите папку для комплекта CSV",
    "Reset view": "Сбросить вид",
    "Save PNG": "Сохранить PNG",
    "Inspect cursor": "Координаты курсора",
    "Chart hints": "Колесо мыши — масштаб · перетаскивание — панорама · F — фокус · Esc — выход",
    "Chart requires matplotlib\n(pip install matplotlib)": (
        "Для графика требуется matplotlib\n(pip install matplotlib)"
    ),
    "Save Chart as PNG": "Сохранить график как PNG",
    "PNG Images (*.png)": "Изображения PNG (*.png)",
    "Signal": "Сигнал",
    "Time (s)": "Время (s)",
    "Frequency (Hz)": "Частота (Hz)",
    "Experiment": "Эксперимент",
    "Coordinate": "Координата",
}

RISK_LABELS: dict[str, str] = {
    "safe": "БЕЗОПАСНО",
    "watch": "НАБЛЮДЕНИЕ",
    "critical": "КРИТИЧЕСКИЙ",
}

SIGNAL_ROLE_LABELS: dict[str, str] = {
    "acceleration_x": "Ускорение X",
    "acceleration_y": "Ускорение Y",
    "acceleration_z": "Ускорение Z",
    "pressure": "Давление",
    "velocity": "Скорость",
}

GEOMETRY_LABELS: dict[str, str] = {
    "single_cylinder": "Одиночный цилиндр",
    "tandem": "Тандем",
}

PEAK_INTERPRETATION_LABELS: dict[str, str] = {
    "vortex_shedding": "Срыв вихрей",
    "harmonic": "Гармоника",
    "structural": "Конструкционная частота",
    "unknown": "Не определено",
}


def tr(text: str) -> str:
    """Return the Russian UI translation for *text*, or *text* unchanged."""
    return UI_STRINGS.get(text, text)


def display_label(labels: Mapping[str, str], value: object) -> str:
    """Return a localized label for a stable enum/string value."""
    key = str(value).lower()
    return labels.get(key, str(value))


def source_value(labels: Mapping[str, str], label: str) -> str:
    """Return the stable source value associated with a localized label."""
    for value, translated in labels.items():
        if translated == label:
            return value
    return label
