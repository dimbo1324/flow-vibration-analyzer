"""Точка входа командной строки Industrial Vibration Analyzer.

Usage::

    python -m iva.cli.main analyze \\
        --data data/examples/example_clean_sine.csv \\
        --config config/example_config.json \\
        --output reports/run_001

Коды возврата:
    0 — успех
    1 — ожидаемая доменная ошибка IVA
    2 — непредвиденная ошибка Python

Архитектурное правило: CLI не импортирует ``iva.ui`` или ``PySide6``.
"""

from __future__ import annotations

import argparse
import sys
import traceback
from collections.abc import Sequence
from pathlib import Path
from typing import NoReturn

from iva.app.analysis_runner import AnalysisRunner
from iva.app.analysis_session import AnalysisSession
from iva.app.demo_service import create_demo_session, list_available_demo_scenarios
from iva.app.report_service import export_report_html, export_report_pdf
from iva.app.session_service import save_current_session
from iva.app.settings_manager import load_analysis_config_json
from iva.core.models.exceptions import IVAError
from iva.infrastructure.writers.csv_export_writer import (
    export_physics_summary_csv,
    export_signal_csv,
    export_spectrum_csv,
)
from iva.infrastructure.writers.html_summary_writer import export_analysis_summary_html
from iva.infrastructure.writers.json_export_writer import export_analysis_summary_json

__all__ = ["main", "build_parser"]


_RISK_LABELS = {
    "safe": "БЕЗОПАСНО",
    "watch": "НАБЛЮДЕНИЕ",
    "critical": "КРИТИЧЕСКИЙ",
}


class _RussianArgumentParser(argparse.ArgumentParser):
    """ArgumentParser с локализованными стандартными заголовками и ошибками."""

    @staticmethod
    def _localize(text: str) -> str:
        replacements = {
            "usage:": "использование:",
            "options:": "параметры:",
            "positional arguments:": "позиционные аргументы:",
            "show this help message and exit": "показать эту справку и выйти",
        }
        for source, translated in replacements.items():
            text = text.replace(source, translated)
        return text

    def format_help(self) -> str:
        return self._localize(super().format_help())

    def format_usage(self) -> str:
        return self._localize(super().format_usage())

    def error(self, message: str) -> NoReturn:
        message = message.replace(
            "the following arguments are required:", "не указаны обязательные аргументы:"
        )
        message = message.replace("expected one argument", "требуется одно значение")
        message = message.replace("invalid choice", "недопустимый вариант")
        self.print_usage(sys.stderr)
        self.exit(2, f"{self.prog}: ошибка: {message}\n")


