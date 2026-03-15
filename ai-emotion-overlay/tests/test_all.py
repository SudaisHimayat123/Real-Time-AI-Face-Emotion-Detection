"""
============================================================
Unit Tests for AI Face Emotion Overlay
Run: pytest tests/ -v
============================================================
"""

import sys
import os
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.emotion_classifier import (
    EmotionClassifier,
    EMOTION_LABELS,
    EMOTION_COLORS,
    EMOTION_DISPLAY
)
from backend.face_detector import FaceDetection
from backend.hud_renderer import HUDRenderer
from backend.session_logger import SessionLogger
from backend.video_recorder import VideoRecorder


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_frame():
    """Create a synthetic 480x640 BGR frame."""
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    # Draw a gray face-sized rectangle
    frame[100:200, 150:250] = 128
    return frame


@pytest.fixture
def sample_face_crop():
    """Create a synthetic 64x64 BGR face crop."""
    crop = np.random.randint(50, 200, (64, 64, 3), dtype=np.uint8)
    return crop


@pytest.fixture
def sample_scores():
    """Normalized emotion scores dict."""
    return {
        "angry": 0.05,
        "disgust": 0.02,
        "fear": 0.03,
        "happy": 0.72,
        "neutral": 0.10,
        "sad": 0.04,
        "surprise": 0.04
    }


@pytest.fixture
def mock_config():
    return {
        "overlay": {
            "show_hud": True,
            "show_bounding_box": True,
            "show_persona": False,
            "hud_alpha": 0.8,
            "bbox_color": [255, 255, 255],
            "bbox_thickness": 2,
            "progress_bar_width": 160,
        },
        "persona": {
            "enabled": False,
            "scale_factor": 1.3,
            "assets": {}
        },
        "model": {
            "emotion_model": "mock",
            "smoothing_window": 3,
            "min_face_size": 32
        }
    }


@pytest.fixture
def session_logger_temp(tmp_path):
    return SessionLogger(
        db_path=str(tmp_path / "test.db"),
        csv_dir=str(tmp_path / "csv")
    )


# ─────────────────────────────────────────────────────────────────────────────
# EmotionClassifier Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestEmotionClassifier:

    def test_emotion_labels_count(self):
        assert len(EMOTION_LABELS) == 7

    def test_emotion_labels_content(self):
        expected = {"angry", "disgust", "fear", "happy", "neutral", "sad", "surprise"}
        assert set(EMOTION_LABELS) == expected

    def test_normalize_scores_sums_to_one(self):
        raw = {"happy": 10.0, "sad": 5.0, "angry": 2.0}
        norm = EmotionClassifier._normalize_scores(raw)
        assert abs(sum(norm.values()) - 1.0) < 1e-6

    def test_normalize_scores_all_labels_present(self):
        raw = {"happy": 0.9}
        norm = EmotionClassifier._normalize_scores(raw)
        for label in EMOTION_LABELS:
            assert label in norm

    def test_normalize_scores_no_negatives(self):
        raw = {"happy": -0.5, "angry": 0.8}
        norm = EmotionClassifier._normalize_scores(raw)
        for v in norm.values():
            assert v >= 0.0

    def test_get_dominant_emotion(self, sample_scores):
        dominant, confidence = EmotionClassifier.get_dominant_emotion(sample_scores)
        assert dominant == "happy"
        assert abs(confidence - 0.72) < 1e-6

    def test_get_dominant_emotion_empty(self):
        dominant, confidence = EmotionClassifier.get_dominant_emotion({})
        assert dominant == "neutral"
        assert confidence == 0.0

    def test_predict_returns_all_labels(self, sample_face_crop):
        clf = EmotionClassifier(model_type="mock")
        scores = clf.predict(sample_face_crop, face_index=0)
        for label in EMOTION_LABELS:
            assert label in scores

    def test_predict_scores_sum_to_one(self, sample_face_crop):
        clf = EmotionClassifier(model_type="mock")
        scores = clf.predict(sample_face_crop, face_index=0)
        assert abs(sum(scores.values()) - 1.0) < 1e-5

    def test_predict_scores_non_negative(self, sample_face_crop):
        clf = EmotionClassifier(model_type="mock")
        scores = clf.predict(sample_face_crop, face_index=0)
        for v in scores.values():
            assert v >= 0.0

    def test_predict_tiny_face_returns_uniform(self):
        """Faces smaller than min_face_size should return uniform scores."""
        clf = EmotionClassifier(model_type="mock", min_face_size=100)
        tiny_crop = np.zeros((20, 20, 3), dtype=np.uint8)
        scores = clf.predict(tiny_crop, face_index=0)
        # Should return uniform (all roughly equal)
        values = list(scores.values())
        assert max(values) - min(values) < 0.02

    def test_predict_none_face(self):
        clf = EmotionClassifier(model_type="mock")
        scores = clf.predict(None, face_index=0)
        assert isinstance(scores, dict)
        assert len(scores) == len(EMOTION_LABELS)

    def test_smoothing_history_accumulates(self, sample_face_crop):
        clf = EmotionClassifier(model_type="mock", smoothing_window=5)
        for i in range(7):
            clf.predict(sample_face_crop, face_index=0)
        # History deque should have up to window_size entries
        assert len(clf._history.get(0, [])) <= 5

    def test_reset_history(self, sample_face_crop):
        clf = EmotionClassifier(model_type="mock", smoothing_window=5)
        for _ in range(3):
            clf.predict(sample_face_crop, face_index=0)
        clf.reset_history(face_index=0)
        assert 0 not in clf._history

    def test_uniform_scores(self):
        uniform = EmotionClassifier._uniform_scores_static()
        assert len(uniform) == len(EMOTION_LABELS)
        expected_val = 1.0 / len(EMOTION_LABELS)
        for v in uniform.values():
            assert abs(v - expected_val) < 1e-6


