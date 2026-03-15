"""
============================================================
Video Recorder Module
Handles saving processed video output with all overlays.
============================================================
"""

import cv2
import os
from datetime import datetime
from loguru import logger


class VideoRecorder:
    """Records and saves output video with all overlays."""

    def __init__(self, output_dir: str = "outputs/videos", codec: str = "mp4v"):
        self.output_dir = output_dir
        self.codec = codec
        self._writer: cv2.VideoWriter = None
        self._output_path: str = ""
        self._frame_count = 0
        self.is_recording = False

        os.makedirs(output_dir, exist_ok=True)

    def start_recording(self, frame_size: tuple, fps: float = 30.0) -> str:
        """
        Start recording.

        Args:
            frame_size: (width, height)
            fps: Frames per second

        Returns:
            Output file path
        """
        if self.is_recording:
            logger.warning("Already recording")
            return self._output_path

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"emotion_recording_{timestamp}.mp4"
        self._output_path = os.path.join(self.output_dir, filename)

        fourcc = cv2.VideoWriter_fourcc(*self.codec)
        self._writer = cv2.VideoWriter(
            self._output_path, fourcc, fps, frame_size
        )

        if not self._writer.isOpened():
            logger.error(f"Failed to open video writer: {self._output_path}")
            self._writer = None
            return ""

        self.is_recording = True
        self._frame_count = 0
        logger.info(f"Recording started: {self._output_path}")
        return self._output_path

    def write_frame(self, frame):
        """Write a frame to the recording."""
        if not self.is_recording or self._writer is None:
            return
        try:
            self._writer.write(frame)
            self._frame_count += 1
        except Exception as e:
            logger.error(f"Frame write error: {e}")

    def stop_recording(self) -> str:
        """
        Stop recording and finalize the file.

        Returns:
            Path to saved video file
        """
        if not self.is_recording:
            return ""

        if self._writer is not None:
            self._writer.release()
            self._writer = None

        self.is_recording = False
        path = self._output_path
        logger.success(
            f"Recording saved: {path} | {self._frame_count} frames"
        )
        return path

    def toggle_recording(self, frame_size: tuple, fps: float = 30.0) -> bool:
        """Toggle recording on/off. Returns True if now recording."""
        if self.is_recording:
            self.stop_recording()
            return False
        else:
            self.start_recording(frame_size, fps)
            return True

    def release(self):
        """Release all resources."""
        if self.is_recording:
            self.stop_recording()
