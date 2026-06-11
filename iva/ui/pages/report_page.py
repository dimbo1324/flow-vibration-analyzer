"""Page 07 — Report: export controls and analysis summary."""

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

from iva.ui.styles.theme import (
    COLOR_MUTED,
    COLOR_TEXT,
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

        title = QLabel("07 — Report")
        title.setStyleSheet(
            f"font-size: {FONT_SIZE_TITLE}pt; font-weight: bold; color: {COLOR_TEXT};"
        )
        layout.addWidget(title)

        subtitle = QLabel("Export analysis results")
        subtitle.setStyleSheet(f"color: {COLOR_MUTED}; font-size: 11pt;")
        layout.addWidget(subtitle)

        # Export buttons row
        btn_box = QGroupBox("Export")
        btn_layout = QHBoxLayout(btn_box)

        self._pdf_btn = QPushButton("Export PDF (Stage 9)")
        self._pdf_btn.setEnabled(False)
        self._pdf_btn.setToolTip("PDF report generation is available in Stage 9")

        self._csv_spectrum_btn = QPushButton("Export Spectrum CSV")
        self._csv_spectrum_btn.setEnabled(False)
        self._csv_spectrum_btn.clicked.connect(self._on_export_spectrum_csv)

        self._csv_signal_btn = QPushButton("Export Signal CSV")
        self._csv_signal_btn.setEnabled(False)
        self._csv_signal_btn.clicked.connect(self._on_export_signal_csv)

        self._csv_physics_btn = QPushButton("Export Physics CSV")
        self._csv_physics_btn.setEnabled(False)
        self._csv_physics_btn.clicked.connect(self._on_export_physics_csv)

        btn_layout.addWidget(self._pdf_btn)
        btn_layout.addWidget(self._csv_spectrum_btn)
        btn_layout.addWidget(self._csv_signal_btn)
        btn_layout.addWidget(self._csv_physics_btn)
        btn_layout.addStretch()
        layout.addWidget(btn_box)

        # Summary text area
        summary_box = QGroupBox("Analysis Summary")
        summary_layout = QVBoxLayout(summary_box)
        self._summary_text = QTextEdit()
        self._summary_text.setReadOnly(True)
        self._summary_text.setPlaceholderText(
            "No analysis result yet.\nRun an analysis to see the summary here."
        )
        self._summary_text.setMinimumHeight(300)
        summary_layout.addWidget(self._summary_text)
        layout.addWidget(summary_box)

        self._status_label = QLabel("")
        self._status_label.setStyleSheet(f"color: {COLOR_MUTED}; font-size: 10pt;")
        layout.addWidget(self._status_label)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_export_spectrum_csv(self) -> None:
        if self._result is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Spectrum CSV", "spectrum.csv", "CSV Files (*.csv)"
        )
        if not path:
            return
        try:
            from iva.infrastructure.writers.csv_export_writer import export_spectrum_csv

            export_spectrum_csv(self._result, path)
            self._status_label.setText(f"Exported: {Path(path).name}")
        except Exception as exc:  # noqa: BLE001
            self._status_label.setText(f"Export failed: {exc}")

    def _on_export_signal_csv(self) -> None:
        if self._result is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Signal CSV", "signal.csv", "CSV Files (*.csv)"
        )
        if not path:
            return
        try:
            from iva.infrastructure.writers.csv_export_writer import export_signal_csv

            export_signal_csv(self._result, path)
            self._status_label.setText(f"Exported: {Path(path).name}")
        except Exception as exc:  # noqa: BLE001
            self._status_label.setText(f"Export failed: {exc}")

    def _on_export_physics_csv(self) -> None:
        if self._result is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Physics CSV", "physics_summary.csv", "CSV Files (*.csv)"
        )
        if not path:
            return
        try:
            from iva.infrastructure.writers.csv_export_writer import export_physics_summary_csv

            export_physics_summary_csv(self._result, path)
            self._status_label.setText(f"Exported: {Path(path).name}")
        except Exception as exc:  # noqa: BLE001
            self._status_label.setText(f"Export failed: {exc}")

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def on_analysis_completed(self, result: AnalysisResult) -> None:
        """Populate summary and enable export buttons."""
        self._result = result

        lines: list[str] = []
        lines.append(f"Session ID:    {result.session_id}")
        lines.append(f"Completed at:  {result.completed_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        lines.append(f"Source file:   {result.source_file_path.name}")
        lines.append(f"MD5:           {result.source_file_md5}")
        lines.append("")

        if result.spectrum:
            sp = result.spectrum
            lines.append(f"RMS total:     {sp.rms_total:.6f}")
            if sp.dominant_peak:
                pk = sp.dominant_peak
                lines.append(
                    f"Dominant peak: {pk.frequency_hz:.3f} Hz  (amplitude: {pk.amplitude:.4g})"
                )
            lines.append(f"Peaks found:   {len(sp.all_peaks)}")

        if result.physics:
            ph = result.physics
            lines.append("")
            lines.append(f"Reynolds number:        {ph.reynolds_number:.4e}")
            lines.append(f"Strouhal number:        {ph.strouhal_number:.6f}")
            lines.append(f"Shedding frequency:     {ph.calculated_shedding_frequency_hz:.4f} Hz")
            if ph.velocity_ratio is not None:
                lines.append(f"Velocity ratio Vr:      {ph.velocity_ratio:.4f}")
            if ph.frequency_ratio is not None:
                lines.append(f"Frequency ratio fs/fn:  {ph.frequency_ratio:.4f}")

        if result.risk:
            lines.append("")
            lines.append(f"Risk level:    {result.risk.risk_level}")
            lines.append(f"Deviation:     {result.risk.dominant_frequency_deviation:.4f}")
            lines.append("")
            lines.append("Recommendation:")
            lines.append(result.risk.recommendation_text)

        if result.warnings:
            lines.append("")
            lines.append("Warnings:")
            for w in result.warnings:
                lines.append(f"  • {w}")

        self._summary_text.setText("\n".join(lines))

        # Enable relevant export buttons
        self._csv_spectrum_btn.setEnabled(result.spectrum is not None)
        self._csv_signal_btn.setEnabled(result.processed_data is not None)
        self._csv_physics_btn.setEnabled(True)

    def clear(self) -> None:
        """Reset the page."""
        self._result = None
        self._summary_text.clear()
        for btn in (
            self._csv_spectrum_btn,
            self._csv_signal_btn,
            self._csv_physics_btn,
        ):
            btn.setEnabled(False)
        self._status_label.setText("")
