"""Minimal static HTML summary writer for analysis results.

Produces a self-contained HTML file with no external assets, no JavaScript,
and no charts — purely informational text and tables.  All user-supplied
content is escaped with :func:`html.escape` to prevent injection.

Architecture rule: no numerical calculations here — only serialisation.
"""

from __future__ import annotations

import html
import logging
from pathlib import Path

from iva.core.models.analysis_result import AnalysisResult
from iva.core.models.exceptions import ExportError
from iva.infrastructure.reporting.report_strings_ru import (
    PEAK_INTERPRETATION_LABELS,
    RISK_LABELS,
    display_label,
)

logger = logging.getLogger(__name__)

__all__ = ["export_analysis_summary_html"]


def export_analysis_summary_html(result: AnalysisResult, output_path: str | Path) -> Path:
    """Write a minimal static HTML summary of *result* to *output_path*.

    The file is self-contained (no external CSS or JS) and opens correctly in
    any modern browser without an internet connection.

    Args:
        result: Completed analysis result.
        output_path: Destination file path (created if necessary).

    Returns:
        The resolved output path.

    Raises:
        ExportError: If the file cannot be written.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    content = _render_html(result)

    try:
        with open(output_path, "w", encoding="utf-8") as fh:
            fh.write(content)
    except OSError as exc:
        raise ExportError(
            user_message=f"Не удалось записать сводку HTML в файл '{output_path.name}'.",
            technical_details=str(exc),
        ) from exc

    logger.info("export_analysis_summary_html: written to '%s'", output_path.name)
    return output_path


# ---------------------------------------------------------------------------
# Internal rendering
# ---------------------------------------------------------------------------


def _e(text: str) -> str:
    """HTML-escape *text*."""
    return html.escape(str(text))


def _render_html(result: AnalysisResult) -> str:
    """Build the full HTML document string."""
    source_name = _e(result.source_file_path.name)
    completed = _e(result.completed_at.strftime("%Y-%m-%d %H:%M:%S UTC"))
    session_id = _e(result.session_id)
    md5 = _e(result.source_file_md5)

    # ---- spectrum block ---------------------------------------------------
    spectrum_rows = ""
    if result.spectrum is not None:
        sp = result.spectrum
        rms_band = f"{sp.rms_in_band:.4e}" if sp.rms_in_band is not None else "—"
        dominant_info = "—"
        if sp.dominant_peak is not None:
            dp = sp.dominant_peak
            dominant_info = (
                f"{dp.frequency_hz:.2f} Hz "
                f"(амплитуда {dp.amplitude:.4e}, "
                f"ширина {dp.width_hz_3db:.2f} Hz, "
                f"{_e(display_label(PEAK_INTERPRETATION_LABELS, dp.interpretation))})"
            )
        spectrum_rows = f"""
        <tr><th>Доминирующий пик</th><td>{dominant_info}</td></tr>
        <tr><th>Количество пиков</th><td>{len(sp.all_peaks)}</td></tr>
        <tr><th>Общий RMS</th><td>{sp.rms_total:.4e}</td></tr>
        <tr><th>RMS в полосе</th><td>{rms_band}</td></tr>
        <tr><th>Частотные точки</th><td>{len(sp.frequencies)}</td></tr>
