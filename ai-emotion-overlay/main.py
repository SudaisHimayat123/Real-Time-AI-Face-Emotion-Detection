"""
============================================================
AI Face Emotion Overlay — Standalone Desktop Application
Main entry point. Runs entirely with OpenCV, MediaPipe,
and FER — no web server required.

Controls:
  q / ESC  — Quit
  h        — Toggle HUD
  b        — Toggle bounding box
  p        — Toggle persona overlays
  r        — Toggle recording
  s        — Save session CSV
  SPACE    — Pause / Resume
============================================================
"""

import sys
import os
import cv2
import time
import argparse
import yaml
from loguru import logger

# ── Ensure project root is in path ───────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.face_detector import FaceDetector
from backend.emotion_classifier import EmotionClassifier
from backend.hud_renderer import HUDRenderer
from backend.session_logger import SessionLogger
from backend.video_recorder import VideoRecorder


# ═════════════════════════════════════════════════════════════════════════════
# Configuration loader
# ═════════════════════════════════════════════════════════════════════════════

def load_config(config_path: str = "configs/config.yaml") -> dict:
    """Load YAML configuration file."""
    if not os.path.exists(config_path):
        logger.warning(f"Config not found at {config_path}, using defaults")
        return {}
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


# ═════════════════════════════════════════════════════════════════════════════
# Core Pipeline
# ═════════════════════════════════════════════════════════════════════════════

class EmotionOverlayApp:
    """
    Main application class for standalone desktop emotion overlay.
    Handles webcam/video capture, detection, and display.
    """

    def __init__(self, config: dict, video_source=None):
        self.config = config
        self.video_source = video_source  # None = webcam, str = video file path
        self.paused = False
        self.frame_count = 0

        # FPS tracking
        self._fps_counter = 0
        self._fps_timer = time.time()
        self._fps = 0.0

        logger.info("🚀 Initializing AI Face Emotion Overlay...")

        # ── Initialize modules ───────────────────────────────────────────
        cam_cfg = config.get("camera", {})
        model_cfg = config.get("model", {})
        session_cfg = config.get("session", {})
        rec_cfg = config.get("recording", {})

        # Initialize Face Detector
        try:
            self.face_detector = FaceDetector(
                min_confidence=model_cfg.get("face_detection_confidence", 0.6)
            )
            logger.success("✅ Face Detector initialized")
        except Exception as e:
            logger.error(f"❌ Face Detector initialization failed: {e}")
            raise RuntimeError(f"Cannot initialize face detector: {e}")

        # Initialize Emotion Classifier (MUST SUCCEED)
        try:
            self.emotion_classifier = EmotionClassifier(
                model_type=model_cfg.get("emotion_model", "fer"),
                smoothing_window=model_cfg.get("smoothing_window", 8),
                min_face_size=model_cfg.get("min_face_size", 48),
                cooldown_seconds=model_cfg.get("cooldown_seconds", 0.8),
                min_confidence=model_cfg.get("min_confidence", 0.60),
                min_difference_threshold=model_cfg.get("min_difference_threshold", 0.10),
                low_confidence_floor=model_cfg.get("low_confidence_floor", 0.40)
            )
            logger.success("✅ Emotion Classifier initialized")
            
            # Verify classifier is ready
            if not self.emotion_classifier.is_ready():
                raise RuntimeError("Emotion classifier failed readiness check")
                
        except RuntimeError as e:
            logger.error(f"❌ CRITICAL: {e}")
            raise

        # Initialize HUD Renderer
        try:
            self.hud_renderer = HUDRenderer(config)
            logger.success("✅ HUD Renderer initialized")
        except Exception as e:
            logger.warning(f"⚠️  HUD Renderer initialization issue: {e}")

        # Initialize Session Logger (optional)
        if session_cfg.get("log_emotions", True):
            try:
                self.session_logger = SessionLogger(
                    db_path=session_cfg.get("db_path", "outputs/sessions.db"),
                    csv_dir=session_cfg.get("csv_dir", "outputs/csv")
                )
                logger.success("✅ Session Logger initialized")
            except Exception as e:
                logger.warning(f"⚠️  Session Logger initialization issue: {e}")
                self.session_logger = None
        else:
            self.session_logger = None

        # Initialize Video Recorder
        try:
            self.recorder = VideoRecorder(
                output_dir=rec_cfg.get("output_dir", "outputs/videos"),
                codec=rec_cfg.get("codec", "mp4v")
            )
            logger.success("✅ Video Recorder initialized")
        except Exception as e:
            logger.warning(f"⚠️  Video Recorder initialization issue: {e}")

        # ── Open video capture ────────────────────────────────────────────
        source = self.video_source if self.video_source else \
            int(config.get("camera", {}).get("device_id", 0))

        self.cap = cv2.VideoCapture(source)
        if not self.cap.isOpened():
            logger.error(f"Cannot open video source: {source}")
            raise RuntimeError(f"Failed to open video source: {source}")

        # Set camera resolution
        if self.video_source is None:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, cam_cfg.get("width", 1280))
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam_cfg.get("height", 720))
            self.cap.set(cv2.CAP_PROP_FPS, cam_cfg.get("fps", 30))

        actual_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        logger.success(f"Video source opened: {actual_w}x{actual_h}")

        # Start session logging
        if self.session_logger:
            source_name = "webcam" if self.video_source is None else "video_file"
            self.session_logger.start_session(source=source_name)

        # Auto-start recording if configured
        if rec_cfg.get("auto_save", False):
            self.recorder.start_recording((actual_w, actual_h), fps=30.0)

        self.window_name = config.get("display", {}).get("window_name", "AI Face Emotion Overlay")

    # ──────────────────────────────────────────────────────────────────────────
    # Main loop
    # ──────────────────────────────────────────────────────────────────────────

    def run(self):
        """Main processing loop."""
        logger.info("=" * 70)
        logger.success("✅ ALL MODELS READY - Starting main loop")
        logger.info(f"📊 Using: {self.emotion_classifier.model_type.upper()} emotion model")
        logger.info(f"🔧 Smoothing window: {self.emotion_classifier.smoothing_window} frames")
        logger.info(f"⏱️  Cooldown lock: {self.emotion_classifier.cooldown_seconds}s")
        logger.info(f"✋ Min confidence: {self.emotion_classifier.min_confidence:.0%}")
        logger.info("=" * 70)
        logger.info("⌨️  Controls: q/ESC=quit, h=HUD, b=boxes, p=persona, r=record, s=export, SPACE=pause")

        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, 1280, 720)

        while True:
            key = cv2.waitKey(1) & 0xFF

            # ── Keyboard controls ──────────────────────────────────────────
            if key == ord("q") or key == 27:   # q or ESC
                break
            elif key == ord("h"):
                self.hud_renderer.toggle_hud()
            elif key == ord("b"):
                self.hud_renderer.toggle_bbox()
            elif key == ord("p"):
                self.hud_renderer.toggle_persona()
            elif key == ord("r"):
                w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                recording = self.recorder.toggle_recording((w, h), fps=self._fps or 30.0)
                logger.info(f"Recording: {'started' if recording else 'stopped'}")
            elif key == ord("s"):
                if self.session_logger:
                    path = self.session_logger.export_csv()
                    logger.info(f"CSV exported: {path}")
            elif key == ord(" "):
                self.paused = not self.paused
                logger.info(f"{'Paused' if self.paused else 'Resumed'}")

            if self.paused:
                continue

            # ── Capture frame ──────────────────────────────────────────────
            ret, frame = self.cap.read()
            if not ret:
                if self.video_source:
                    logger.info("End of video file")
                    break
                else:
                    logger.warning("Failed to grab frame from webcam")
                    continue

            self.frame_count += 1
            self._update_fps()

            # ── Detection + classification ─────────────────────────────────
            detections = self.face_detector.detect(frame)
            emotion_results = []

            for i, det in enumerate(detections):
                scores = self.emotion_classifier.predict(det.face_crop, face_index=i)
                emotion_results.append(scores)

                # Log to session
                if self.session_logger:
                    dominant, confidence = EmotionClassifier.get_dominant_emotion(scores)
                    self.session_logger.log_frame(
                        scores, i, dominant, confidence
                    )

            # ── Render overlays ────────────────────────────────────────────
            output_frame = self.hud_renderer.render(
                frame,
                detections,
                emotion_results,
                fps=self._fps,
                recording=self.recorder.is_recording,
                frame_count=self.frame_count
            )

            # ── Record frame ───────────────────────────────────────────────
            if self.recorder.is_recording:
                self.recorder.write_frame(output_frame)

            # ── Display ────────────────────────────────────────────────────
            cv2.imshow(self.window_name, output_frame)

        self._cleanup()

    def _update_fps(self):
        """Update rolling FPS estimate."""
        self._fps_counter += 1
        now = time.time()
        elapsed = now - self._fps_timer
        if elapsed >= 1.0:
            self._fps = self._fps_counter / elapsed
            self._fps_counter = 0
            self._fps_timer = now

    def _cleanup(self):
        """Release all resources on exit."""
        logger.info("Shutting down...")

        if self.cap:
            self.cap.release()

        if self.recorder.is_recording:
            self.recorder.stop_recording()

        if self.session_logger:
            self.session_logger.end_session(total_frames=self.frame_count)
            # Auto-export CSV on exit
            if self.config.get("session", {}).get("export_csv", True):
                csv_path = self.session_logger.export_csv()
                if csv_path:
                    logger.info(f"Session CSV saved: {csv_path}")

        self.face_detector.release()
        cv2.destroyAllWindows()
        logger.success("Application closed cleanly")