# ─────────────────────────────────────────────────────────────────────────────
# HUDRenderer Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestHUDRenderer:

    def test_render_returns_frame(self, mock_config, sample_frame, sample_scores):
        renderer = HUDRenderer(mock_config)
        det = FaceDetection(x=150, y=100, w=100, h=100, confidence=0.95)
        result = renderer.render(sample_frame, [det], [sample_scores], fps=30.0)
        assert result is not None
        assert result.shape == sample_frame.shape

    def test_render_no_faces(self, mock_config, sample_frame):
        renderer = HUDRenderer(mock_config)
        result = renderer.render(sample_frame, [], [], fps=30.0)
        assert result is not None
        assert result.shape == sample_frame.shape

    def test_toggle_hud(self, mock_config):
        renderer = HUDRenderer(mock_config)
        initial = renderer.show_hud
        renderer.toggle_hud()
        assert renderer.show_hud == (not initial)

    def test_toggle_bbox(self, mock_config):
        renderer = HUDRenderer(mock_config)
        initial = renderer.show_bbox
        renderer.toggle_bbox()
        assert renderer.show_bbox == (not initial)

    def test_toggle_persona(self, mock_config):
        renderer = HUDRenderer(mock_config)
        initial = renderer.show_persona
        renderer.toggle_persona()
        assert renderer.show_persona == (not initial)

    def test_aggregate_scores_empty(self):
        result = HUDRenderer._aggregate_scores([])
        assert set(result.keys()) == set(EMOTION_LABELS)

    def test_aggregate_scores_single(self, sample_scores):
        result = HUDRenderer._aggregate_scores([sample_scores])
        assert abs(result["happy"] - sample_scores["happy"]) < 1e-6

    def test_aggregate_scores_multiple(self):
        s1 = {e: 0.1 for e in EMOTION_LABELS}
        s1["happy"] = 0.4
        s2 = {e: 0.1 for e in EMOTION_LABELS}
        s2["happy"] = 0.6
        result = HUDRenderer._aggregate_scores([s1, s2])
        assert abs(result["happy"] - 0.5) < 1e-6

    def test_render_with_recording_flag(self, mock_config, sample_frame, sample_scores):
        renderer = HUDRenderer(mock_config)
        det = FaceDetection(x=150, y=100, w=80, h=80, confidence=0.9)
        result = renderer.render(
            sample_frame, [det], [sample_scores],
            fps=25.0, recording=True, frame_count=100
        )
        assert result is not None

    def test_render_large_frame(self, mock_config, sample_scores):
        renderer = HUDRenderer(mock_config)
        large_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        result = renderer.render(large_frame, [], [])
        assert result.shape == (1080, 1920, 3)