def build_parser() -> argparse.ArgumentParser:
    """Собрать парсер CLI без изменения стабильных имён команд и флагов."""
    parser = _RussianArgumentParser(
        prog="iva",
        description="Анализатор вибраций потока IVA - интерфейс командной строки",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Пример:\n"
            "  python -m iva.cli.main analyze \\\n"
            "      --data data/examples/example_clean_sine.csv \\\n"
            "      --config config/example_config.json \\\n"
            "      --output reports/run_001\n"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", metavar="КОМАНДА")

    analyze = subparsers.add_parser(
        "analyze",
        help="Выполнить полный анализ вибраций по файлу данных и конфигурации.",
    )
    analyze.add_argument(
        "--data",
        required=True,
        metavar="ПУТЬ",
        help="Путь к входному файлу данных (.csv, .parquet или .xlsx).",
    )
    analyze.add_argument(
        "--config",
        required=True,
        metavar="ПУТЬ",
        help="Путь к файлу конфигурации анализа JSON.",
    )
    analyze.add_argument(
        "--output",
        required=True,
        metavar="ПАПКА",
        help="Папка для записи файлов с результатами.",
    )
    analyze.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="Печатать полную трассировку при ошибке (для отладки).",
    )
    # Экспорт отчётов и проекта необязателен: базовый analyze всегда сохраняет
    # машиночитаемые результаты, а тяжёлые пользовательские форматы включаются явно.
    analyze.add_argument(
        "--export-pdf",
        action="store_true",
        default=False,
        help="Экспортировать отчет PDF в папку результатов.",
    )
    analyze.add_argument(
        "--export-html",
        action="store_true",
        default=False,
        help="Экспортировать отчет HTML в папку результатов.",
    )
    analyze.add_argument(
        "--save-project",
        action="store_true",
        default=False,
        help="Сохранить сеанс как файл .vibproj в папке результатов.",
    )

    demo = subparsers.add_parser(
        "demo",
        help="Запустить полный анализ встроенного синтетического сценария.",
    )
    demo.add_argument(
        "--scenario",
        default="clean_40hz",
        metavar="КЛЮЧ",
        help="Ключ демо-сценария (по умолчанию: clean_40hz).",
    )
    demo.add_argument(
        "--list-scenarios",
        action="store_true",
        help="Показать доступные демо-сценарии и завершить работу.",
    )
    demo.add_argument(
        "--output",
        metavar="ПАПКА",
        help="Папка результатов (по умолчанию: out/cli-runs/demo_<сценарий>).",
    )
    demo.add_argument(
        "--export-pdf",
        action="store_true",
        default=False,
        help="Экспортировать отчет PDF в папку результатов.",
    )
    demo.add_argument(
        "--export-html",
        action="store_true",
        default=False,
        help="Экспортировать полный отчет HTML в папку результатов.",
    )
    demo.add_argument(
        "--save-project",
        action="store_true",
        default=False,
        help="Сохранить демо-сеанс как файл .vibproj.",
    )
    demo.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="Печатать полную трассировку при ошибке (для отладки).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Разобрать аргументы и вернуть процессу стабильный код завершения.

    Args:
        argv: Список аргументов; ``None`` означает ``sys.argv[1:]``.

    Returns:
        Код завершения: 0 — успех, 1 — IVAError, 2 — непредвиденная ошибка.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "analyze":
        return _run_analyze(args)
    if args.command == "demo":
        return _run_demo(args)

    parser.print_help()
    return 1


