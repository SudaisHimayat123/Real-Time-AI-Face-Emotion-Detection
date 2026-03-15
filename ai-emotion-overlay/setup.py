#!/usr/bin/env python3
"""
============================================================
AI Face Emotion Overlay — Quick Setup Script
Run this once to set up the project environment.
Usage: python setup.py
============================================================
"""

import subprocess
import sys
import os
import shutil


def run(cmd, check=True):
    print(f"  $ {cmd}")
    result = subprocess.run(cmd, shell=True, check=check)
    return result.returncode == 0


def main():
    print("=" * 60)
    print("  AI Face Emotion Overlay — Setup")
    print("=" * 60)

    # Check Python version
    if sys.version_info < (3, 9):
        print(f"\n❌ Python 3.9+ required. You have {sys.version}")
        sys.exit(1)
    print(f"\n✅ Python {sys.version.split()[0]}")

    # Create required directories
    dirs = [
        "outputs/videos",
        "outputs/csv",
        "outputs/uploads",
        "ai_models",
        "assets/overlays",
        "datasets",
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    print("✅ Directories created")

    # Copy .env example
    if not os.path.exists("configs/.env"):
        if os.path.exists("configs/.env.example"):
            shutil.copy("configs/.env.example", "configs/.env")
            print("✅ configs/.env created from template")

    # Install Python dependencies
    print("\n📦 Installing Python dependencies...")
    success = run(f"{sys.executable} -m pip install --upgrade pip -q")
    success = run(f"{sys.executable} -m pip install -r requirements.txt")

    if not success:
        print("⚠️  Some packages may have failed to install.")
        print("    Try installing manually: pip install opencv-python mediapipe fer")
    else:
        print("✅ Python dependencies installed")

    # Generate placeholder persona assets
    print("\n🎭 Generating placeholder persona assets...")
    run(f"{sys.executable} assets/generate_placeholders.py", check=False)

    # Test imports
    print("\n🔍 Testing key imports...")
    test_imports = ["cv2", "mediapipe", "numpy", "yaml", "loguru"]
    all_ok = True
    for pkg in test_imports:
        try:
            __import__(pkg)
            print(f"  ✅ {pkg}")
        except ImportError:
            print(f"  ❌ {pkg} — run: pip install {pkg}")
            all_ok = False

    # Check FER
    try:
        from fer import FER
        print("  ✅ fer (emotion model)")
    except ImportError:
        print("  ⚠️  fer not installed — run: pip install fer")

    print("\n" + "=" * 60)
    if all_ok:
        print("  ✅ Setup complete! Run the app with:")
        print()
        print("     python main.py")
        print()
        print("  Options:")
        print("     python main.py --source 0      # webcam")
        print("     python main.py --source video.mp4  # video file")
        print("     python main.py --model deepface    # DeepFace model")
        print()
        print("  Web version:")
        print("     python -m backend.api_server   # start API")
        print("     cd frontend && npm install && npm run dev")
    else:
        print("  ⚠️  Some dependencies missing. Check above and install manually.")
    print("=" * 60)


if __name__ == "__main__":
    main()