# ─────────────────────────────────────────────────────────────────────────────
# SessionLogger Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestSessionLogger:

    def test_start_session(self, session_logger_temp):
        sid = session_logger_temp.start_session("webcam")
        assert isinstance(sid, int)
        assert sid > 0

    def test_log_frame(self, session_logger_temp, sample_scores):
        session_logger_temp.start_session("webcam")
        session_logger_temp.log_frame(sample_scores, 0, "happy", 0.72)
        session_logger_temp._flush_buffer()
        # Verify data exists
        timeline = session_logger_temp.get_emotion_timeline()
        assert "time" in timeline

    def test_end_session(self, session_logger_temp):
        session_logger_temp.start_session("test")
        session_logger_temp.end_session(total_frames=100)
        sessions = session_logger_temp.get_all_sessions()
        assert len(sessions) >= 1
        assert sessions[0]["total_frames"] == 100

    def test_export_csv(self, session_logger_temp, sample_scores, tmp_path):
        session_logger_temp.start_session("test")
        for i in range(10):
            session_logger_temp.log_frame(sample_scores, 0, "happy", 0.72)
        path = session_logger_temp.export_csv()
        assert path
        assert os.path.exists(path)

    def test_get_session_summary(self, session_logger_temp, sample_scores):
        session_logger_temp.start_session("test")
        for _ in range(5):
            session_logger_temp.log_frame(sample_scores, 0, "happy", 0.72)
        session_logger_temp._flush_buffer()
        summary = session_logger_temp.get_session_summary()
        assert "avg_happy" in summary
        assert summary.get("avg_happy", 0) > 0

    def test_get_all_sessions_empty_initially(self, tmp_path):
        fresh = SessionLogger(
            db_path=str(tmp_path / "fresh.db"),
            csv_dir=str(tmp_path / "csv")
        )
        sessions = fresh.get_all_sessions()
        assert sessions == []

    def test_multiple_sessions(self, session_logger_temp, sample_scores):
        for i in range(3):
            session_logger_temp.start_session(f"source_{i}")
            session_logger_temp.end_session(total_frames=i * 10)
        sessions = session_logger_temp.get_all_sessions()
        assert len(sessions) == 3


# ─────────────────────────────────────────────────────────────────────────────
# VideoRecorder Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestVideoRecorder:

    def test_not_recording_initially(self, tmp_path):
        recorder = VideoRecorder(output_dir=str(tmp_path))
        assert not recorder.is_recording

    def test_start_and_stop_recording(self, tmp_path, sample_frame):
        recorder = VideoRecorder(output_dir=str(tmp_path))
        h, w = sample_frame.shape[:2]
        path = recorder.start_recording((w, h), fps=30.0)
        assert recorder.is_recording

        # Write a few frames
        for _ in range(5):
            recorder.write_frame(sample_frame)

        saved_path = recorder.stop_recording()
        assert not recorder.is_recording
        assert saved_path
        assert os.path.exists(saved_path)

    def test_toggle_recording(self, tmp_path, sample_frame):
        recorder = VideoRecorder(output_dir=str(tmp_path))
        h, w = sample_frame.shape[:2]
        is_rec = recorder.toggle_recording((w, h), fps=24.0)
        assert is_rec
        is_rec = recorder.toggle_recording((w, h), fps=24.0)
        assert not is_rec

    def test_write_without_recording_does_nothing(self, tmp_path, sample_frame):
        recorder = VideoRecorder(output_dir=str(tmp_path))
        # Should not raise
        recorder.write_frame(sample_frame)


# ─────────────────────────────────────────────────────────────────────────────
# FaceDetection Dataclass Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestFaceDetection:

    def test_face_detection_creation(self):
        det = FaceDetection(x=10, y=20, w=100, h=120, confidence=0.95)
        assert det.x == 10
        assert det.y == 20
        assert det.w == 100
        assert det.h == 120
        assert det.confidence == 0.95
        assert det.landmarks is None
        assert det.face_crop is None

    def test_face_detection_with_crop(self, sample_face_crop):
        det = FaceDetection(
            x=0, y=0, w=64, h=64,
            confidence=0.88,
            face_crop=sample_face_crop
        )
        assert det.face_crop is not None
        assert det.face_crop.shape == (64, 64, 3)


# ─────────────────────────────────────────────────────────────────────────────
# Integration Test
# ─────────────────────────────────────────────────────────────────────────────

class TestIntegration:

    def test_full_pipeline_single_frame(self, mock_config, sample_frame, tmp_path):
        """
        End-to-end test: simulate processing a single frame through all modules.
        """
        # Init
        clf = EmotionClassifier(model_type="mock")
        renderer = HUDRenderer(mock_config)

        # Simulate a detected face
        face_crop = sample_frame[100:200, 150:250].copy()
        det = FaceDetection(x=150, y=100, w=100, h=100, confidence=0.9, face_crop=face_crop)

        # Predict
        scores = clf.predict(face_crop, face_index=0)
        assert isinstance(scores, dict)
        assert abs(sum(scores.values()) - 1.0) < 1e-5

        # Render
        output = renderer.render(sample_frame, [det], [scores], fps=30.0)
        assert output is not None
        assert output.shape == sample_frame.shape

        # Session logging
        logger_inst = SessionLogger(
            db_path=str(tmp_path / "integration.db"),
            csv_dir=str(tmp_path / "csv")
        )
        sid = logger_inst.start_session("test")
        dominant, confidence = EmotionClassifier.get_dominant_emotion(scores)
        logger_inst.log_frame(scores, 0, dominant, confidence)
        logger_inst.end_session(total_frames=1)

        summary = logger_inst.get_session_summary(sid)
        assert summary is not None
