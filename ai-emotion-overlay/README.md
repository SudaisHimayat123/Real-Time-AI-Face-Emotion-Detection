# 🧠 AI Face Emotion Overlay

Real-time facial emotion detection with HUD overlay, bounding boxes, persona AR filters, and session logging. Built with Python, OpenCV, MediaPipe, and FER.

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://python.org)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.8%2B-green)](https://opencv.org)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10%2B-orange)](https://mediapipe.dev)

---

## 📸 Features

| Feature | Status |
|---------|--------|
| Real-time webcam detection | ✅ |
| Multi-face detection | ✅ |
| 7-class emotion classification | ✅ |
| HUD progress bars | ✅ |
| Bounding box + emotion label | ✅ |
| Prediction smoothing (anti-flicker) | ✅ |
| Session emotion logging (SQLite) | ✅ |
| CSV export | ✅ |
| Video recording | ✅ |
| Persona / AR overlays | ✅ |
| Emotion history graph (matplotlib) | ✅ |
| Admin dashboard (CLI) | ✅ |
| FastAPI web backend | ✅ |
| React web frontend | ✅ |
| Docker support | ✅ |

---

## 🚀 Quick Start (Desktop App — Recommended)

### 1. Clone / Download

```bash
git clone https://github.com/yourname/ai-emotion-overlay.git
cd ai-emotion-overlay
```

### 2. Create virtual environment

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note:** The `fer` library and `mediapipe` will be downloaded automatically. First run may take a moment while models are loaded.

### 4. Run the desktop app

```bash
python main.py
```

### CLI Options

```bash
# Use specific webcam (default is 0)
python main.py --source 1

# Process a saved video file
python main.py --source path/to/video.mp4

# Use a different emotion model
python main.py --model deepface

# Start with HUD hidden
python main.py --no-hud

# Auto-start recording
python main.py --record

# Enable persona overlays
python main.py --persona
```

---

## ⌨️ Keyboard Controls (Desktop App)

| Key | Action |
|-----|--------|
| `q` or `ESC` | Quit |
| `h` | Toggle HUD panel |
| `b` | Toggle bounding boxes |
| `p` | Toggle persona overlays |
| `r` | Toggle video recording |
| `s` | Export session CSV |
| `SPACE` | Pause / Resume |

---

## 🌐 Web Version (FastAPI + React)

### Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Start API server
python -m backend.api_server
# API available at: http://localhost:8000
# Docs at: http://localhost:8000/docs
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# Frontend at: http://localhost:3000
```

### Docker (one command)

```bash
docker-compose up --build
```

---

## 📁 Project Structure

```
ai-emotion-overlay/
├── main.py                     ← Desktop app entry point
├── admin_dashboard.py          ← CLI session viewer
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── build.spec                  ← PyInstaller EXE config
│
├── backend/
│   ├── face_detector.py        ← MediaPipe face detection
│   ├── emotion_classifier.py   ← FER/DeepFace/Custom CNN
│   ├── hud_renderer.py         ← OpenCV overlay rendering
│   ├── session_logger.py       ← SQLite session + CSV export
│   ├── video_recorder.py       ← Output video saving
│   ├── emotion_graph.py        ← Matplotlib history graphs
│   └── api_server.py           ← FastAPI web backend
│
├── ai_models/
│   ├── train_model.py          ← Custom CNN training script
│   └── README.md               ← Model setup instructions
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── pages/
│   │       ├── HomePage.jsx
│   │       ├── LivePage.jsx
│   │       ├── SessionsPage.jsx
│   │       └── SettingsPage.jsx
│   ├── package.json
│   └── vite.config.js
│
├── assets/
│   ├── overlays/               ← Persona AR filter PNGs
│   └── generate_placeholders.py
│
├── configs/
│   ├── config.yaml             ← Main configuration
│   └── .env.example
│
├── datasets/                   ← FER-2013 dataset (download separately)
├── outputs/
│   ├── videos/                 ← Saved recordings
│   ├── csv/                    ← Exported session data
│   └── sessions.db             ← SQLite database
│
├── tests/
│   └── test_all.py             ← 30+ unit + integration tests
│
└── docs/
    └── ...
```

---

## 🤖 Emotion Model Backends

### FER (Default — Recommended for quick start)

```bash
pip install fer
```

Config: `emotion_model: fer`

### DeepFace (Higher accuracy)

```bash
pip install deepface
```

Config: `emotion_model: deepface`

### Custom CNN (Train your own)

See `ai_models/README.md` for full training instructions using FER-2013 dataset.

Config: `emotion_model: custom`

---

## 🎭 Persona Overlays

Add custom PNG files (with alpha channel) to `assets/overlays/`:

| File | Trigger Emotion |
|------|----------------|
| `crown.png` | Happy |
| `rain.png` | Sad |
| `fire.png` | Angry |
| `stars.png` | Surprise |
| `glasses.png` | Neutral |
| `ghost.png` | Fear |
| `mask.png` | Disgust |

Generate placeholders:
```bash
python assets/generate_placeholders.py
```

Enable in config: `show_persona: true` or use `--persona` flag.

---

## 📊 Session Data & Export

All sessions are automatically logged to `outputs/sessions.db`.

```bash
# Launch admin dashboard
python admin_dashboard.py

# View sessions, export CSV, generate graphs
```

Or export via API:
```
GET /api/export-csv?session_id=1
GET /api/session/1/timeline
GET /api/session/1/summary
```

---

## 🧪 Running Tests

```bash
pip install pytest
pytest tests/ -v
```

---

## 📦 Build Standalone EXE

```bash
pip install pyinstaller
pyinstaller build.spec
# EXE will be in dist/AI_Emotion_Overlay.exe
```

---

## ⚙️ Configuration

Edit `configs/config.yaml` to customize:

- Camera resolution and FPS
- Emotion model and confidence threshold
- HUD position and transparency
- Persona overlay scale
- Recording settings
- Session logging behavior

---

## 🛠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| Camera not found | Check `device_id` in config.yaml (try 0, 1, 2) |
| Low FPS | Switch to `fer` model, reduce resolution |
| Emotion flickering | Increase `smoothing_window` in config |
| Face not detected | Improve lighting, face camera directly |
| Model load error | Run `pip install fer mediapipe` again |
| Low accuracy | Try `deepface` backend or train custom CNN |

---

## 📄 License

MIT License — Free for personal and commercial use.

---

## 🙏 Credits

- [MediaPipe](https://mediapipe.dev) — Face detection
- [FER](https://github.com/justinshenk/fer) — Facial emotion recognition
- [DeepFace](https://github.com/serengil/deepface) — Deep face analysis
- [OpenCV](https://opencv.org) — Computer vision
- [FastAPI](https://fastapi.tiangolo.com) — Web API
- FER-2013 Dataset — Kaggle
