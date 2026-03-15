# API Documentation

Base URL: `http://localhost:8000`

Interactive docs: `http://localhost:8000/docs` (Swagger UI)

---

## REST Endpoints

### Health Check
```
GET /health
```
Response:
```json
{
  "status": "healthy",
  "model": "fer",
  "version": "1.0.0"
}
```

---

### Analyze Single Frame
```
POST /api/analyze-frame
Content-Type: multipart/form-data
Body: image (file, JPEG/PNG)
```
Response:
```json
{
  "success": true,
  "face_count": 1,
  "faces": [
    {
      "face_index": 0,
      "bbox": { "x": 150, "y": 100, "w": 120, "h": 140 },
      "dominant_emotion": "happy",
      "confidence": 0.923,
      "scores": {
        "angry": 0.012,
        "disgust": 0.005,
        "fear": 0.008,
        "happy": 0.923,
        "neutral": 0.035,
        "sad": 0.010,
        "surprise": 0.007
      }
    }
  ],
  "processed_image": "data:image/jpeg;base64,..."
}
```

---

### Upload Video File
```
POST /api/upload-video
Content-Type: multipart/form-data
Body: video (file, MP4/AVI)
```
Response:
```json
{
  "success": true,
  "upload_path": "outputs/uploads/video.mp4",
  "message": "Video uploaded."
}
```

---

### Session Management

**Start session:**
```
POST /api/start-session?source=webcam
```
Response: `{ "session_id": 5, "status": "started" }`

**End session:**
```
POST /api/end-session?total_frames=1200
```
Response: `{ "status": "ended", "session_id": 5 }`

---

### Session Data

**List all sessions:**
```
GET /api/sessions
```

**Session summary:**
```
GET /api/session/{session_id}/summary
```
Response:
```json
{
  "session_id": 5,
  "summary": {
    "total_frames": 1200,
    "avg_happy": 0.42,
    "avg_neutral": 0.31,
    "avg_sad": 0.10,
    ...
  }
}
```

**Emotion timeline:**
```
GET /api/session/{session_id}/timeline?downsample=5
```
Response:
```json
{
  "session_id": 5,
  "timeline": {
    "time": [0.0, 1.5, 3.0, ...],
    "happy": [0.12, 0.85, 0.90, ...],
    "neutral": [0.80, 0.10, 0.05, ...],
    ...
  }
}
```

---

### Export & Download

**Export CSV:**
```
GET /api/export-csv?session_id=5
```
Returns: CSV file download

**List recordings:**
```
GET /api/recordings
```

**Download recording:**
```
GET /api/download-recording/{filename}
```
Returns: MP4 file download

---

## WebSocket — Real-time Streaming

```
WS /ws/stream
```

**Client sends:** Base64-encoded JPEG frame (data URL format)
```
data:image/jpeg;base64,/9j/4AAQSkZJRgAB...
```

**Server returns:** JSON object
```json
{
  "fps": 28.5,
  "face_count": 1,
  "faces": [
    {
      "dominant": "happy",
      "confidence": 0.91,
      "scores": {
        "angry": 0.01,
        "happy": 0.91,
        ...
      }
    }
  ],
  "image": "data:image/jpeg;base64,..."
}
```

### JavaScript Example
```javascript
const ws = new WebSocket("ws://localhost:8000/ws/stream");

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  document.getElementById("output").src = data.image;
  console.log("FPS:", data.fps);
  console.log("Emotion:", data.faces[0]?.dominant);
};

// Send frame from canvas
function sendFrame(canvas) {
  const dataUrl = canvas.toDataURL("image/jpeg", 0.7);
  ws.send(dataUrl);
}
```

---

## Error Responses

All endpoints return standard HTTP error codes:

| Code | Meaning |
|------|---------|
| 400 | Bad request (invalid image, missing params) |
| 404 | Resource not found |
| 500 | Internal server error |

Error body:
```json
{
  "detail": "Error description here"
}
```
