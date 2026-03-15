# Installation Guide

## System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| OS | Windows 10 / Ubuntu 20.04 / macOS 12 | Windows 11 / Ubuntu 22.04 |
| Python | 3.9 | 3.10 or 3.11 |
| RAM | 4 GB | 8 GB |
| CPU | Dual-core 2GHz | Quad-core 3GHz+ |
| GPU | Not required | NVIDIA GPU (CUDA) for faster inference |
| Webcam | Any USB/built-in | 720p or higher |
| Storage | 2 GB free | 5 GB free |

---

## Step 1 — Install Python

Download Python 3.10 from https://python.org/downloads/

> ⚠️ On Windows, check "Add Python to PATH" during installation.

Verify:
```bash
python --version
# Python 3.10.x
```

---

## Step 2 — Create Virtual Environment

```bash
# Navigate to project folder
cd ai-emotion-overlay

# Create venv
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate
```

---

## Step 3 — Install Dependencies

**Option A: Automatic (recommended)**
```bash
python setup.py
```

**Option B: Manual**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Core packages installed:
- `opencv-python` — video capture and overlay rendering
- `mediapipe` — face detection
- `fer` — pre-trained emotion model (FER-2013)
- `numpy`, `pandas` — data handling
- `loguru` — logging
- `pyyaml` — config file loading
- `matplotlib` — session graphs
- `fastapi`, `uvicorn` — web API (optional)

---

## Step 4 — Run

```bash
python main.py
```

On first run, `fer` and `mediapipe` will download their model weights (one-time, ~100MB total).

---

## Step 5 — Verify

You should see:
1. A window titled "AI Face Emotion Overlay" opens
2. Your webcam feed appears
3. If a face is detected: white bounding box + emotion label appears
4. Left-side HUD shows emotion progress bars
5. Bottom bar shows FPS counter

---

## Troubleshooting Installation

### `pip install` fails on mediapipe
```bash
pip install mediapipe --no-cache-dir
```

### Camera not opening
- Try different device IDs: edit `configs/config.yaml` → `camera.device_id: 1`
- Or pass via CLI: `python main.py --source 1`

### "No module named cv2"
```bash
pip install opencv-python
```

### Slow performance / low FPS
- Lower camera resolution in `configs/config.yaml`
- Use `model: fer` (fastest)
- Close other applications using the webcam

### macOS camera permission
- Go to System Preferences → Security & Privacy → Camera
- Allow Terminal / your Python app access

### Linux camera permission
```bash
sudo usermod -a -G video $USER
# Then log out and back in
```

---

## Web Version Additional Setup

### Backend
```bash
pip install fastapi uvicorn python-multipart websockets
python -m backend.api_server
```

### Frontend
```bash
# Install Node.js 18+ from nodejs.org
cd frontend
npm install
npm run dev
```

### Docker
```bash
# Install Docker Desktop from docker.com
docker-compose up --build
```
