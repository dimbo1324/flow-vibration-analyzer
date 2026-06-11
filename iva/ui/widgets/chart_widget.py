"""ChartWidget — matplotlib canvas embedded in a Qt widget.

Falls back gracefully to a placeholder label if matplotlib is not available.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt  # type: ignore[import-untyped]
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget  # type: ignore[import-untyped]

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

    matplotlib.use("QtAgg")
    from matplotlib.backends.backend_qtagg import (  # type: ignore[import-untyped]
        FigureCanvasQTAgg as FigureCanvas,
    )
    from matplotlib.figure import Figure  # type: ignore[import-untyped]

    _MATPLOTLIB_AVAILABLE = True
except ImportError:
    _MATPLOTLIB_AVAILABLE = False

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
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        if _MATPLOTLIB_AVAILABLE:
            bg = _hex_to_rgb_float(COLOR_BG)
            self._fig = Figure(facecolor=bg, tight_layout=True)  # type: ignore[possibly-undefined]
            self._ax = self._fig.add_subplot(111)
            self._canvas = FigureCanvas(self._fig)  # type: ignore[possibly-undefined]
            self._canvas.setParent(self)
            self._style_axes()
            layout.addWidget(self._canvas)
        else:
            lbl = QLabel("Chart requires matplotlib\n(pip install matplotlib)")
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
    # Public plotting API
    # ------------------------------------------------------------------

    def plot_signal(
        self,
        time_array: NDArray[np.float64],
        signal_array: NDArray[np.float64],
        label: str = "Signal",
    ) -> None:
        """Plot a time-domain signal."""
        if not _MATPLOTLIB_AVAILABLE:
            return
        self._ax.clear()
        self._ax.plot(time_array, signal_array, color=COLOR_ACCENT, linewidth=0.8, label=label)
        self._ax.set_xlabel("Time (s)", color=COLOR_MUTED, fontsize=9)
        self._ax.set_ylabel("Amplitude", color=COLOR_MUTED, fontsize=9)
        self._ax.legend(
            facecolor=COLOR_SURFACE,
            labelcolor=COLOR_TEXT,
            fontsize=8,
            framealpha=0.8,
        )
        self._style_axes()
        self._canvas.draw()

    def plot_two_signals(
        self,
        time_array: NDArray[np.float64],
        signal_a: NDArray[np.float64],
        signal_b: NDArray[np.float64],
        label_a: str = "Cleaned",
        label_b: str = "Filtered",
    ) -> None:
        """Plot two overlaid time-domain signals."""
        if not _MATPLOTLIB_AVAILABLE:
            return
        self._ax.clear()
        self._ax.plot(time_array, signal_a, color=COLOR_MUTED, linewidth=0.6, label=label_a)
        self._ax.plot(time_array, signal_b, color=COLOR_ACCENT, linewidth=0.8, label=label_b)
        self._ax.set_xlabel("Time (s)", color=COLOR_MUTED, fontsize=9)
        self._ax.set_ylabel("Amplitude", color=COLOR_MUTED, fontsize=9)
        self._ax.legend(
            facecolor=COLOR_SURFACE,
            labelcolor=COLOR_TEXT,
            fontsize=8,
            framealpha=0.8,
        )
        self._style_axes()
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
        self._ax.set_xlabel("Frequency (Hz)", color=COLOR_MUTED, fontsize=9)
        self._ax.set_ylabel("PSD", color=COLOR_MUTED, fontsize=9)
        self._style_axes()
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
        self._ax.set_xlabel("Time (s)", color=COLOR_MUTED, fontsize=9)
        self._ax.set_ylabel("RMS", color=COLOR_MUTED, fontsize=9)
        self._style_axes()
        self._canvas.draw()

    def clear(self) -> None:
        """Clear the plot area."""
        if _MATPLOTLIB_AVAILABLE:
            self._ax.clear()
            self._style_axes()
            self._canvas.draw()
