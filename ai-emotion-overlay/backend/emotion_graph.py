"""
============================================================
Emotion History Graph Module
Generates session emotion timeline visualizations using matplotlib.
Can display live or export as PNG/HTML.
============================================================
"""

import os
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for headless use
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
from typing import Dict, List, Optional
from datetime import datetime
from loguru import logger

from backend.emotion_classifier import EMOTION_LABELS, EMOTION_COLORS


# Convert BGR color tuples to matplotlib RGB (0-1 range)
def _bgr_to_mpl(bgr):
    b, g, r = bgr
    return (r / 255, g / 255, b / 255)


MPLOT_COLORS = {k: _bgr_to_mpl(v) for k, v in EMOTION_COLORS.items()}


class EmotionHistoryGraph:
    """
    Tracks and visualizes emotion scores over time.
    Supports live rolling window display and full session export.
    """

    def __init__(self, window_size: int = 150, output_dir: str = "outputs"):
        """
        Args:
            window_size: Number of recent data points to show in live view
            output_dir: Directory to save exported graphs
        """
        self.window_size = window_size
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Rolling history buffers
        self._history: Dict[str, deque] = {
            emotion: deque(maxlen=window_size) for emotion in EMOTION_LABELS
        }
        self._timestamps: deque = deque(maxlen=window_size)
        self._elapsed: float = 0.0

    def update(self, scores: Dict[str, float], elapsed: float):
        """
        Add a new data point.

        Args:
            scores: Dict of emotion -> score (0.0 - 1.0)
            elapsed: Elapsed time in seconds
        """
        self._elapsed = elapsed
        self._timestamps.append(elapsed)
        for emotion in EMOTION_LABELS:
            self._history[emotion].append(scores.get(emotion, 0.0))

    def export_session_graph(
        self,
        timeline: Dict[str, List],
        session_id: Optional[int] = None,
        title: str = "Emotion History"
    ) -> str:
        """
        Export a full session emotion timeline chart.

        Args:
            timeline: Dict with 'time' key and per-emotion lists from SessionLogger
            session_id: Session ID for filename
            title: Chart title

        Returns:
            Path to saved PNG file
        """
        if not timeline or "time" not in timeline:
            logger.warning("No timeline data to plot")
            return ""

        times = timeline["time"]
        if not times:
            return ""

        fig, axes = plt.subplots(
            len(EMOTION_LABELS), 1,
            figsize=(14, 2.2 * len(EMOTION_LABELS)),
            sharex=True
        )
        fig.patch.set_facecolor("#0d0d0d")

        fig.suptitle(
            title,
            fontsize=16, fontweight="bold",
            color="white", y=0.98
        )

        for ax, emotion in zip(axes, EMOTION_LABELS):
            values = timeline.get(emotion, [0.0] * len(times))
            color = MPLOT_COLORS.get(emotion, (1, 1, 1))

            ax.fill_between(times, values, alpha=0.35, color=color)
            ax.plot(times, values, color=color, linewidth=1.5, label=emotion.capitalize())
            ax.set_ylim(0, 1)
            ax.set_ylabel(emotion.capitalize(), fontsize=9, color=color, labelpad=4)
            ax.set_facecolor("#141414")
            ax.tick_params(colors="gray", labelsize=8)
            ax.spines["bottom"].set_color("#333")
            ax.spines["top"].set_color("#333")
            ax.spines["left"].set_color("#333")
            ax.spines["right"].set_color("#333")
            ax.yaxis.label.set_color(color)
            ax.grid(axis="y", color="#252525", linewidth=0.7)

        axes[-1].set_xlabel("Time (seconds)", fontsize=10, color="gray")

        plt.tight_layout(rect=[0, 0, 1, 0.97])

        # Save
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        sid_str = f"session_{session_id}_" if session_id else ""
        filename = f"{sid_str}emotion_history_{ts}.png"
        filepath = os.path.join(self.output_dir, filename)

        plt.savefig(filepath, dpi=120, bbox_inches="tight", facecolor=fig.get_facecolor())
        plt.close(fig)
        logger.success(f"Emotion history graph saved: {filepath}")
        return filepath

    def export_dominant_pie(
        self,
        summary: Dict,
        session_id: Optional[int] = None
    ) -> str:
        """
        Export a pie chart of dominant emotion distribution.

        Args:
            summary: Session summary dict from SessionLogger.get_session_summary()

        Returns:
            Path to saved PNG file
        """
        emotion_avgs = {
            e: summary.get(f"avg_{e}", 0.0) for e in EMOTION_LABELS
        }
        labels = [e.capitalize() for e in EMOTION_LABELS]
        sizes = [max(0, v) for v in emotion_avgs.values()]
        colors = [MPLOT_COLORS[e] for e in EMOTION_LABELS]

        if sum(sizes) == 0:
            return ""

        fig, ax = plt.subplots(figsize=(8, 7))
        fig.patch.set_facecolor("#0d0d0d")
        ax.set_facecolor("#0d0d0d")

        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, colors=colors,
            autopct="%1.1f%%", startangle=140,
            wedgeprops=dict(edgecolor="#0d0d0d", linewidth=2),
            textprops=dict(color="white", fontsize=10)
        )
        for at in autotexts:
            at.set_fontsize(9)
            at.set_color("white")

        ax.set_title(
            "Emotion Distribution (Session)",
            color="white", fontsize=14, pad=20
        )

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        sid_str = f"session_{session_id}_" if session_id else ""
        filename = f"{sid_str}emotion_pie_{ts}.png"
        filepath = os.path.join(self.output_dir, filename)

        plt.tight_layout()
        plt.savefig(filepath, dpi=120, facecolor=fig.get_facecolor())
        plt.close(fig)
        logger.success(f"Pie chart saved: {filepath}")
        return filepath
