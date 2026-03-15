"""
============================================================
Session Logger Module
Tracks emotion data over session duration, logs to SQLite,
exports CSV, and generates session emotion history charts.
============================================================
"""

import os
import csv
import sqlite3
import time
from datetime import datetime
from typing import Dict, List, Optional
import numpy as np
from loguru import logger


class SessionLogger:
    """
    Logs per-frame emotion data to SQLite and exports to CSV.
    Also provides session history for graph visualization.
    """

    def __init__(self, db_path: str = "outputs/sessions.db", csv_dir: str = "outputs/csv"):
        self.db_path = db_path
        self.csv_dir = csv_dir
        self.session_id: Optional[int] = None
        self.session_start: Optional[float] = None
        self._buffer: List[dict] = []
        self._buffer_size = 50  # Flush to DB every N records

        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
        os.makedirs(csv_dir, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database schema."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    total_frames INTEGER DEFAULT 0,
                    source TEXT DEFAULT 'webcam',
                    notes TEXT
                )
            """)

            # Emotion logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS emotion_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    timestamp REAL NOT NULL,
                    elapsed_seconds REAL NOT NULL,
                    face_index INTEGER DEFAULT 0,
                    dominant_emotion TEXT,
                    confidence REAL,
                    angry REAL,
                    disgust REAL,
                    fear REAL,
                    happy REAL,
                    neutral REAL,
                    sad REAL,
                    surprise REAL,
                    FOREIGN KEY (session_id) REFERENCES sessions (id)
                )
            """)

            conn.commit()
            conn.close()
            logger.info(f"Database initialized: {self.db_path}")
        except Exception as e:
            logger.error(f"DB init error: {e}")

    def start_session(self, source: str = "webcam") -> int:
        """
        Start a new logging session.

        Args:
            source: Input source ('webcam', 'video_file', etc.)

        Returns:
            New session ID
        """
        self.session_start = time.time()
        start_time = datetime.now().isoformat()

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sessions (start_time, source) VALUES (?, ?)",
                (start_time, source)
            )
            self.session_id = cursor.lastrowid
            conn.commit()
            conn.close()
            logger.info(f"Session {self.session_id} started [{source}]")
        except Exception as e:
            logger.error(f"Failed to start session: {e}")
            self.session_id = 0

        return self.session_id

    def log_frame(
        self,
        emotion_scores: Dict[str, float],
        face_index: int = 0,
        dominant: str = "neutral",
        confidence: float = 0.0
    ):
        """
        Log emotion data for a single frame.

        Args:
            emotion_scores: Dict of emotion -> score
            face_index: Which face (0-indexed)
            dominant: Dominant emotion label
            confidence: Confidence of dominant emotion
        """
        if self.session_id is None:
            return

        now = time.time()
        elapsed = now - (self.session_start or now)

        record = {
            "session_id": self.session_id,
            "timestamp": now,
            "elapsed_seconds": round(elapsed, 2),
            "face_index": face_index,
            "dominant_emotion": dominant,
            "confidence": round(confidence, 4),
            "angry": round(emotion_scores.get("angry", 0.0), 4),
            "disgust": round(emotion_scores.get("disgust", 0.0), 4),
            "fear": round(emotion_scores.get("fear", 0.0), 4),
            "happy": round(emotion_scores.get("happy", 0.0), 4),
            "neutral": round(emotion_scores.get("neutral", 0.0), 4),
            "sad": round(emotion_scores.get("sad", 0.0), 4),
            "surprise": round(emotion_scores.get("surprise", 0.0), 4),
        }

        self._buffer.append(record)

        # Flush buffer to DB periodically
        if len(self._buffer) >= self._buffer_size:
            self._flush_buffer()

    def _flush_buffer(self):
        """Write buffered records to SQLite."""
        if not self._buffer:
            return
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.executemany("""
                INSERT INTO emotion_logs
                (session_id, timestamp, elapsed_seconds, face_index,
                 dominant_emotion, confidence, angry, disgust, fear,
                 happy, neutral, sad, surprise)
                VALUES
                (:session_id, :timestamp, :elapsed_seconds, :face_index,
                 :dominant_emotion, :confidence, :angry, :disgust, :fear,
                 :happy, :neutral, :sad, :surprise)
            """, self._buffer)
            conn.commit()
            conn.close()
            self._buffer.clear()
        except Exception as e:
            logger.error(f"Buffer flush error: {e}")

    def end_session(self, total_frames: int = 0):
        """
        End the current session and flush remaining data.

        Args:
            total_frames: Total frames processed in the session
        """
        self._flush_buffer()

        if self.session_id is None:
            return

        end_time = datetime.now().isoformat()
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE sessions SET end_time=?, total_frames=? WHERE id=?",
                (end_time, total_frames, self.session_id)
            )
            conn.commit()
            conn.close()

            duration = time.time() - (self.session_start or time.time())
            logger.info(
                f"Session {self.session_id} ended | "
                f"Duration: {duration:.1f}s | Frames: {total_frames}"
            )
        except Exception as e:
            logger.error(f"Failed to end session: {e}")

    def export_csv(self, session_id: Optional[int] = None) -> str:
        """
        Export session emotion data as CSV.

        Args:
            session_id: Session to export (default: current session)

        Returns:
            Path to exported CSV file
        """
        self._flush_buffer()
        sid = session_id or self.session_id
        if sid is None:
            logger.warning("No session to export")
            return ""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"session_{sid}_{timestamp}.csv"
        filepath = os.path.join(self.csv_dir, filename)

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM emotion_logs WHERE session_id=? ORDER BY elapsed_seconds",
                (sid,)
            )
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            conn.close()

            with open(filepath, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(columns)
                writer.writerows(rows)

            logger.success(f"CSV exported: {filepath} ({len(rows)} records)")
            return filepath
        except Exception as e:
            logger.error(f"CSV export error: {e}")
            return ""

    def get_session_summary(self, session_id: Optional[int] = None) -> dict:
        """
        Get a statistical summary of the session.

        Returns:
            Dict with dominant emotions, average scores, duration, etc.
        """
        sid = session_id or self.session_id
        if sid is None:
            return {}

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Aggregate emotion averages
            cursor.execute("""
                SELECT
                    COUNT(*) as total_frames,
                    AVG(angry) as avg_angry,
                    AVG(disgust) as avg_disgust,
                    AVG(fear) as avg_fear,
                    AVG(happy) as avg_happy,
                    AVG(neutral) as avg_neutral,
                    AVG(sad) as avg_sad,
                    AVG(surprise) as avg_surprise
                FROM emotion_logs WHERE session_id=?
            """, (sid,))
            row = cursor.fetchone()
            cols = [d[0] for d in cursor.description]
            conn.close()

            summary = dict(zip(cols, row)) if row else {}
            return summary
        except Exception as e:
            logger.error(f"Summary error: {e}")
            return {}

    def get_all_sessions(self) -> List[dict]:
        """List all recorded sessions."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sessions ORDER BY id DESC")
            rows = cursor.fetchall()
            cols = [d[0] for d in cursor.description]
            conn.close()
            return [dict(zip(cols, row)) for row in rows]
        except Exception as e:
            logger.error(f"Get sessions error: {e}")
            return []

    def get_emotion_timeline(
        self,
        session_id: Optional[int] = None,
        downsample: int = 1
    ) -> Dict[str, List]:
        """
        Get emotion timeline data for graphing.

        Args:
            session_id: Session to retrieve
            downsample: Take every Nth record (for performance)

        Returns:
            Dict with 'time' list and per-emotion score lists
        """
        sid = session_id or self.session_id
        if sid is None:
            return {}

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT elapsed_seconds, angry, disgust, fear, happy, neutral, sad, surprise
                FROM emotion_logs
                WHERE session_id=?
                ORDER BY elapsed_seconds
            """, (sid,))
            rows = cursor.fetchall()
            conn.close()

            # Downsample
            rows = rows[::downsample]

            timeline = {
                "time": [r[0] for r in rows],
                "angry": [r[1] for r in rows],
                "disgust": [r[2] for r in rows],
                "fear": [r[3] for r in rows],
                "happy": [r[4] for r in rows],
                "neutral": [r[5] for r in rows],
                "sad": [r[6] for r in rows],
                "surprise": [r[7] for r in rows],
            }
            return timeline
        except Exception as e:
            logger.error(f"Timeline retrieval error: {e}")
            return {}
