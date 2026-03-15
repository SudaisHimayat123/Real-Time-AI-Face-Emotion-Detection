"""
============================================================
Face Detection Module (v2.0 — Updated MediaPipe Task API)
Uses MediaPipe Face Detector Task for high accuracy, low latency detection.
Updated to use new MediaPipe Tasks API (not deprecated solutions).
============================================================
"""

import cv2
import numpy as np
from loguru import logger
from dataclasses import dataclass
from typing import List, Tuple, Optional
import os

try:
    from mediapipe.tasks import vision
    from mediapipe.tasks.python import vision as vision_module
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    logger.warning("❌ MediaPipe Tasks API not available")


@dataclass
class FaceDetection:
    """Represents a single detected face with bounding box and landmarks."""
    x: int           # Top-left x
    y: int           # Top-left y
    w: int           # Width
    h: int           # Height
    confidence: float
    landmarks: Optional[List[Tuple[int, int]]] = None  # Key facial points
    face_crop: Optional[np.ndarray] = None             # Cropped face region


class FaceDetector:
    """
    Multi-backend face detector supporting MediaPipe Tasks API and OpenCV DNN.
    Uses new MediaPipe Face Detector Task (not deprecated solutions API).
    """

    def __init__(self, min_confidence: float = 0.6, model_selection: int = 0):
        """
        Initialize face detector.

        Args:
            min_confidence: Minimum detection confidence threshold (0.0 - 1.0)
            model_selection: 0 = short range (2m), 1 = full range (5m)
        """
        self.min_confidence = min_confidence
        self.model_selection = model_selection
        self._backend = None
        self._face_detector = None
        self._dnn_net = None

        self._initialize_detector()

    def _initialize_detector(self):
        """Initialize the best available face detection backend."""
        if MEDIAPIPE_AVAILABLE:
            try:
                # New MediaPipe Face Detector Task API
                base_options = vision_module.BaseOptions(
                    model_asset_path="mediapipe/face_detector/blaze_face_short_range.tflite"
                )
                options = vision_module.FaceDetectorOptions(
                    base_options=base_options,
                    min_detection_confidence=self.min_confidence
                )
                self._face_detector = vision_module.FaceDetector.create_from_options(options)
                self._backend = "mediapipe_task"
                logger.success("✅ Face Detector initialized: MediaPipe Task API")
            except Exception as e:
                logger.warning(f"⚠️  MediaPipe Task API init failed: {e}")
                self._backend = "opencv"
                self._init_opencv_dnn()
        else:
            self._backend = "opencv"
            self._init_opencv_dnn()

    def _init_opencv_dnn(self):
        """Initialize OpenCV DNN face detector as fallback."""
        try:
            # Use pre-trained Caffe model for face detection
            model_dir = os.path.join(cv2.data.haarcascades)
            proto_path = os.path.join(model_dir, "../../../extra/opencv_contrib_data/face_detection_yunet/face_detection_yunet_2023mar.onnx")
            
            if os.path.exists(proto_path):
                self._dnn_net = cv2.FaceDetectorYN.create(
                    model=proto_path,
                    config="",
                    input_size=(320, 320),
                    score_threshold=self.min_confidence,
                    nms_threshold=0.4,
                    top_k=5000,
                    backend_id=cv2.dnn.DNN_BACKEND_OPENCV,
                    target_id=cv2.dnn.DNN_TARGET_CPU
                )
                logger.success("✅ Face Detector initialized: OpenCV YuNet")
            else:
                logger.warning("⚠️  YuNet model not found, using basic cascade")
        except Exception as e:
            logger.warning(f"⚠️  OpenCV DNN init issue: {e}")

    def detect(self, frame: np.ndarray) -> List[FaceDetection]:
        """
        Detect all faces in a given frame.

        Args:
            frame: BGR numpy array from OpenCV

        Returns:
            List of FaceDetection objects
        """
        if frame is None or frame.size == 0:
            return []

        h, w = frame.shape[:2]
        detections = []

        try:
            if self._backend == "mediapipe_task":
                detections = self._detect_mediapipe_task(frame, h, w)
            else:
                detections = self._detect_opencv_dnn(frame, h, w)
        except Exception as e:
            logger.debug(f"Face detection error: {e}")

        return detections

    def _detect_mediapipe_task(self, frame: np.ndarray, h: int, w: int) -> List[FaceDetection]:
        """Detect faces using new MediaPipe Face Detector Task API."""
        try:
            import mediapipe as mp
            from mediapipe.framework.formats import detection_pb2
            
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Create MediaImage from numpy array
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            
            # Run detection
            detection_result = self._face_detector.detect(mp_image)
            
            detections = []
            if not detection_result.detections:
                return detections
            
            # Process each detected face
            for detection in detection_result.detections:
                confidence = detection.categories[0].score if detection.categories else 0.0
                
                if confidence < self.min_confidence:
                    continue
                
                bbox = detection.bounding_box
                
                # Convert bounding box to pixel coordinates
                x = max(0, int(bbox.origin_x))
                y = max(0, int(bbox.origin_y))
                bw = max(1, int(bbox.width))
                bh = max(1, int(bbox.height))
                
                # Ensure within bounds
                x = min(x, w - 1)
                y = min(y, h - 1)
                bw = min(bw, w - x)
                bh = min(bh, h - y)
                
                # Extract face crop
                face_crop = frame[y:y + bh, x:x + bw].copy()
                
                # Extract key points (landmarks) if available
                landmarks = []
                if hasattr(detection, 'keypoints') and detection.keypoints:
                    for keypoint in detection.keypoints:
                        kx = int(keypoint.x * w)
                        ky = int(keypoint.y * h)
                        landmarks.append((kx, ky))
                
                detections.append(FaceDetection(
                    x=x, y=y, w=bw, h=bh,
                    confidence=float(confidence),
                    landmarks=landmarks if landmarks else None,
                    face_crop=face_crop
                ))
            
            return detections
            
        except Exception as e:
            logger.debug(f"MediaPipe Task detection error: {e}")
            return []

    def _detect_mediapipe(self, frame: np.ndarray, h: int, w: int) -> List[FaceDetection]:
        """Detect faces using MediaPipe (deprecated - kept for compatibility)."""
        # MediaPipe expects RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self._mp_face_detection.process(rgb_frame)

        detections = []
        if not results.detections:
            return detections

        for detection in results.detections:
            score = detection.score[0] if detection.score else 0.0
            if score < self.min_confidence:
                continue

            bbox = detection.location_data.relative_bounding_box

            # Convert relative coords to absolute pixel coords
            x = max(0, int(bbox.xmin * w))
            y = max(0, int(bbox.ymin * h))
            bw = min(int(bbox.width * w), w - x)
            bh = min(int(bbox.height * h), h - y)

            # Validate bounding box
            if bw <= 0 or bh <= 0:
                continue

            # Extract face crop
            face_crop = frame[y:y + bh, x:x + bw].copy()

            # Extract key points if available
            landmarks = []
            kps = detection.location_data.relative_keypoints
            for kp in kps:
                kx = int(kp.x * w)
                ky = int(kp.y * h)
                landmarks.append((kx, ky))

            detections.append(FaceDetection(
                x=x, y=y, w=bw, h=bh,
                confidence=float(score),
                landmarks=landmarks,
                face_crop=face_crop
            ))

        return detections

    def _detect_opencv_dnn(self, frame: np.ndarray, h: int, w: int) -> List[FaceDetection]:
        """Fallback: Simple OpenCV face detection using Haar Cascades."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Use DNN-based detector if cascade not desired
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(48, 48)
        )

        detections = []
        for (x, y, fw, fh) in faces:
            face_crop = frame[y:y + fh, x:x + fw].copy()
            detections.append(FaceDetection(
                x=int(x), y=int(y), w=int(fw), h=int(fh),
                confidence=0.9,  # Haar doesn't return confidence
                face_crop=face_crop
            ))

        return detections

    def get_face_mesh_landmarks(self, frame: np.ndarray) -> Optional[object]:
        """
        Get detailed 468 face mesh landmarks for AR/persona overlay alignment.

        Args:
            frame: BGR frame

        Returns:
            MediaPipe face mesh results or None
        """
        if self._mp_face_mesh is None:
            return None

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return self._mp_face_mesh.process(rgb)

    def release(self):
        """Release detector resources."""
        if self._mp_face_detection:
            self._mp_face_detection.close()
        if self._mp_face_mesh:
            self._mp_face_mesh.close()
        logger.info("Face detector resources released")
