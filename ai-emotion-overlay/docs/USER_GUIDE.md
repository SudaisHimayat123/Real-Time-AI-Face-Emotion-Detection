# User Guide

## Starting the Application

```bash
python main.py
```

A window will open showing your webcam feed with all overlays.

---

## Understanding the Interface

```
┌─────────────────────────────────────────────────────────┐
│ FACE EMOTION HUD          ┌──────────────────────────┐  │
│ Angry    ░░░░░░░░░░  5%   │                          │  │
│ Disgust  ░░░░░░░░░░  2%   │  happy (99%)  ← label   │  │
│ Fear     ░░░░░░░░░░  3%   │  ┌──────────────────┐   │  │
│ Happy    █████████░ 92%   │  │   YOUR FACE      │   │  │
│ Neutral  ░█░░░░░░░░  8%   │  │                  │   │  │
│ Sad      ░░░░░░░░░░  3%   │  └──────────────────┘   │  │
│ Surprise ░░░░░░░░░░  2%   │                          │  │
│                           └──────────────────────────┘  │
├─────────────────────────────────────────────────────────┤
│ FPS: 30.0   Faces: 1     Frame: 450    Press 'q' to quit│
└─────────────────────────────────────────────────────────┘
```

### HUD Panel (Left Side)
- Shows all 7 emotion classes with a color-coded progress bar
- Bars update in real-time with smoothed confidence scores
- Title "FACE EMOTION HUD" in magenta/purple

### Face Overlay
- White bounding box with corner accents around your face
- Label above box shows: **Emotion Name (Confidence%)**
- Colored dot in top-right corner of box indicates dominant emotion
- Works with multiple faces simultaneously

### Status Bar (Bottom)
- **FPS** — Frames per second (green if ≥20, red if lower)
- **Faces** — Number of faces currently detected
- **Frame** — Total frame count since session start
- **Press 'q' to quit** — reminder hint

---

## Keyboard Controls

| Key | Action |
|-----|--------|
| `q` or `ESC` | Quit the application |
| `h` | Toggle HUD panel on/off |
| `b` | Toggle bounding boxes on/off |
| `p` | Toggle persona/AR overlays on/off |
| `r` | Start/stop video recording |
| `s` | Save session emotion data as CSV |
| `SPACE` | Pause/Resume video feed |

---

## Processing a Video File

```bash
python main.py --source /path/to/your/video.mp4
```

- All overlays will be rendered on the video
- Press `r` to record the output
- When the video ends, the app closes automatically

---

## Recording Output

Press `r` to start/stop recording. A red **REC** indicator appears in the bottom-right corner.

Recordings are saved to: `outputs/videos/emotion_recording_YYYYMMDD_HHMMSS.mp4`

---

## Session Data & CSV Export

Every session automatically logs emotion data to `outputs/sessions.db`.

**Export during session:** Press `s`

**Export after session:**
```bash
python admin_dashboard.py
```

CSV columns:
```
id, session_id, timestamp, elapsed_seconds, face_index,
dominant_emotion, confidence, angry, disgust, fear,
happy, neutral, sad, surprise
```

---

## Admin Dashboard

```bash
python admin_dashboard.py
```

Options:
1. List all past sessions
2. View session detail with emotion averages
3. Export session as CSV
4. Generate emotion timeline PNG chart
5. Generate emotion pie chart

---

## Persona / AR Overlays

Enable with:
```bash
python main.py --persona
```
Or press `p` while running.

Add your own PNG overlays to `assets/overlays/`:
- Files must have **alpha (transparency) channel** (BGRA)
- See `assets/generate_placeholders.py` to create test assets

---

## Configuration

Edit `configs/config.yaml` to change:
- Camera device ID and resolution
- Emotion model (fer / deepface / custom)
- HUD transparency and position
- Bounding box color and thickness
- Smoothing window size
- Auto-recording on startup

---

## Tips for Best Results

1. **Good lighting** — Face the light source; avoid backlighting
2. **Face the camera** — Profile views reduce detection accuracy
3. **Keep face in frame** — Partial faces may not be detected
4. **Clean lens** — Smudged webcam reduces quality
5. **Multiple faces** — Move both people in view; works up to 5 faces
6. **Smoothing** — Increase `smoothing_window` in config if emotions flicker too much
7. **Low FPS** — Try `--model fer` (fastest) or reduce camera resolution
