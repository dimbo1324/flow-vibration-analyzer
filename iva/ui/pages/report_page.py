"""Page 07 — Report: export controls and analysis summary (Stage 9)."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtWidgets import (  # type: ignore[import-untyped]
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from iva.ui.strings_ru import RISK_LABELS, display_label, tr
from iva.ui.styles.theme import (
    COLOR_GOOD,
    COLOR_MUTED,
    COLOR_TEXT,
    COLOR_WARN,
    FONT_SIZE_TITLE,
    SPACING_MD,
)

if TYPE_CHECKING:
    from iva.core.models.analysis_result import AnalysisResult

__all__ = ["ReportPage"]


class ReportPage(QWidget):
    """Report page: analysis summary text and export buttons."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._result: AnalysisResult | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_MD, SPACING_MD, SPACING_MD, SPACING_MD)
        layout.setSpacing(SPACING_MD)

        title = QLabel(tr("07 — Report"))
        title.setStyleSheet(
            f"font-size: {FONT_SIZE_TITLE}pt; font-weight: bold; color: {COLOR_TEXT};"
        )
        layout.addWidget(title)

        subtitle = QLabel(tr("Export analysis results as PDF, HTML, JSON or CSV"))
        subtitle.setStyleSheet(f"color: {COLOR_MUTED}; font-size: 11pt;")
        layout.addWidget(subtitle)

        # Readiness indicator
        self._readiness_label = QLabel(tr("No analysis result available."))
        self._readiness_label.setStyleSheet(f"color: {COLOR_WARN}; font-size: 11pt;")
        layout.addWidget(self._readiness_label)

        self._demo_marker = QLabel(
            "Демонстрационные синтетические данные. Данные сгенерированы программно "
            "и предназначены только для демонстрации работы приложения."
        )
        self._demo_marker.setObjectName("reportDemoMarker")
        self._demo_marker.setWordWrap(True)
        self._demo_marker.setStyleSheet(f"color: {COLOR_WARN}; font-weight: bold;")
        self._demo_marker.setVisible(False)
        layout.addWidget(self._demo_marker)

        # Export buttons row
        btn_box = QGroupBox(tr("Export"))
        btn_layout = QHBoxLayout(btn_box)

        self._pdf_btn = QPushButton(tr("Export PDF"))
        self._pdf_btn.setEnabled(False)
        self._pdf_btn.setToolTip("Экспортировать полный отчет анализа в PDF")
        self._pdf_btn.clicked.connect(self._on_export_pdf)

        self._html_btn = QPushButton(tr("Export HTML"))
        self._html_btn.setEnabled(False)
        self._html_btn.setToolTip("Экспортировать автономный отчет HTML")
        self._html_btn.clicked.connect(self._on_export_html)

        self._json_btn = QPushButton(tr("Export JSON Summary"))
        self._json_btn.setEnabled(False)
        self._json_btn.setToolTip("Экспортировать машиночитаемую сводку JSON")
        self._json_btn.clicked.connect(self._on_export_json)

        self._csv_pkg_btn = QPushButton(tr("Export CSV Package"))
        self._csv_pkg_btn.setEnabled(False)
        self._csv_pkg_btn.setToolTip(
            "Экспортировать CSV-файлы спектра, сигнала и физических параметров"
        )
        self._csv_pkg_btn.clicked.connect(self._on_export_csv_package)

        self._csv_spectrum_btn = QPushButton(tr("Spectrum CSV"))
        self._csv_spectrum_btn.setEnabled(False)
        self._csv_spectrum_btn.clicked.connect(self._on_export_spectrum_csv)

        self._csv_signal_btn = QPushButton(tr("Signal CSV"))
        self._csv_signal_btn.setEnabled(False)
        self._csv_signal_btn.clicked.connect(self._on_export_signal_csv)

        self._csv_physics_btn = QPushButton(tr("Physics CSV"))
        self._csv_physics_btn.setEnabled(False)
        self._csv_physics_btn.clicked.connect(self._on_export_physics_csv)

        btn_layout.addWidget(self._pdf_btn)
        btn_layout.addWidget(self._html_btn)
        btn_layout.addWidget(self._json_btn)
        btn_layout.addWidget(self._csv_pkg_btn)
        btn_layout.addWidget(self._csv_spectrum_btn)
        btn_layout.addWidget(self._csv_signal_btn)
        btn_layout.addWidget(self._csv_physics_btn)
        btn_layout.addStretch()
        layout.addWidget(btn_box)

        # Summary text area
        summary_box = QGroupBox(tr("Analysis Summary"))
        summary_layout = QVBoxLayout(summary_box)
        self._summary_text = QTextEdit()
        self._summary_text.setReadOnly(True)
        self._summary_text.setPlaceholderText(
            "Результат анализа пока отсутствует.\n" "Запустите анализ, чтобы увидеть сводку."
        )
        self._summary_text.setMinimumHeight(300)
        summary_layout.addWidget(self._summary_text)
        layout.addWidget(summary_box)

        self._status_label = QLabel("")
        self._status_label.setStyleSheet(f"color: {COLOR_MUTED}; font-size: 10pt;")
        layout.addWidget(self._status_label)

    # ------------------------------------------------------------------
    # Export slots
    # ------------------------------------------------------------------

    def _on_export_pdf(self) -> None:
        if self._result is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Экспорт отчета PDF", "report.pdf", "Файлы PDF (*.pdf)"
        )
        if not path:
            return
        try:
            from iva.app.report_service import export_report_pdf

            export_report_pdf(self._result, path)
            self._set_status(f"PDF экспортирован: {Path(path).name}", ok=True)
        except Exception as exc:  # noqa: BLE001
            self._set_status(f"Ошибка экспорта PDF: {exc}", ok=False)

    def _on_export_html(self) -> None:
        if self._result is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Экспорт отчета HTML", "report.html", "Файлы HTML (*.html)"
        )
        if not path:
            return
        try:
            from iva.app.report_service import export_report_html

            export_report_html(self._result, path)
            self._set_status(f"HTML экспортирован: {Path(path).name}", ok=True)
        except Exception as exc:  # noqa: BLE001
            self._set_status(f"Ошибка экспорта HTML: {exc}", ok=False)

    def _on_export_json(self) -> None:
        if self._result is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, tr("Export JSON Summary"), "analysis_summary.json", "Файлы JSON (*.json)"
        )
        if not path:
            return
        try:
            from iva.app.report_service import export_report_json

            export_report_json(self._result, path)
            self._set_status(f"JSON экспортирован: {Path(path).name}", ok=True)
        except Exception as exc:  # noqa: BLE001
            self._set_status(f"Ошибка экспорта JSON: {exc}", ok=False)

    def _on_export_csv_package(self) -> None:
        if self._result is None:
            return
        output_dir = QFileDialog.getExistingDirectory(
            self, tr("Select Output Directory for CSV Package")
        )
        if not output_dir:
            return
        try:
            from iva.app.report_service import export_report_bundle

            written = export_report_bundle(self._result, output_dir)
            csv_count = sum(1 for k in written if "csv" in k)
            self._set_status(
                f"Комплект CSV экспортирован: файлов {csv_count}; "
                f"папка {Path(output_dir).name}",
                ok=True,
            )
        except Exception as exc:  # noqa: BLE001
            self._set_status(f"Ошибка экспорта комплекта CSV: {exc}", ok=False)

    def _on_export_spectrum_csv(self) -> None:
        if self._result is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Экспорт CSV спектра", "spectrum.csv", "Файлы CSV (*.csv)"
        )
        if not path:
            return
        try:
            from iva.app.report_service import export_report_spectrum_csv

            export_report_spectrum_csv(self._result, path)
            self._set_status(f"Экспортирован файл: {Path(path).name}", ok=True)
        except Exception as exc:  # noqa: BLE001
            self._set_status(f"Ошибка экспорта: {exc}", ok=False)

    def _on_export_signal_csv(self) -> None:
        if self._result is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Экспорт CSV сигнала", "signal.csv", "Файлы CSV (*.csv)"
        )
        if not path:
            return
        try:
            from iva.app.report_service import export_report_signal_csv

            export_report_signal_csv(self._result, path)
            self._set_status(f"Экспортирован файл: {Path(path).name}", ok=True)
        except Exception as exc:  # noqa: BLE001
            self._set_status(f"Ошибка экспорта: {exc}", ok=False)

    def _on_export_physics_csv(self) -> None:
        if self._result is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт CSV физических параметров",
            "physics_summary.csv",
            "Файлы CSV (*.csv)",
        )
        if not path:
            return
        try:
            from iva.app.report_service import export_report_physics_csv

            export_report_physics_csv(self._result, path)
            self._set_status(f"Экспортирован файл: {Path(path).name}", ok=True)
        except Exception as exc:  # noqa: BLE001
            self._set_status(f"Ошибка экспорта: {exc}", ok=False)

    def _set_status(self, message: str, ok: bool = True) -> None:
        colour = COLOR_GOOD if ok else COLOR_WARN
        self._status_label.setStyleSheet(f"color: {colour}; font-size: 10pt;")
        self._status_label.setText(message)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def on_analysis_completed(self, result: AnalysisResult) -> None:
        """Populate summary and enable export buttons."""
        self._result = result
        self._demo_marker.setVisible(result.is_demo)

        # Update readiness indicator
        self._readiness_label.setText(
            f"Результат готов — сеанс {result.session_id[:8]}… | "
            f"Источник: {result.source_file_path.name} | "
            f"Предупреждения: {len(result.warnings)}"
        )
        self._readiness_label.setStyleSheet(f"color: {COLOR_GOOD}; font-size: 11pt;")

        lines: list[str] = []
        if result.is_demo:
            lines.append("ДЕМОНСТРАЦИОННЫЕ СИНТЕТИЧЕСКИЕ ДАННЫЕ")
            if result.demo_title:
                lines.append(f"Сценарий:      {result.demo_title}")
            lines.append("Данные сгенерированы программно и предназначены только для демонстрации.")
            lines.append("")
        lines.append(f"ID сеанса:     {result.session_id}")
        lines.append(f"Завершено:     {result.completed_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        lines.append(f"Исходный файл: {result.source_file_path.name}")
        lines.append(f"MD5:           {result.source_file_md5}")
        lines.append("")

        if result.spectrum:
            sp = result.spectrum
            lines.append(f"Общий RMS:     {sp.rms_total:.6f}")
            if sp.dominant_peak:
                pk = sp.dominant_peak
                lines.append(
                    f"Доминирующий пик: {pk.frequency_hz:.3f} Hz  "
                    f"(амплитуда: {pk.amplitude:.4g})"
                )
            lines.append(f"Найдено пиков: {len(sp.all_peaks)}")

        if result.physics:
            ph = result.physics
            lines.append("")
            lines.append(f"Число Рейнольдса:       {ph.reynolds_number:.4e}")
            lines.append(f"Число Струхаля:         {ph.strouhal_number:.6f}")
            lines.append(f"Частота срыва:          {ph.calculated_shedding_frequency_hz:.4f} Hz")
            if ph.velocity_ratio is not None:
                lines.append(f"Приведенная скорость Vr:{ph.velocity_ratio:>10.4f}")
            if ph.frequency_ratio is not None:
                lines.append(f"Отношение частот fs/fn: {ph.frequency_ratio:.4f}")

        if result.risk:
            lines.append("")
            lines.append(f"Уровень риска: {display_label(RISK_LABELS, result.risk.risk_level)}")
            lines.append(f"Отклонение:    {result.risk.dominant_frequency_deviation:.4f}")
            lines.append("")
            lines.append("Рекомендация:")
            lines.append(result.risk.recommendation_text)

        if result.warnings:
            lines.append("")
            lines.append("Предупреждения:")
            for w in result.warnings:
                lines.append(f"  • {w}")

        self._summary_text.setText("\n".join(lines))

        # Enable export buttons
        has_spectrum = result.spectrum is not None
        has_processed = result.processed_data is not None

        self._pdf_btn.setEnabled(True)
        self._html_btn.setEnabled(True)
        self._json_btn.setEnabled(True)
        self._csv_pkg_btn.setEnabled(True)
        self._csv_spectrum_btn.setEnabled(has_spectrum)
        self._csv_signal_btn.setEnabled(has_processed)
        self._csv_physics_btn.setEnabled(True)

    def clear(self) -> None:
        """Reset the page."""
        self._result = None
        self._summary_text.clear()
        self._readiness_label.setText(tr("No analysis result available."))
        self._readiness_label.setStyleSheet(f"color: {COLOR_WARN}; font-size: 11pt;")
        for btn in (
            self._pdf_btn,
            self._html_btn,
            self._json_btn,
            self._csv_pkg_btn,
            self._csv_spectrum_btn,
            self._csv_signal_btn,
            self._csv_physics_btn,
        ):
            btn.setEnabled(False)
        self._status_label.setText("")
        self._demo_marker.setVisible(False)
