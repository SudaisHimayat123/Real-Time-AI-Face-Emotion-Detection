# Assets Directory

## overlays/

Place your persona / AR filter PNG files here.

Each file should be named to match the emotion it represents:

| Filename | Emotion | Description |
|----------|---------|-------------|
| `crown.png` | Happy | Crown / celebration overlay |
| `rain.png` | Sad | Rain drop / cloud effect |
| `fire.png` | Angry | Fire / flame overlay |
| `stars.png` | Surprise | Stars / sparkle effect |
| `glasses.png` | Neutral | Cool glasses overlay |
| `ghost.png` | Fear | Ghost / spooky overlay |
| `mask.png` | Disgust | Mask overlay |

### Requirements for PNG files:
- Must have **4 channels (RGBA / BGRA)** — alpha channel required for transparency
- Transparent background (alpha = 0 where no overlay should appear)
- Recommended size: 300×200px or larger
- The overlay is auto-scaled and centered above the detected face

### Generate Placeholders:
```bash
python assets/generate_placeholders.py
```

### Tips for custom assets:
- Download free PNG overlays from sites like PNGTree, FreePNG, Freepik
- Use GIMP or Photoshop to add/edit alpha channel
- Test with: `python main.py --persona`
