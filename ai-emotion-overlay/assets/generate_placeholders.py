"""
============================================================
Generate Placeholder Persona Overlay Assets
Creates simple placeholder PNG files for each emotion.
Replace these with real AR filter PNG files (BGRA with alpha).
============================================================
"""

import os
import numpy as np

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Emotion -> (symbol, color RGBA)
EMOTION_ASSETS = {
    "crown.png":  ("👑", (255, 215, 0, 200)),    # happy - gold crown
    "rain.png":   ("💧", (100, 150, 255, 200)),   # sad - rain drop
    "fire.png":   ("🔥", (255, 80, 0, 200)),      # angry - fire
    "stars.png":  ("⭐", (255, 240, 50, 200)),    # surprise - stars
    "glasses.png":("🕶️", (50, 50, 50, 200)),     # neutral - glasses
    "ghost.png":  ("👻", (220, 220, 255, 200)),   # fear - ghost
    "mask.png":   ("😷", (200, 200, 200, 200)),   # disgust - mask
}


def generate_placeholder_overlay(filename, size=(200, 150)):
    """Create a simple colored placeholder PNG with alpha channel."""
    output_dir = os.path.join("assets", "overlays")
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)

    if PIL_AVAILABLE:
        _, color = EMOTION_ASSETS.get(filename, ("?", (200, 200, 200, 180)))
        img = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Draw colored circle as placeholder
        r, g, b, a = color
        draw.ellipse(
            [size[0] // 4, size[1] // 4, 3 * size[0] // 4, 3 * size[1] // 4],
            fill=(r, g, b, a),
            outline=(255, 255, 255, 100),
            width=3
        )
        img.save(filepath, "PNG")
    else:
        # Fallback: raw numpy BGRA array
        h, w = size[1], size[0]
        arr = np.zeros((h, w, 4), dtype=np.uint8)
        cy, cx = h // 2, w // 2
        radius = min(h, w) // 3
        Y, X = np.ogrid[:h, :w]
        mask = (X - cx) ** 2 + (Y - cy) ** 2 <= radius ** 2
        arr[mask] = [200, 200, 200, 180]

        try:
            import cv2
            cv2.imwrite(filepath, arr)
        except ImportError:
            print(f"Cannot save {filename} without PIL or OpenCV")
            return

    print(f"Created placeholder: {filepath}")


if __name__ == "__main__":
    print("Generating placeholder persona overlay assets...")
    for fname in EMOTION_ASSETS:
        generate_placeholder_overlay(fname)
    print("\nDone! Replace these placeholders with real PNG overlay images.")
    print("Each PNG should have an alpha (transparency) channel.")
    print("Tip: Use BGRA format, 200x150px or larger, transparent background.")
