#!/usr/bin/env python
"""Точка входа настольного приложения Industrial Vibration Analyzer."""

from __future__ import annotations

import os
import sys


def main() -> int:
    """Запустить настольное приложение IVA.

    Returns:
        Exit code (0 on success, 1 on import error).
    """
    if "--smoke-test" not in sys.argv and os.environ.get("QT_QPA_PLATFORM") == "offscreen":
        # A leftover offscreen platform (typically from an interrupted smoke
        # test in the same shell) would render the GUI window invisible.
        print(
            "Предупреждение: QT_QPA_PLATFORM=offscreen снят для запуска графического интерфейса.",
            file=sys.stderr,
        )
        del os.environ["QT_QPA_PLATFORM"]

    try:
        from PySide6.QtWidgets import QApplication  # type: ignore[import-untyped]

        from iva.ui.main_window import MainWindow
        from iva.ui.styles.theme import apply_dark_theme
    except ImportError as exc:
        print(
            "Ошибка: PySide6 не установлен.\n"
            "Установите его командой: pip install PySide6\n"
            f"Подробности: {exc}",
            file=sys.stderr,
        )
        return 1

    _existing = QApplication.instance()
    app: QApplication = _existing if isinstance(_existing, QApplication) else QApplication(sys.argv)
    apply_dark_theme(app)
    window = MainWindow()
    window.show()
    if "--smoke-test" in sys.argv:
        app.processEvents()
        window.close()
        return 0
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
