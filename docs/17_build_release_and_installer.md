# 17. Сборка, релиз и установщик — Industrial Vibration Analyzer

## Назначение документа

Этот документ описывает процесс сборки приложения в исполняемый файл и создания установщика для Windows 11. Любой разработчик с доступом к репозиторию должен быть способен воспроизвести сборку по этому документу.

---

## Обзор процесса

```
[Исходный код Python]
        │
        ▼
  pytest (все тесты)
        │ если пройдены
        ▼
  PyInstaller → однофайловый .exe приложения
        │
        ▼
  Inno Setup → IVA_Setup_{версия}.exe
        │
        ▼
  [Готовый установщик для передачи пользователю]
```

Весь процесс автоматизирован скриптом `scripts/build_installer.py`. Ручные шаги не требуются.

---

## Требования к среде сборки

- Windows 11 (64-bit)
- Python 3.11+ (для выполнения скрипта сборки)
- Inno Setup 6.x (установлен и добавлен в PATH)
- Все зависимости из `requirements.txt` установлены

Проверка готовности среды:

```bash
python scripts/build_installer.py --check-only
```

---

## Конфигурация PyInstaller

Файл `scripts/iva.spec` содержит конфигурацию сборки. Ключевые параметры:

```python
# scripts/iva.spec

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('config/defaults.toml', 'config'),
        ('tests/fixtures/dissertation', 'tests/fixtures/dissertation'),
    ],
    hiddenimports=[
        'scipy.signal._max_len_seq_inner',
        'scipy._lib.messagestream',
        'pandas._libs.tslibs.timedeltas',
    ],
    ...
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='IVA',
    debug=False,
    strip=False,
    upx=True,
    console=False,               # Без консольного окна
    icon='assets/iva_icon.ico',
    version='version_info.txt',
)
```

Результат сборки PyInstaller: один файл `dist/IVA.exe`, содержащий Python-интерпретатор и все зависимости.

---

## Конфигурация Inno Setup

Файл `scripts/installer.iss` описывает установщик:

```ini
[Setup]
AppName=Industrial Vibration Analyzer
AppVersion={#AppVersion}
DefaultDirName={commonpf64}\IVA
DefaultGroupName=Industrial Vibration Analyzer
OutputDir=dist\installer
OutputBaseFilename=IVA_Setup_{#AppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
PrivilegesRequired=lowest      ; Установка без прав администратора

[Files]
Source: "dist\IVA.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Industrial Vibration Analyzer"; Filename: "{app}\IVA.exe"
Name: "{commondesktop}\Industrial Vibration Analyzer"; Filename: "{app}\IVA.exe"

[Run]
Filename: "{app}\IVA.exe"; Description: "Запустить приложение"; Flags: nowait postinstall skipifsilent
```

---

## Управление версией

Версия приложения определяется в одном месте — файле `iva/__version__.py`:

```python
__version__ = "1.0.0"
```

Все остальные места (PyInstaller spec, Inno Setup script, заголовок окна, PDF-отчёт) получают версию из этого файла. Дублирование версии в нескольких местах запрещено.

Формат версии: `MAJOR.MINOR.PATCH` по принципу семантического версионирования:
- `MAJOR` — несовместимые изменения формата входных/выходных данных;
- `MINOR` — новые функции, обратно совместимые;
- `PATCH` — исправления ошибок.

---

## Запуск сборки

```bash
# Полная сборка с тестами
python scripts/build_installer.py

# Сборка без запуска тестов (только для отладки сборочного процесса)
python scripts/build_installer.py --skip-tests

# Проверка среды без сборки
python scripts/build_installer.py --check-only
```

Скрипт выполняет следующие шаги:
1. Проверяет наличие всех инструментов.
2. Запускает `pytest tests/unit/ tests/integration/`.
3. Если тесты пройдены — запускает `pyinstaller scripts/iva.spec`.
4. Запускает Inno Setup с `scripts/installer.iss`.
5. Выводит путь к готовому установщику и его размер.
6. Фиксирует результат сборки в `build_log.txt`.

---

## Результат сборки

Готовый установщик находится в:
```
dist/installer/IVA_Setup_{версия}.exe
```

Размер установщика: приблизительно 60–90 МБ (зависит от версий зависимостей). Размер после установки: приблизительно 150–220 МБ.

---

## Чеклист перед релизом

Перед каждым релизом разработчик обязан пройти следующий чеклист:

- [ ] Все тесты пройдены (`pytest` без падений)
- [ ] Версия обновлена в `iva/__version__.py`
- [ ] Раздел «Что нового» в `20_roadmap.md` актуален
- [ ] Глоссарий `21_glossary.md` дополнен при добавлении новых терминов
- [ ] Установщик запущен на чистой машине без Python
- [ ] Приложение успешно установилось, запустилось и выполнило тестовый анализ
- [ ] Установщик успешно удалился через «Программы и компоненты»

---

## Откат релиза

Если после выпуска обнаружена критическая ошибка:
1. Предыдущий установщик хранится в `dist/installer/archive/`.
2. Пользователю передаётся предыдущий установщик с комментарием об ошибке.
3. Исправление выпускается как PATCH-версия.

---

*Версия документа: 1.0. Дата: 2025. Ответственный: автор проекта.*
