# Dockerfile для воспроизводимых проверок IVA в Linux-контейнере.
#
# Назначение: запуск тестов, линтера, mypy и CLI-демо в среде, близкой к CI.
# Не предназначен для сборки Windows-установщика и не запускает PySide6 GUI
# (нативный оконный режим Qt не поддерживается без X11/Wayland).
#
# Сборка:  docker build -t iva-dev .
# Запуск:  docker run --rm iva-dev

FROM python:3.12-slim

# Системные пакеты: минимальный набор для headless-тестирования PySide6
# и рендеринга Matplotlib. libEGL/libGL нужны PySide6 даже в offscreen-режиме.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libegl1 \
    libgl1 \
    libglib2.0-0 \
    libxkbcommon-x11-0 \
    libdbus-1-3 \
    libfontconfig1 \
    libfreetype6 \
    && rm -rf /var/lib/apt/lists/*

# Headless-режим: Qt рисует в памяти, Matplotlib использует не-интерактивный бэкенд.
ENV QT_QPA_PLATFORM=offscreen \
    QT_OPENGL=software \
    MPLBACKEND=Agg

WORKDIR /app

# Копируем только файлы зависимостей — слой кешируется пока они не изменились.
COPY requirements.txt requirements-dev.txt ./

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements-dev.txt

# Копируем исходный код проекта.
COPY . .

# Устанавливаем пакет в editable-режиме, чтобы импорты работали как в .venv.
RUN pip install --no-cache-dir -e .

# Команда по умолчанию: проверка состояния проекта, безопасная для любого окружения.
CMD ["python", "-m", "pytest", "-m", "not performance", "-q"]
