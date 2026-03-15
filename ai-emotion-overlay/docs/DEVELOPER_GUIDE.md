# Developer Guide

## Project Architecture

```
Input (Webcam/Video)
    │
    ▼
FaceDetector (MediaPipe)
    │  Returns: List[FaceDetection]
    ▼
EmotionClassifier (FER / DeepFace / Custom CNN)
    │  Per face: Dict[emotion -> score]
    │  Applies prediction smoothing (sliding window average)
    ▼
HUDRenderer (OpenCV)
    │  Draws: bounding box, label, HUD panel, persona overlay
    ▼
Output Frame
    ├── Display (cv2.imshow)
    ├── VideoRecorder (cv2.VideoWriter)
    └── SessionLogger (SQLite)
```

---

## Adding a New Emotion Model Backend

1. Open `backend/emotion_classifier.py`
2. Add an `_init_yourmodel()` method
3. Add an `_infer_yourmodel()` method returning `Dict[str, float]`
4. Register in `_initialize_model()` and `_run_inference()`

Example:
```python
def _init_yourmodel(self):
    import yourlib
    self._model = yourlib.load()

def _infer_yourmodel(self, face_crop: np.ndarray) -> Dict[str, float]:
    result = self._model.predict(face_crop)
    return self._normalize_scores(result)
```

---

## Adding a New Overlay Element

1. Open `backend/hud_renderer.py`
2. Add your drawing method (e.g., `_draw_my_element()`)
3. Call it inside the `render()` method
4. Add a toggle flag and `toggle_my_element()` method

---

## Database Schema

**sessions table:**
```sql
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time TEXT NOT NULL,
    end_time TEXT,
    total_frames INTEGER DEFAULT 0,
    source TEXT DEFAULT 'webcam',
    notes TEXT
);
```

**emotion_logs table:**
```sql
CREATE TABLE emotion_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    timestamp REAL NOT NULL,
    elapsed_seconds REAL NOT NULL,
    face_index INTEGER DEFAULT 0,
    dominant_emotion TEXT,
    confidence REAL,
    angry REAL, disgust REAL, fear REAL,
    happy REAL, neutral REAL, sad REAL, surprise REAL,
    FOREIGN KEY (session_id) REFERENCES sessions (id)
);
```

---

## Running Tests

```bash
# All tests
pytest tests/ -v

# Specific test class
pytest tests/test_all.py::TestEmotionClassifier -v

# With coverage report
pip install pytest-cov
pytest tests/ --cov=backend --cov-report=html
```

---

## Code Standards

- **PEP 8** for all Python code
- **Type hints** on all function signatures
- **Docstrings** on all public classes and methods
- **Loguru** for all logging (not `print`)
- **Error handling** — all external calls wrapped in try/except
- Max line length: 100 characters

---

## Performance Guidelines

- Keep inference under 20ms per frame for 30+ FPS
- Use prediction smoothing (deque) instead of per-frame reset
- Avoid creating new arrays inside the render loop
- Use `cv2.addWeighted` for transparent overlays (faster than PIL)
- Buffer SQLite writes (flush every 50 frames, not every frame)

---

## Adding New Persona Assets

1. Create or find a PNG with alpha transparency
2. Name it according to the emotion mapping in `configs/config.yaml`
3. Place in `assets/overlays/`
4. The overlay will auto-load on next app start

Asset requirements:
- Format: PNG with BGRA (4 channels including alpha)
- Size: 200×150px minimum, 400×300px recommended
- Background: fully transparent (alpha=0)
- Subject: centered with some padding

---

## API Development

To add a new endpoint to the FastAPI backend:

```python
@app.get("/api/my-endpoint")
async def my_endpoint(param: str = "default"):
    """Describe what this does."""
    # Your logic here
    return {"result": "value"}
```

Test with: `http://localhost:8000/docs` (auto-generated Swagger UI)

---

## Building Docker Image

```bash
docker build -t ai-emotion-overlay:latest .
docker run -p 8000:8000 ai-emotion-overlay:latest
```

---

## Building EXE

```bash
pip install pyinstaller
pyinstaller build.spec --clean
# Output: dist/AI_Emotion_Overlay.exe
```
