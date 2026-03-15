# ============================================================
# AI Face Emotion Overlay — Docker Image
# ============================================================

FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create output directories
RUN mkdir -p outputs/videos outputs/csv outputs/uploads ai_models assets/overlays

# Expose API port
EXPOSE 8000

# Default command: run web API server
CMD ["python", "-m", "backend.api_server"]