"""
    else:
        spectrum_rows = "<tr><td colspan='2'>Спектральный анализ недоступен.</td></tr>"

    # ---- peaks table ------------------------------------------------------
    peaks_rows = ""
    if result.spectrum is not None and result.spectrum.all_peaks:
        for pk in result.spectrum.all_peaks:
            peaks_rows += (
                f"<tr>"
                f"<td>{pk.frequency_hz:.2f}</td>"
                f"<td>{pk.amplitude:.4e}</td>"
                f"<td>{pk.width_hz_3db:.2f}</td>"
                f"<td>{_e(display_label(PEAK_INTERPRETATION_LABELS, pk.interpretation))}</td>"
                f"<td>{pk.confidence:.2f}</td>"
                f"</tr>\n"
            )

    # ---- physics block ----------------------------------------------------
    physics_rows = ""
    if result.physics is not None:
        ph = result.physics
        vr_txt = f"{ph.velocity_ratio:.4f}" if ph.velocity_ratio is not None else "—"
        fr_txt = f"{ph.frequency_ratio:.4f}" if ph.frequency_ratio is not None else "—"
        fs_txt = f"{ph.calculated_shedding_frequency_hz:.4f}"
        physics_rows = f"""
        <tr><th>Число Рейнольдса (Re)</th><td>{ph.reynolds_number:.4e}</td></tr>
        <tr><th>Число Струхаля (St)</th><td>{ph.strouhal_number:.6f}</td></tr>
        <tr><th>Частота срыва (fs)</th><td>{fs_txt} Hz</td></tr>
        <tr><th>Приведенная скорость (Vr)</th><td>{vr_txt}</td></tr>
        <tr><th>Отношение частот (fs/fn)</th><td>{fr_txt}</td></tr>
        <tr><th>Кинематическая вязкость (ν)</th><td>{ph.kinematic_viscosity_m2s:.4e} m²/s</td></tr>
"""
    else:
        physics_rows = (
            "<tr><td colspan='2'>Расчет не выполнен: параметры потока не заданы.</td></tr>"
        )

    # ---- risk block -------------------------------------------------------
    risk_block = ""
    if result.risk is not None:
        risk = result.risk
        risk_level_str = _e(display_label(RISK_LABELS, risk.risk_level))
        recommendation = _e(risk.recommendation_text)
        deviation = f"{risk.dominant_frequency_deviation:.4f}"
        risk_block = f"""
        <h2>Оценка риска</h2>
        <table>
          <tr><th>Уровень риска</th><td><strong>{risk_level_str}</strong></td></tr>
          <tr><th>Отклонение частоты |fs/fn − 1|</th><td>{deviation}</td></tr>
          <tr><th>Рекомендация</th><td>{recommendation}</td></tr>
        </table>
"""
    else:
        risk_block = "<h2>Оценка риска</h2><p>Не выполнена: физические параметры недоступны.</p>"

    # ---- warnings block ---------------------------------------------------
    warnings_block = ""
    if result.warnings:
        items = "".join(f"<li>{_e(w)}</li>" for w in result.warnings)
        warnings_block = f"<h2>Предупреждения</h2><ul>{items}</ul>"

    # ---- peaks section ----------------------------------------------------
    peaks_section = ""
    if peaks_rows:
        peaks_section = f"""
        <h2>Обнаруженные пики</h2>
        <table>
          <thead>
            <tr>
              <th>Частота (Hz)</th>
              <th>Амплитуда</th>
              <th>Ширина -3 dB (Hz)</th>
              <th>Интерпретация</th>
              <th>Достоверность</th>
            </tr>
          </thead>
          <tbody>
{peaks_rows}
          </tbody>
        </table>
"""

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Сводка анализа IVA — {source_name}</title>
  <style>
    body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 2em auto;
            padding: 0 1em; color: #222; }}
    h1 {{ border-bottom: 2px solid #444; padding-bottom: 0.3em; }}
    h2 {{ border-bottom: 1px solid #ccc; margin-top: 1.5em; }}
    table {{ border-collapse: collapse; width: 100%; margin: 0.5em 0; }}
    th, td {{ border: 1px solid #ccc; padding: 0.4em 0.8em; text-align: left; }}
    th {{ background: #f5f5f5; width: 220px; }}
    ul {{ padding-left: 1.5em; }}
    .meta {{ color: #666; font-size: 0.9em; }}
  </style>
</head>
<body>
  <h1>Сводка анализа IVA</h1>
  <p class="meta">
    Исходный файл: <strong>{source_name}</strong><br>
    Завершено: {completed}<br>
    ID сеанса: {session_id}<br>
    MD5: {md5}
  </p>

  <h2>Спектральный анализ</h2>
  <table>
{spectrum_rows}
  </table>

{peaks_section}

  <h2>Физические параметры</h2>
  <table>
{physics_rows}
  </table>

{risk_block}

{warnings_block}
</body>
</html>
"""
