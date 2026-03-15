"""
============================================================
HUD & Overlay Renderer Module
Renders bounding boxes, emotion labels, progress bar HUD,
and optional persona AR filter overlays on video frames.
============================================================
"""

import cv2
import numpy as np
import os
from typing import Dict, List, Optional, Tuple
from loguru import logger

from backend.emotion_classifier import (
    EMOTION_LABELS,
    EMOTION_DISPLAY,
    EMOTION_COLORS,
    EmotionClassifier
)
from backend.face_detector import FaceDetection


class HUDRenderer:
    """
    Renders all visual overlays on video frames:
    - White bounding box + emotion label on each face
    - Left-side HUD panel with progress bars for all emotion scores
    - Optional persona/AR filter overlays
    - FPS counter and session info
    """

    def __init__(self, config: dict):
        self.config = config
        self.show_hud = config.get("overlay", {}).get("show_hud", True)
        self.show_bbox = config.get("overlay", {}).get("show_bounding_box", True)
        self.show_persona = config.get("overlay", {}).get("show_persona", False)

        # HUD dimensions
        self.hud_x = 10
        self.hud_y = 10
        self.hud_w = 210
        self.bar_w = 160
        self.bar_h = 14

        # Font settings
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_small = 0.45
        self.font_medium = 0.55
        self.font_large = 0.7

        # Color palette (BGR)
        self.COL_WHITE = (255, 255, 255)
        self.COL_BLACK = (0, 0, 0)
        self.COL_MAGENTA = (255, 100, 255)
        self.COL_DARK_BG = (15, 15, 15)
        self.COL_PANEL_BG = (25, 25, 25)
        self.COL_GRAY = (120, 120, 120)
        self.COL_GREEN = (50, 200, 50)
        self.COL_RED = (50, 50, 220)

        # Persona overlay assets cache
        self._persona_assets: Dict[str, Optional[np.ndarray]] = {}
        self._load_persona_assets()

    # ──────────────────────────────────────────────────────────────────────────
    # Main render entry point
    # ──────────────────────────────────────────────────────────────────────────

    def render(
        self,
        frame: np.ndarray,
        detections: List[FaceDetection],
        emotion_results: List[Dict[str, float]],
        fps: float = 0.0,
        recording: bool = False,
        frame_count: int = 0
    ) -> np.ndarray:
        """
        Render all overlays on the frame.

        Args:
            frame: BGR frame from camera/video
            detections: List of detected faces
            emotion_results: List of emotion score dicts (one per face)
            fps: Current frames per second
            recording: Whether currently recording
            frame_count: Total frames processed

        Returns:
            Frame with all overlays rendered
        """
        output = frame.copy()

        # ── Render each detected face ──────────────────────────────────────
        for i, (det, scores) in enumerate(zip(detections, emotion_results)):
            dominant, confidence = EmotionClassifier.get_dominant_emotion(scores)

            if self.show_bbox:
                self._draw_face_box(output, det, dominant, confidence)

            if self.show_persona:
                self._draw_persona(output, det, dominant)

        # ── HUD panel (uses scores from first/dominant face) ───────────────
        if self.show_hud:
            agg_scores = self._aggregate_scores(emotion_results)
            self._draw_hud_panel(output, agg_scores)

        # ── Status bar (bottom) ───────────────────────────────────────────
        self._draw_status_bar(output, fps, len(detections), recording, frame_count)

        return output

    # ──────────────────────────────────────────────────────────────────────────
    # Face bounding box + label
    # ──────────────────────────────────────────────────────────────────────────

    def _draw_face_box(
        self,
        frame: np.ndarray,
        det: FaceDetection,
        emotion: str,
        confidence: float
    ):
        """Draw white bounding box and emotion label on detected face."""
        x, y, w, h = det.x, det.y, det.w, det.h
        thickness = self.config.get("overlay", {}).get("bbox_thickness", 2)
        bbox_color = tuple(self.config.get("overlay", {}).get("bbox_color", [255, 255, 255]))

        # ── Corner accent style bounding box ──────────────────────────────
        corner_len = max(10, min(w, h) // 6)

        # Draw full box first (thin)
        cv2.rectangle(frame, (x, y), (x + w, y + h), bbox_color, 1)

        # Draw corner accents (thicker)
        corners = [
            # Top-left
            [(x, y), (x + corner_len, y)],
            [(x, y), (x, y + corner_len)],
            # Top-right
            [(x + w, y), (x + w - corner_len, y)],
            [(x + w, y), (x + w, y + corner_len)],
            # Bottom-left
            [(x, y + h), (x + corner_len, y + h)],
            [(x, y + h), (x, y + h - corner_len)],
            # Bottom-right
            [(x + w, y + h), (x + w - corner_len, y + h)],
            [(x + w, y + h), (x + w, y + h - corner_len)],
        ]
        for pt1, pt2 in corners:
            cv2.line(frame, pt1, pt2, self.COL_WHITE, thickness + 1)

        # ── Emotion label ──────────────────────────────────────────────────
        display_emotion = EMOTION_DISPLAY.get(emotion, emotion.capitalize())
        label = f"{display_emotion} ({confidence * 100:.0f}%)"

        # Measure text for background box
        (lw, lh), baseline = cv2.getTextSize(
            label, self.font, self.font_medium, 1
        )

        # Solid black label background above bounding box
        label_y = max(lh + baseline + 4, y - 4)
        cv2.rectangle(
            frame,
            (x, label_y - lh - baseline - 4),
            (x + lw + 8, label_y + 2),
            self.COL_BLACK,
            -1
        )

        # Emotion-colored text
        emotion_color = EMOTION_COLORS.get(emotion, self.COL_WHITE)
        cv2.putText(
            frame, label,
            (x + 4, label_y - baseline - 2),
            self.font, self.font_medium,
            emotion_color, 1, cv2.LINE_AA
        )

        # Confidence dot indicator
        dot_color = emotion_color
        cv2.circle(frame, (x + w - 8, y + 8), 5, dot_color, -1)

    # ──────────────────────────────────────────────────────────────────────────
    # HUD Panel
    # ──────────────────────────────────────────────────────────────────────────

    def _draw_hud_panel(self, frame: np.ndarray, scores: Dict[str, float]):
        """
        Draw the left-side HUD panel with:
        - Title: FACE EMOTION HUD
        - 7 emotion rows, each with colored progress bar and percentage
        """
        h_frame, w_frame = frame.shape[:2]

        # HUD panel dimensions
        row_h = 26
        title_h = 36
        padding = 10
        panel_h = title_h + (len(EMOTION_LABELS) * row_h) + padding * 2
        panel_w = self.hud_w + 20

        px, py = self.hud_x, self.hud_y

        # ── Draw semi-transparent panel background ─────────────────────────
        overlay = frame.copy()
        cv2.rectangle(
            overlay,
            (px, py),
            (px + panel_w, py + panel_h),
            self.COL_DARK_BG,
            -1
        )
        # Border
        cv2.rectangle(
            overlay,
            (px, py),
            (px + panel_w, py + panel_h),
            (60, 60, 60),
            1
        )
        # Blend for transparency
        alpha = self.config.get("overlay", {}).get("hud_alpha", 0.82)
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

        # ── Panel title ────────────────────────────────────────────────────
        cv2.putText(
            frame, "FACE EMOTION HUD",
            (px + 8, py + 24),
            self.font, 0.52,
            self.COL_MAGENTA, 1, cv2.LINE_AA
        )

        # Separator line
        cv2.line(
            frame,
            (px + 4, py + title_h),
            (px + panel_w - 4, py + title_h),
            (60, 60, 60), 1
        )

        # ── Emotion rows ───────────────────────────────────────────────────
        for idx, emotion in enumerate(EMOTION_LABELS):
            score = scores.get(emotion, 0.0)
            row_y = py + title_h + padding + idx * row_h
            color = EMOTION_COLORS.get(emotion, self.COL_WHITE)
            display = EMOTION_DISPLAY.get(emotion, emotion.capitalize())

            # Emotion label (left)
            label_x = px + 8
            cv2.putText(
                frame, display,
                (label_x, row_y + 11),
                self.font, 0.42,
                self.COL_WHITE, 1, cv2.LINE_AA
            )

            # Progress bar track (background)
            bar_x = px + 72
            bar_y = row_y + 2
            track_end = bar_x + self.bar_w
            cv2.rectangle(
                frame,
                (bar_x, bar_y),
                (track_end, bar_y + self.bar_h),
                (50, 50, 50),
                -1
            )
            cv2.rectangle(
                frame,
                (bar_x, bar_y),
                (track_end, bar_y + self.bar_h),
                (70, 70, 70),
                1
            )

            # Progress bar fill
            fill_w = int(self.bar_w * score)
            if fill_w > 0:
                # Gradient-like effect: darken at edges
                cv2.rectangle(
                    frame,
                    (bar_x, bar_y),
                    (bar_x + fill_w, bar_y + self.bar_h),
                    color,
                    -1
                )
                # Highlight top edge
                brighter = tuple(min(255, c + 60) for c in color)
                cv2.line(
                    frame,
                    (bar_x, bar_y + 1),
                    (bar_x + fill_w, bar_y + 1),
                    brighter, 1
                )

            # Percentage text (right of bar)
            pct_text = f"{score * 100:.0f}%"
            cv2.putText(
                frame, pct_text,
                (track_end + 4, row_y + 11),
                self.font, 0.40,
                self.COL_GRAY, 1, cv2.LINE_AA
            )

    # ──────────────────────────────────────────────────────────────────────────
    # Status bar
    # ──────────────────────────────────────────────────────────────────────────

    def _draw_status_bar(
        self,
        frame: np.ndarray,
        fps: float,
        face_count: int,
        recording: bool,
        frame_count: int
    ):
        """Draw bottom status bar with FPS, face count, recording indicator."""
        h, w = frame.shape[:2]
        bar_h = 28
        bar_y = h - bar_h

        # Semi-transparent background
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, bar_y), (w, h), self.COL_DARK_BG, -1)
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

        # FPS counter
        fps_color = self.COL_GREEN if fps >= 20 else self.COL_RED
        cv2.putText(
            frame, f"FPS: {fps:.1f}",
            (10, h - 8),
            self.font, 0.50, fps_color, 1, cv2.LINE_AA
        )

        # Face count
        cv2.putText(
            frame, f"Faces: {face_count}",
            (100, h - 8),
            self.font, 0.50, self.COL_WHITE, 1, cv2.LINE_AA
        )

        # Recording indicator
        if recording:
            cv2.circle(frame, (w - 120, h - 12), 6, (0, 0, 220), -1)
            cv2.putText(
                frame, "REC",
                (w - 108, h - 7),
                self.font, 0.48, (0, 0, 220), 1, cv2.LINE_AA
            )

        # Quit hint (bottom right)
        hint = "Press 'q' to quit"
        (hint_w, _), _ = cv2.getTextSize(hint, self.font, 0.45, 1)
        cv2.putText(
            frame, hint,
            (w - hint_w - 10, h - 8),
            self.font, 0.45, self.COL_GRAY, 1, cv2.LINE_AA
        )

        # Frame counter (center)
        frame_txt = f"Frame: {frame_count}"
        (ft_w, _), _ = cv2.getTextSize(frame_txt, self.font, 0.42, 1)
        cv2.putText(
            frame, frame_txt,
            ((w - ft_w) // 2, h - 8),
            self.font, 0.42, self.COL_GRAY, 1, cv2.LINE_AA
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Persona / AR overlay
    # ──────────────────────────────────────────────────────────────────────────

    def _load_persona_assets(self):
        """Load PNG overlay assets for each emotion."""
        asset_dir = os.path.join("assets", "overlays")
        persona_cfg = self.config.get("persona", {}).get("assets", {})

        for emotion, filename in persona_cfg.items():
            path = os.path.join(asset_dir, filename)
            if os.path.exists(path):
                img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
                if img is not None:
                    self._persona_assets[emotion] = img
                    logger.debug(f"Loaded persona asset: {filename}")
                else:
                    self._persona_assets[emotion] = None
            else:
                self._persona_assets[emotion] = None

    def _draw_persona(
        self,
        frame: np.ndarray,
        det: FaceDetection,
        emotion: str
    ):
        """
        Overlay the emotion-based persona/AR filter on the detected face.
        Uses face bounding box to position and scale overlay.
        """
        asset = self._persona_assets.get(emotion)
        if asset is None:
            return

        x, y, w, h = det.x, det.y, det.w, det.h
        scale = self.config.get("persona", {}).get("scale_factor", 1.3)

        # Scale overlay relative to face size
        ow = int(w * scale)
        oh = int(h * scale)

        # Center above the face
        ox = x - (ow - w) // 2
        oy = y - oh // 2

        try:
            self._alpha_blend_overlay(frame, asset, ox, oy, ow, oh)
        except Exception as e:
            logger.debug(f"Persona overlay render error: {e}")

    def _alpha_blend_overlay(
        self,
        frame: np.ndarray,
        overlay: np.ndarray,
        ox: int, oy: int,
        ow: int, oh: int
    ):
        """Alpha-blend a BGRA overlay image onto the frame."""
        fh, fw = frame.shape[:2]

        # Resize overlay
        resized = cv2.resize(overlay, (ow, oh), interpolation=cv2.INTER_AREA)

        # Compute valid region (clip to frame boundaries)
        x1 = max(0, ox)
        y1 = max(0, oy)
        x2 = min(fw, ox + ow)
        y2 = min(fh, oy + oh)

        if x1 >= x2 or y1 >= y2:
            return

        rx1 = x1 - ox
        ry1 = y1 - oy
        rx2 = rx1 + (x2 - x1)
        ry2 = ry1 + (y2 - y1)

        roi = frame[y1:y2, x1:x2]
        asset_roi = resized[ry1:ry2, rx1:rx2]

        if asset_roi.shape[2] == 4:
            alpha = asset_roi[:, :, 3:4].astype(np.float32) / 255.0
            asset_bgr = asset_roi[:, :, :3].astype(np.float32)
            roi_f = roi.astype(np.float32)
            blended = roi_f * (1.0 - alpha) + asset_bgr * alpha
            frame[y1:y2, x1:x2] = blended.astype(np.uint8)
        else:
            frame[y1:y2, x1:x2] = asset_roi[:, :, :3]

    # ──────────────────────────────────────────────────────────────────────────
    # Utility
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _aggregate_scores(
        emotion_results: List[Dict[str, float]]
    ) -> Dict[str, float]:
        """
        Average emotion scores across all detected faces for the HUD display.
        IMPROVED: Shows raw average confidence scores (NOT normalized).
        This allows seeing actual confidence levels instead of proportional percentages.
        
        If no faces detected, returns uniform scores.
        """
        if not emotion_results:
            val = 1.0 / len(EMOTION_LABELS)
            return {e: val for e in EMOTION_LABELS}

        aggregated = {e: 0.0 for e in EMOTION_LABELS}
        for scores in emotion_results:
            for emotion, score in scores.items():
                aggregated[emotion] = aggregated.get(emotion, 0.0) + score

        n = len(emotion_results)
        # Return raw averaged scores WITHOUT normalization
        # This shows actual confidence instead of proportion summing to 1.0
        return {k: min(1.0, v / n) for k, v in aggregated.items()}

    def toggle_hud(self):
        """Toggle HUD visibility."""
        self.show_hud = not self.show_hud
        logger.info(f"HUD {'enabled' if self.show_hud else 'disabled'}")

    def toggle_bbox(self):
        """Toggle bounding box visibility."""
        self.show_bbox = not self.show_bbox
        logger.info(f"Bounding box {'enabled' if self.show_bbox else 'disabled'}")

    def toggle_persona(self):
        """Toggle persona overlay."""
        self.show_persona = not self.show_persona
        logger.info(f"Persona overlay {'enabled' if self.show_persona else 'disabled'}")
