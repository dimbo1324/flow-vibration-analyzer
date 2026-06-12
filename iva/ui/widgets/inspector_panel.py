"""Right-side inspector content for current session and analysis results."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt  # type: ignore[import-untyped]
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget  # type: ignore[import-untyped]

from iva.ui.strings_ru import RISK_LABELS, display_label
from iva.ui.styles.theme import COLOR_MUTED, COLOR_TEXT, SPACING_MD, SPACING_SM

if TYPE_CHECKING:
    from iva.core.models.analysis_result import AnalysisResult

__all__ = ["InspectorPanel"]


class InspectorPanel(QWidget):
    """Present compact session context without owning application state."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING_MD, SPACING_MD, SPACING_MD, SPACING_MD)
        layout.setSpacing(SPACING_SM)

        title = QLabel("ТЕКУЩИЙ СЕАНС")
        title.setStyleSheet(f"color: {COLOR_MUTED}; font-weight: 700;")
        layout.addWidget(title)

        self._text = QLabel()
        self._text.setObjectName("inspectorText")
        self._text.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self._text.setWordWrap(True)
        self._text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._text.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 10pt;")
        layout.addWidget(self._text)
        layout.addStretch()
        self.clear()

    def update_result(
        self,
        result: AnalysisResult,
        project_path: Path | None = None,
    ) -> None:
        """Render source, project, key metrics, risk, and warning count."""
        lines = [f"Источник: {result.source_file_path.name}"]
        if result.is_demo:
            lines.append("Режим: демонстрационные синтетические данные")
            if result.demo_title:
                lines.append(f"Сценарий: {result.demo_title}")
        else:
            lines.append("Режим: измеренные данные")
        lines.append(
            f"Проект: {project_path.name}" if project_path is not None else "Проект: не сохранён"
        )
        lines.append("")

        if result.spectrum is not None:
            if result.spectrum.dominant_peak is not None:
                peak_frequency = result.spectrum.dominant_peak.frequency_hz
                lines.append(f"Доминирующий пик: {peak_frequency:.2f} Hz")
            lines.append(f"RMS: {result.spectrum.rms_total:.4g}")
        if result.physics is not None:
            lines.append(f"Re: {result.physics.reynolds_number:.3e}")
            lines.append(f"St: {result.physics.strouhal_number:.4f}")
        if result.risk is not None:
            lines.append(f"Риск: {display_label(RISK_LABELS, result.risk.risk_level)}")
        lines.append(f"Предупреждения: {len(result.warnings)}")
        self._text.setText("\n".join(lines))

    def clear(self) -> None:
        """Show the inspector empty state."""
        self._text.setText(
            "Результатов анализа пока нет\n\nОткройте файл или запустите демо-анализ"
        )
