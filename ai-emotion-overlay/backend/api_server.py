"""
============================================================
FastAPI Web Backend
REST API endpoints for the web version of the application.
Enables browser-based webcam capture with WebSocket streaming.
============================================================
"""

import os
import cv2
import base64
import asyncio
import numpy as np
import time
from typing import Optional
from io import BytesIO

from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
from loguru import logger

# ── Internal imports ─────────────────────────────────────────────────────────
from backend.face_detector import FaceDetector
from backend.emotion_classifier import EmotionClassifier
from backend.hud_renderer import HUDRenderer
from backend.session_logger import SessionLogger
from backend.video_recorder import VideoRecorder
import yaml

# ── Load config ───────────────────────────────────────────────────────────────
with open("configs/config.yaml", "r") as f:
    CONFIG = yaml.safe_load(f)

# ── Initialize components ─────────────────────────────────────────────────────
face_detector = FaceDetector(
    min_confidence=CONFIG["model"]["face_detection_confidence"]
)
emotion_classifier = EmotionClassifier(
    model_type=CONFIG["model"]["emotion_model"],
    smoothing_window=CONFIG["model"]["smoothing_window"]
)
hud_renderer = HUDRenderer(CONFIG)
session_logger = SessionLogger(
    db_path=CONFIG["session"]["db_path"],
    csv_dir=CONFIG["session"]["csv_dir"]
)
video_recorder = VideoRecorder(
    output_dir=CONFIG["recording"]["output_dir"]
)

