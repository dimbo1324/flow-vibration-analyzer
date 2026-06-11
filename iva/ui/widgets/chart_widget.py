"""ChartWidget — matplotlib canvas embedded in a Qt widget.

Falls back gracefully to a placeholder label if matplotlib is not available.

Stage 9 additions:
- enable_cursor_inspection() — show mouse coordinates in a label.
- reset_view() — reset axis limits to auto.
- export_png() — save figure as PNG.
- NavigationToolbar2QT (zoom/pan) added to layout (graceful fallback if unavailable).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt  # type: ignore[import-untyped]
from PySide6.QtWidgets import (  # type: ignore[import-untyped]
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from iva.core.models.exceptions import ExportError
from iva.ui.strings_ru import tr
from iva.ui.styles.theme import (
    COLOR_ACCENT,
    COLOR_BAD,
    COLOR_BG,
    COLOR_MUTED,
    COLOR_SURFACE,
    COLOR_TEXT,
    COLOR_WARN,
)

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray

    from iva.core.models.analysis_result import SpectralPeak

try:
    import matplotlib  # type: ignore[import-untyped]

    # Use Agg when in offscreen mode to avoid GL issues, otherwise QtAgg.
    if os.environ.get("MPLBACKEND") == "Agg" or os.environ.get("QT_QPA_PLATFORM") == "offscreen":
        matplotlib.use("Agg")
    else:
        matplotlib.use("QtAgg")

    from matplotlib.backends.backend_qtagg import (  # type: ignore[import-untyped]
        FigureCanvasQTAgg as FigureCanvas,
    )
    from matplotlib.figure import Figure  # type: ignore[import-untyped]

    _MATPLOTLIB_AVAILABLE = True
except ImportError:
    _MATPLOTLIB_AVAILABLE = False

# Try to import NavigationToolbar — only available with QtAgg backend
try:
    from matplotlib.backends.backend_qt import (  # type: ignore[import-untyped]
        NavigationToolbar2QT,
    )

    _TOOLBAR_AVAILABLE = True
except ImportError:
    try:
        from matplotlib.backends.backend_qtagg import (  # type: ignore[import-untyped]
            NavigationToolbar2QT,
        )

        _TOOLBAR_AVAILABLE = True
    except ImportError:
        _TOOLBAR_AVAILABLE = False

__all__ = ["ChartWidget"]


def _hex_to_rgb_float(hex_color: str) -> tuple[float, float, float]:
    """Convert a ``#RRGGBB`` string to a (r, g, b) tuple in [0, 1]."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4))
    return r, g, b