# ═════════════════════════════════════════════════════════════════════════════
# Entry point
# ═════════════════════════════════════════════════════════════════════════════

def parse_args():
    parser = argparse.ArgumentParser(
        description="AI Face Emotion Overlay — Real-time facial emotion detection"
    )
    parser.add_argument(
        "--source",
        default=None,
        help="Video source: leave blank for webcam, or provide path to video file"
    )
    parser.add_argument(
        "--config",
        default="configs/config.yaml",
        help="Path to configuration YAML file"
    )
    parser.add_argument(
        "--model",
        default=None,
        choices=["fer", "deepface", "custom"],
        help="Override emotion model backend"
    )
    parser.add_argument(
        "--no-hud",
        action="store_true",
        help="Start with HUD hidden"
    )
    parser.add_argument(
        "--record",
        action="store_true",
        help="Auto-start recording on launch"
    )
    parser.add_argument(
        "--persona",
        action="store_true",
        help="Enable persona/AR overlays"
    )
    return parser.parse_args()


def main():
    # Configure logger
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | {message}",
        level="INFO"
    )
    logger.add("outputs/app.log", rotation="10 MB", level="DEBUG")

    args = parse_args()

    # Load config
    config = load_config(args.config)

    # Apply CLI overrides
    if args.model:
        config.setdefault("model", {})["emotion_model"] = args.model

    if args.no_hud:
        config.setdefault("overlay", {})["show_hud"] = False

    if args.record:
        config.setdefault("recording", {})["auto_save"] = True

    if args.persona:
        config.setdefault("overlay", {})["show_persona"] = True
        config.setdefault("persona", {})["enabled"] = True

    # Launch app
    try:
        app = EmotionOverlayApp(config=config, video_source=args.source)
        app.run()
    except RuntimeError as e:
        logger.error(str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
