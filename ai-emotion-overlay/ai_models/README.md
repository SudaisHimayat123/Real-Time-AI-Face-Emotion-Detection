# AI Models Directory

## Contents

This directory stores trained model files for emotion classification.

### Expected Files

| File | Description | Size |
|------|-------------|------|
| `emotion_cnn.h5` | Custom trained CNN (Keras) | ~15MB |
| `emotion_cnn_quantized.tflite` | INT8 quantized TFLite model | ~4MB |
| `training_curves.png` | Generated during training |  |
| `confusion_matrix.png` | Generated during training |  |

---

## Option 1: Use Pre-trained FER Library (Recommended — No training needed)

The app uses the `fer` library by default which includes a pre-trained model:

```bash
pip install fer
```

No model files needed in this directory for the default setup.

---

## Option 2: Use DeepFace (High accuracy)

```bash
pip install deepface
```

Set `emotion_model: deepface` in `configs/config.yaml`.
DeepFace will auto-download its models on first run.

---

## Option 3: Train Custom CNN on FER-2013

### 1. Download Dataset

Download FER-2013 from Kaggle:
https://www.kaggle.com/datasets/msambare/fer2013

Save as: `datasets/fer2013.csv`

### 2. Train

```bash
# Fast: custom lightweight CNN
python ai_models/train_model.py --data datasets/fer2013.csv --model cnn --epochs 50

# Accurate: MobileNetV2 transfer learning
python ai_models/train_model.py --data datasets/fer2013.csv --model mobilenet --epochs 30
```

### 3. Use the model

Set `emotion_model: custom` in `configs/config.yaml`.

---

## Model Performance (FER-2013 Benchmarks)

| Model | Accuracy | Speed | Notes |
|-------|----------|-------|-------|
| FER library | ~65% | Fast | Good for MVP |
| DeepFace | ~72% | Moderate | Best accuracy |
| Custom CNN | ~60-68% | Fast | Trainable |
| MobileNetV2 fine-tuned | ~68-72% | Fast | Best custom option |

---

## INT8 Quantization (for speed)

After training, quantize your model:

```python
import tensorflow as tf

converter = tf.lite.TFLiteConverter.from_keras_model_file("emotion_cnn.h5")
converter.optimizations = [tf.lite.Optimize.DEFAULT]
tflite_model = converter.convert()

with open("emotion_cnn_quantized.tflite", "wb") as f:
    f.write(tflite_model)
```

This reduces model size ~4x and improves inference speed significantly.