class ChartWidget(QWidget):
    """Matplotlib figure canvas with helper methods for IVA chart types.

    If matplotlib is unavailable (e.g. during headless testing without the
    library), a plain placeholder label is shown instead and all plotting
    methods become no-ops.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._cursor_enabled = False
        self._motion_cid: int | None = None
        self._home_xlim: tuple[float, float] | None = None
        self._home_ylim: tuple[float, float] | None = None
        self._pan_anchor: tuple[float, float, tuple[float, float], tuple[float, float]] | None = (
            None
        )
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        if _MATPLOTLIB_AVAILABLE:
            bg = _hex_to_rgb_float(COLOR_BG)
            self._fig = Figure(facecolor=bg, tight_layout=True)  # type: ignore[possibly-undefined]
            self._ax = self._fig.add_subplot(111)
            self._canvas = FigureCanvas(self._fig)  # type: ignore[possibly-undefined]
            self._canvas.setParent(self)
            self._style_axes()
            self._canvas.mpl_connect("scroll_event", self._on_scroll)
            self._canvas.mpl_connect("button_press_event", self._on_button_press)
            self._canvas.mpl_connect("button_release_event", self._on_button_release)
            self._canvas.mpl_connect("motion_notify_event", self._on_pan_motion)

            controls = QHBoxLayout()
            self._reset_button = QPushButton(tr("Reset view"))
            self._reset_button.clicked.connect(self.reset_view)
            self._png_button = QPushButton(tr("Save PNG"))
            self._png_button.clicked.connect(self._save_png_dialog)
            self._cursor_checkbox = QCheckBox(tr("Inspect cursor"))
            self._cursor_checkbox.toggled.connect(self.enable_cursor_inspection)
            controls.addWidget(self._reset_button)
            controls.addWidget(self._png_button)
            controls.addWidget(self._cursor_checkbox)
            controls.addStretch()
            layout.addLayout(controls)

            # Add NavigationToolbar if available and not in offscreen mode
            _is_offscreen = os.environ.get("QT_QPA_PLATFORM") == "offscreen"
            if _TOOLBAR_AVAILABLE and not _is_offscreen:
                try:
                    self._toolbar = NavigationToolbar2QT(self._canvas, self)  # type: ignore[possibly-undefined]
                    self._toolbar.setStyleSheet(
                        f"background: {COLOR_SURFACE}; color: {COLOR_TEXT};"
                        f" border-bottom: 1px solid #333;"
                    )
                    toolbar_labels = {
                        "Home": "Исходный вид",
                        "Back": "Назад",
                        "Forward": "Вперед",
                        "Pan": "Панорамирование",
                        "Zoom": "Масштабирование",
                        "Subplots": "Параметры областей",
                        "Customize": "Настроить график",
                        "Save": "Сохранить",
                    }
                    for action in self._toolbar.actions():
                        source = action.text().replace("&", "")
                        translated = toolbar_labels.get(source)
                        if translated:
                            action.setText(translated)
                            action.setToolTip(translated)
                    layout.addWidget(self._toolbar)
                except Exception:  # noqa: BLE001
                    pass  # toolbar is optional

            layout.addWidget(self._canvas)

            # Coordinate label below chart
            self._coord_label = QLabel("")
            self._coord_label.setStyleSheet(
                f"color: {COLOR_MUTED}; font-size: 9pt; padding: 2px 6px;"
            )
            self._coord_label.setVisible(False)
            layout.addWidget(self._coord_label)
        else:
            lbl = QLabel(tr("Chart requires matplotlib\n(pip install matplotlib)"))
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(f"color: {COLOR_MUTED}; font-size: 12pt;")
            layout.addWidget(lbl)

    def _style_axes(self) -> None:
        """Apply dark theme styling to matplotlib axes."""
        if not _MATPLOTLIB_AVAILABLE:
            return
        bg = _hex_to_rgb_float(COLOR_BG)
        self._ax.set_facecolor(bg)
        self._ax.tick_params(colors=COLOR_MUTED, labelsize=9)
        for spine in self._ax.spines.values():
            spine.set_edgecolor(COLOR_MUTED)
            spine.set_alpha(0.4)

    # ------------------------------------------------------------------
    # Stage 9 additions
    # ------------------------------------------------------------------

    def enable_cursor_inspection(self, enabled: bool = True) -> None:
        """Enable or disable cursor coordinate display on mouse motion.

        Args:
            enabled: If ``True``, connect motion events and show the
                coordinate label.  If ``False``, disconnect events.
        """
        if not _MATPLOTLIB_AVAILABLE:
            return
        if enabled:
            if self._motion_cid is None:
                self._motion_cid = self._canvas.mpl_connect(
                    "motion_notify_event", self._on_mouse_move
                )
            self._coord_label.setVisible(True)
            self._cursor_enabled = True
        else:
            if self._motion_cid is not None:
                try:
                    self._canvas.mpl_disconnect(self._motion_cid)
                except Exception:  # noqa: BLE001
                    pass
                self._motion_cid = None
            self._coord_label.setVisible(False)
            self._cursor_enabled = False

    def _on_mouse_move(self, event: object) -> None:
        """Update coordinate label on mouse motion."""
        if not hasattr(event, "xdata") or not hasattr(event, "ydata"):
            return
        x = getattr(event, "xdata", None)
        y = getattr(event, "ydata", None)
        if x is not None and y is not None:
            self._coord_label.setText(f"x={x:.4g}  y={y:.4g}")
        else:
            self._coord_label.setText("")

    def reset_view(self) -> None:
        """Reset axis limits to auto-fit the current data."""
        if not _MATPLOTLIB_AVAILABLE:
            return
        if self._home_xlim is not None and self._home_ylim is not None:
            self._ax.set_xlim(self._home_xlim)
            self._ax.set_ylim(self._home_ylim)
        else:
            self._ax.relim()
            self._ax.autoscale_view()
        self._canvas.draw_idle()

    def _capture_home_view(self) -> None:
        self._ax.relim()
        self._ax.autoscale_view()
        xlim = self._ax.get_xlim()
        ylim = self._ax.get_ylim()
        self._home_xlim = (float(xlim[0]), float(xlim[1]))
        self._home_ylim = (float(ylim[0]), float(ylim[1]))

    def _on_scroll(self, event: object) -> None:
        """Zoom around the cursor using the mouse wheel."""
        if getattr(event, "inaxes", None) is not self._ax:
            return
        x = getattr(event, "xdata", None)
        y = getattr(event, "ydata", None)
        if x is None or y is None:
            return
        scale = 0.8 if getattr(event, "button", None) == "up" else 1.25
        x0, x1 = self._ax.get_xlim()
        y0, y1 = self._ax.get_ylim()
        self._ax.set_xlim(x - (x - x0) * scale, x + (x1 - x) * scale)
        self._ax.set_ylim(y - (y - y0) * scale, y + (y1 - y) * scale)
        self._canvas.draw_idle()

    def _on_button_press(self, event: object) -> None:
        """Start panning with the middle mouse button."""
        if getattr(event, "button", None) != 2 or getattr(event, "inaxes", None) is not self._ax:
            return
        x = getattr(event, "xdata", None)
        y = getattr(event, "ydata", None)
        if x is not None and y is not None:
            self._pan_anchor = (x, y, self._ax.get_xlim(), self._ax.get_ylim())

    def _on_pan_motion(self, event: object) -> None:
        if self._pan_anchor is None or getattr(event, "inaxes", None) is not self._ax:
            return
        x = getattr(event, "xdata", None)
        y = getattr(event, "ydata", None)
        if x is None or y is None:
            return
        anchor_x, anchor_y, xlim, ylim = self._pan_anchor
        dx = x - anchor_x
        dy = y - anchor_y
        self._ax.set_xlim(xlim[0] - dx, xlim[1] - dx)
        self._ax.set_ylim(ylim[0] - dy, ylim[1] - dy)
        self._canvas.draw_idle()

    def _on_button_release(self, event: object) -> None:
        if getattr(event, "button", None) == 2:
            self._pan_anchor = None

    def export_png(self, output_path: str | Path) -> Path:
        """Save the current figure as a PNG file.

        Args:
            output_path: Destination file path.  Parent directories are
                created automatically.

        Returns:
            The resolved output :class:`~pathlib.Path`.

        Raises:
            ExportError: If matplotlib is unavailable or the file cannot
                be written.
        """
        if not _MATPLOTLIB_AVAILABLE:
            raise ExportError(
                user_message="Экспорт PNG недоступен: библиотека matplotlib не установлена.",
                technical_details="matplotlib import failed",
            )
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._fig.savefig(
                str(output_path),
                dpi=150,
                bbox_inches="tight",
                facecolor=self._fig.get_facecolor(),
            )
        except Exception as exc:
            raise ExportError(
                user_message=f"Не удалось сохранить PNG в файл '{output_path.name}'.",
                technical_details=str(exc),
            ) from exc
        return output_path

    def _save_png_dialog(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, tr("Save Chart as PNG"), "chart.png", tr("PNG Images (*.png)")
        )
        if path:
            self.export_png(path)

    # ------------------------------------------------------------------
    # Public plotting API
    # ------------------------------------------------------------------

    def plot_signal(
        self,
        time_array: NDArray[np.float64],
        signal_array: NDArray[np.float64],
        label: str = "Сигнал",
    ) -> None:
        """Plot a time-domain signal."""
        if not _MATPLOTLIB_AVAILABLE:
            return
        self._ax.clear()
        self._ax.plot(time_array, signal_array, color=COLOR_ACCENT, linewidth=0.8, label=label)
        self._ax.set_xlabel(tr("Time (s)"), color=COLOR_MUTED, fontsize=9)
        self._ax.set_ylabel(tr("Amplitude"), color=COLOR_MUTED, fontsize=9)
        self._ax.legend(
            facecolor=COLOR_SURFACE,
            labelcolor=COLOR_TEXT,
            fontsize=8,
            framealpha=0.8,
        )
        self._style_axes()
        self._capture_home_view()
        self._canvas.draw()

    def plot_two_signals(
        self,
        time_array: NDArray[np.float64],
        signal_a: NDArray[np.float64],
        signal_b: NDArray[np.float64],
        label_a: str = "Очищенный",
        label_b: str = "Отфильтрованный",
    ) -> None:
        """Plot two overlaid time-domain signals."""
        if not _MATPLOTLIB_AVAILABLE:
            return
        self._ax.clear()
        self._ax.plot(time_array, signal_a, color=COLOR_MUTED, linewidth=0.6, label=label_a)
        self._ax.plot(time_array, signal_b, color=COLOR_ACCENT, linewidth=0.8, label=label_b)
        self._ax.set_xlabel(tr("Time (s)"), color=COLOR_MUTED, fontsize=9)
        self._ax.set_ylabel(tr("Amplitude"), color=COLOR_MUTED, fontsize=9)
        self._ax.legend(
            facecolor=COLOR_SURFACE,
            labelcolor=COLOR_TEXT,
            fontsize=8,
            framealpha=0.8,
        )
        self._style_axes()
        self._capture_home_view()
        self._canvas.draw()

    def plot_psd(
        self,
        frequencies: NDArray[np.float64],
        psd_values: NDArray[np.float64],
        peaks: list[SpectralPeak] | None = None,
    ) -> None:
        """Plot power spectral density with optional peak markers."""
        if not _MATPLOTLIB_AVAILABLE:
            return
        self._ax.clear()
        self._ax.semilogy(frequencies, psd_values, color=COLOR_ACCENT, linewidth=0.8)
        if peaks:
            for pk in peaks:
                self._ax.axvline(
                    x=pk.frequency_hz,
                    color=COLOR_BAD,
                    alpha=0.75,
                    linewidth=1.2,
                    linestyle="--",
                    label=f"{pk.frequency_hz:.1f} Hz",
                )
            self._ax.legend(
                facecolor=COLOR_SURFACE,
                labelcolor=COLOR_TEXT,
                fontsize=7,
                framealpha=0.8,
            )
        self._ax.set_xlabel(tr("Frequency (Hz)"), color=COLOR_MUTED, fontsize=9)
        self._ax.set_ylabel("PSD", color=COLOR_MUTED, fontsize=9)
        self._style_axes()
        self._capture_home_view()
        self._canvas.draw()

    def plot_rms_trend(
        self,
        time_array: NDArray[np.float64],
        rms_trend: NDArray[np.float64],
    ) -> None:
        """Plot RMS trend over time."""
        if not _MATPLOTLIB_AVAILABLE:
            return
        self._ax.clear()
        self._ax.plot(time_array, rms_trend, color=COLOR_WARN, linewidth=0.9)
        self._ax.set_xlabel(tr("Time (s)"), color=COLOR_MUTED, fontsize=9)
        self._ax.set_ylabel("RMS", color=COLOR_MUTED, fontsize=9)
        self._style_axes()
        self._capture_home_view()
        self._canvas.draw()

    def plot_profiles(
        self,
        coords: NDArray[np.float64],
        experiment: NDArray[np.float64],
        cfd: NDArray[np.float64],
        label_exp: str = "Эксперимент",
        label_cfd: str = "CFD",
    ) -> None:
        """Plot two overlaid profiles (experiment vs CFD)."""
        if not _MATPLOTLIB_AVAILABLE:
            return
        self._ax.clear()
        self._ax.plot(coords, experiment, color=COLOR_ACCENT, linewidth=1.2, label=label_exp)
        self._ax.plot(coords, cfd, color=COLOR_WARN, linewidth=1.2, linestyle="--", label=label_cfd)
        self._ax.set_xlabel(tr("Coordinate"), color=COLOR_MUTED, fontsize=9)
        self._ax.set_ylabel(tr("Value"), color=COLOR_MUTED, fontsize=9)
        self._ax.legend(
            facecolor=COLOR_SURFACE,
            labelcolor=COLOR_TEXT,
            fontsize=8,
            framealpha=0.8,
        )
        self._style_axes()
        self._capture_home_view()
        self._canvas.draw()

    def clear(self) -> None:
        """Clear the plot area."""
        if _MATPLOTLIB_AVAILABLE:
            self._ax.clear()
            self._home_xlim = None
            self._home_ylim = None
            self._style_axes()
            self._canvas.draw()