def _run_analyze(args: argparse.Namespace) -> int:
    """Выполнить подкоманду ``analyze`` через штатный слой приложения.

    Args:
        args: Разобранные аргументы ``data``, ``config``, ``output`` и ``debug``.

    Returns:
        Код завершения процесса.
    """
    try:
        # Конфигурация проходит через settings_manager, чтобы CLI не дублировал
        # правила построения доменных моделей.
        role_assignment, settings = load_analysis_config_json(args.config)

        # Сеанс является единственным владельцем состояния одного анализа.
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)

        session = AnalysisSession(
            source_file_path=Path(args.data),
            role_assignment=role_assignment,
            settings=settings,
            output_dir=output_dir,
        )

        # CLI вызывает тот же координатор, что и GUI и демонстрационный режим.
        runner = AnalysisRunner()
        result = runner.run(session)

        # Базовые машиночитаемые экспорты создаются при каждом успешном запуске.
        export_analysis_summary_json(result, output_dir / "analysis_summary.json")
        export_spectrum_csv(result, output_dir / "spectrum.csv")
        export_signal_csv(result, output_dir / "signal.csv")
        export_physics_summary_csv(result, output_dir / "physics_summary.csv")
        export_analysis_summary_html(result, output_dir / "analysis_summary.html")

        # Пользовательские отчёты и .vibproj создаются только по явным флагам.
        if args.export_pdf:
            path = export_report_pdf(result, output_dir / "report.pdf")
            print(f"Отчет PDF: {path}")

        if args.export_html:
            path = export_report_html(result, output_dir / "report.html")
            print(f"Отчет HTML: {path}")

        if args.save_project:
            path = save_current_session(session, output_dir / "project.vibproj")
            print(f"Проект сохранен: {path}")

        # Краткая сводка остаётся человекочитаемой и не заменяет файлы экспорта.
        _print_summary(result, output_dir)
        return 0

    except IVAError as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        if exc.recovery_hint:
            print(f"Как исправить: {exc.recovery_hint}", file=sys.stderr)
        if args.debug:
            traceback.print_exc(file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Непредвиденная ошибка: {exc}", file=sys.stderr)
        if args.debug:
            traceback.print_exc(file=sys.stderr)
        return 2


def _run_demo(args: argparse.Namespace) -> int:
    """Выполнить ``demo`` через тот же конвейер, что и пользовательский файл."""
    try:
        if args.list_scenarios:
            print("Доступные демонстрационные сценарии:")
            for scenario in list_available_demo_scenarios():
                print(f"  {scenario.key}: {scenario.title_ru}")
                print(f"    {scenario.description_ru}")
            return 0

        output_dir = Path(args.output or f"out/cli-runs/demo_{args.scenario}")
        output_dir.mkdir(parents=True, exist_ok=True)
        session = create_demo_session(args.scenario, output_dir / "demo-data")
        result = AnalysisRunner().run(session)

        print("Используется демонстрационный синтетический сигнал")
        print(f"Сценарий: {session.demo_title}")

        export_analysis_summary_json(result, output_dir / "analysis_summary.json")
        export_spectrum_csv(result, output_dir / "spectrum.csv")
        export_signal_csv(result, output_dir / "signal.csv")
        export_physics_summary_csv(result, output_dir / "physics_summary.csv")
        export_analysis_summary_html(result, output_dir / "analysis_summary.html")

        if args.export_pdf:
            path = export_report_pdf(result, output_dir / "report.pdf")
            print(f"Отчет PDF: {path}")
        if args.export_html:
            path = export_report_html(result, output_dir / "report.html")
            print(f"Отчет HTML: {path}")
        if args.save_project:
            path = save_current_session(session, output_dir / "project.vibproj")
            print(f"Проект сохранен: {path}")

        _print_summary(result, output_dir)
        return 0
    except IVAError as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        if exc.recovery_hint:
            print(f"Как исправить: {exc.recovery_hint}", file=sys.stderr)
        if args.debug:
            traceback.print_exc(file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Непредвиденная ошибка: {exc}", file=sys.stderr)
        if args.debug:
            traceback.print_exc(file=sys.stderr)
        return 2


def _print_summary(result, output_dir: Path) -> None:  # type: ignore[no-untyped-def]
    """Вывести краткую русскую сводку анализа в stdout."""
    print("=== Анализ IVA завершен ===")
    print(f"Папка результатов: {output_dir}")

    if result.spectrum is not None and result.spectrum.dominant_peak is not None:
        print(f"Доминирующий пик: {result.spectrum.dominant_peak.frequency_hz:.2f} Hz")
    else:
        print("Доминирующий пик: не обнаружен")

    if result.spectrum is not None:
        print(f"Общий RMS: {result.spectrum.rms_total:.6g}")

    if result.physics is not None:
        print(f"Число Рейнольдса: {result.physics.reynolds_number:.3e}")
        print(f"Число Струхаля: {result.physics.strouhal_number:.4f}")
        print(
            "Расчетная частота срыва: " f"{result.physics.calculated_shedding_frequency_hz:.2f} Hz"
        )
        if result.physics.velocity_ratio is not None:
            print(f"Приведенная скорость (Vr): {result.physics.velocity_ratio:.4f}")
    else:
        print("Физика: расчет не выполнен (параметры потока не заданы)")

    if result.risk is not None:
        risk = _RISK_LABELS.get(str(result.risk.risk_level), str(result.risk.risk_level))
        print(f"Уровень риска: {risk}")
    else:
        print("Уровень риска: не оценен")

    if result.warnings:
        print(f"Предупреждения ({len(result.warnings)}):")
        for w in result.warnings:
            print(f"  - {w}")


if __name__ == "__main__":
    raise SystemExit(main())