# ── FastAPI app setup ─────────────────────────────────────────────────────────
app = FastAPI(
    title="AI Face Emotion Overlay API",
    description="Real-time face emotion detection with HUD overlay",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (if frontend built)
if os.path.exists("frontend/dist"):
    app.mount("/static", StaticFiles(directory="frontend/dist"), name="static")


# ═══════════════════════════════════════════════════════════════════════════════
# REST Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/")
async def root():
    return {"status": "running", "message": "AI Face Emotion Overlay API"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "model": CONFIG["model"]["emotion_model"],
        "version": "1.0.0"
    }


@app.post("/api/analyze-frame")
async def analyze_frame(image: UploadFile = File(...)):
    """
    Analyze a single uploaded image frame.
    Returns detected faces, emotion scores, and base64 processed image.

    Request: multipart/form-data with 'image' field (JPEG/PNG)
    Response: {faces: [...], processed_image: base64_string}
    """
    try:
        # Read image bytes and decode
        img_bytes = await image.read()
        nparr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            raise HTTPException(status_code=400, detail="Invalid image format")

        # Run detection pipeline
        detections = face_detector.detect(frame)
        emotion_results = []
        faces_data = []

        for i, det in enumerate(detections):
            scores = emotion_classifier.predict(det.face_crop, face_index=i)
            emotion_results.append(scores)

            from backend.emotion_classifier import EmotionClassifier as EC
            dominant, confidence = EC.get_dominant_emotion(scores)
            faces_data.append({
                "face_index": i,
                "bbox": {"x": det.x, "y": det.y, "w": det.w, "h": det.h},
                "dominant_emotion": dominant,
                "confidence": round(confidence, 3),
                "scores": {k: round(v, 3) for k, v in scores.items()}
            })

        # Render overlays
        processed = hud_renderer.render(frame, detections, emotion_results)

        # Encode output as base64 JPEG
        _, buffer = cv2.imencode(".jpg", processed, [cv2.IMWRITE_JPEG_QUALITY, 85])
        img_b64 = base64.b64encode(buffer).decode("utf-8")

        return {
            "success": True,
            "face_count": len(detections),
            "faces": faces_data,
            "processed_image": f"data:image/jpeg;base64,{img_b64}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"analyze_frame error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload-video")
async def upload_video(video: UploadFile = File(...)):
    """
    Upload and process a pre-recorded video file.
    Returns processing job ID.
    """
    try:
        # Save uploaded video
        os.makedirs("outputs/uploads", exist_ok=True)
        upload_path = f"outputs/uploads/{video.filename}"
        with open(upload_path, "wb") as f:
            content = await video.read()
            f.write(content)

        logger.info(f"Video uploaded: {upload_path} ({len(content)} bytes)")
        return {
            "success": True,
            "upload_path": upload_path,
            "message": "Video uploaded. Use /api/process-video to process."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/start-session")
async def start_session(source: str = "webcam"):
    """Start a new emotion logging session."""
    session_id = session_logger.start_session(source=source)
    return {"session_id": session_id, "status": "started"}


@app.post("/api/end-session")
async def end_session(total_frames: int = 0):
    """End the current session."""
    session_logger.end_session(total_frames=total_frames)
    return {"status": "ended", "session_id": session_logger.session_id}


@app.get("/api/export-csv")
async def export_csv(session_id: Optional[int] = None):
    """Export session emotion data as CSV file download."""
    csv_path = session_logger.export_csv(session_id=session_id)
    if not csv_path or not os.path.exists(csv_path):
        raise HTTPException(status_code=404, detail="CSV export failed or no session data")
    return FileResponse(
        csv_path,
        media_type="text/csv",
        filename=os.path.basename(csv_path)
    )


@app.get("/api/sessions")
async def get_sessions():
    """Get all recorded sessions."""
    sessions = session_logger.get_all_sessions()
    return {"sessions": sessions}


@app.get("/api/session/{session_id}/summary")
async def get_session_summary(session_id: int):
    """Get statistical summary for a session."""
    summary = session_logger.get_session_summary(session_id=session_id)
    return {"session_id": session_id, "summary": summary}


@app.get("/api/session/{session_id}/timeline")
async def get_session_timeline(session_id: int, downsample: int = 5):
    """Get emotion timeline for graphing."""
    timeline = session_logger.get_emotion_timeline(
        session_id=session_id,
        downsample=downsample
    )
    return {"session_id": session_id, "timeline": timeline}


@app.get("/api/recordings")
async def list_recordings():
    """List all saved recordings."""
    rec_dir = CONFIG["recording"]["output_dir"]
    files = []
    if os.path.exists(rec_dir):
        for f in os.listdir(rec_dir):
            if f.endswith(".mp4"):
                path = os.path.join(rec_dir, f)
                files.append({
                    "filename": f,
                    "path": path,
                    "size_mb": round(os.path.getsize(path) / (1024 * 1024), 2)
                })
    return {"recordings": files}


@app.get("/api/download-recording/{filename}")
async def download_recording(filename: str):
    """Download a saved recording."""
    path = os.path.join(CONFIG["recording"]["output_dir"], filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Recording not found")
    return FileResponse(path, media_type="video/mp4", filename=filename)


# ═══════════════════════════════════════════════════════════════════════════════
# WebSocket — Real-time Frame Streaming
# ═══════════════════════════════════════════════════════════════════════════════

@app.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time frame processing.
    Client sends: base64-encoded JPEG frames
    Server returns: JSON with processed image + emotion data
    """
    await websocket.accept()
    logger.info("WebSocket client connected")
    frame_count = 0
    fps_timer = time.time()
    fps = 0.0

    try:
        while True:
            # Receive frame from client
            data = await websocket.receive_text()

            # Decode base64 image
            if "," in data:
                data = data.split(",", 1)[1]

            img_bytes = base64.b64decode(data)
            nparr = np.frombuffer(img_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if frame is None:
                continue

            # Processing pipeline
            detections = face_detector.detect(frame)
            emotion_results = []

            faces_data = []
            for i, det in enumerate(detections):
                scores = emotion_classifier.predict(det.face_crop, face_index=i)
                emotion_results.append(scores)

                from backend.emotion_classifier import EmotionClassifier as EC
                dominant, confidence = EC.get_dominant_emotion(scores)
                faces_data.append({
                    "dominant": dominant,
                    "confidence": round(confidence, 3),
                    "scores": {k: round(v, 3) for k, v in scores.items()}
                })

                # Log to session
                if session_logger.session_id:
                    session_logger.log_frame(scores, i, dominant, confidence)

            # Calculate FPS
            frame_count += 1
            elapsed = time.time() - fps_timer
            if elapsed >= 1.0:
                fps = frame_count / elapsed
                frame_count = 0
                fps_timer = time.time()

            # Render overlays
            processed = hud_renderer.render(
                frame, detections, emotion_results,
                fps=fps, recording=video_recorder.is_recording
            )

            # Record if active
            if video_recorder.is_recording:
                video_recorder.write_frame(processed)

            # Encode output
            _, buffer = cv2.imencode(".jpg", processed, [cv2.IMWRITE_JPEG_QUALITY, 80])
            img_b64 = base64.b64encode(buffer).decode("utf-8")

            # Send back result
            await websocket.send_json({
                "fps": round(fps, 1),
                "face_count": len(detections),
                "faces": faces_data,
                "image": f"data:image/jpeg;base64,{img_b64}"
            })

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# Run server
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run("backend.api_server:app", host=host, port=port, reload=False)
