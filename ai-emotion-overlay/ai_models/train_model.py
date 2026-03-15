"""
============================================================
Custom CNN Emotion Model Training Script
Trains a MobileNetV2-based emotion classifier on FER-2013 dataset.
Output model saved to: ai_models/emotion_cnn.h5

Usage:
  python ai_models/train_model.py --data datasets/fer2013.csv
  python ai_models/train_model.py --data datasets/fer2013/ --epochs 50
============================================================
"""

import os
import sys
import argparse
import numpy as np
import pandas as pd
from loguru import logger

# ── Lazy imports (TF only loaded when this script runs) ───────────────────────
try:
    import tensorflow as tf
    from tensorflow.keras import layers, models, callbacks, optimizers
    from tensorflow.keras.applications import MobileNetV2
    from tensorflow.keras.preprocessing.image import ImageDataGenerator
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import classification_report, confusion_matrix
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    logger.warning("TensorFlow not installed. Install with: pip install tensorflow")

# ── Constants ─────────────────────────────────────────────────────────────────
EMOTION_LABELS = ["angry", "disgust", "fear", "happy", "neutral", "sad", "surprise"]
NUM_CLASSES = len(EMOTION_LABELS)
IMG_SIZE = 48
BATCH_SIZE = 64
MODEL_OUTPUT_PATH = os.path.join("ai_models", "emotion_cnn.h5")


# ═════════════════════════════════════════════════════════════════════════════
# Data loading
# ═════════════════════════════════════════════════════════════════════════════

def load_fer2013_csv(csv_path: str):
    """
    Load FER-2013 dataset from CSV format.
    Expected columns: emotion (int 0-6), pixels (space-separated), Usage

    Download from: https://www.kaggle.com/datasets/msambare/fer2013
    """
    logger.info(f"Loading FER-2013 from: {csv_path}")
    df = pd.read_csv(csv_path)

    X, y = [], []
    for _, row in df.iterrows():
        pixels = np.array(row["pixels"].split(), dtype=np.uint8).reshape(IMG_SIZE, IMG_SIZE)
        X.append(pixels)
        y.append(int(row["emotion"]))

    X = np.array(X, dtype=np.float32) / 255.0
    X = X.reshape(-1, IMG_SIZE, IMG_SIZE, 1)  # Grayscale
    y = np.array(y)

    logger.info(f"Loaded {len(X)} samples across {NUM_CLASSES} classes")
    return X, y


def apply_class_weights(y: np.ndarray) -> dict:
    """Compute class weights to handle FER-2013 class imbalance."""
    from sklearn.utils.class_weight import compute_class_weight
    weights = compute_class_weight("balanced", classes=np.unique(y), y=y)
    return dict(enumerate(weights))


# ═════════════════════════════════════════════════════════════════════════════
# Model architecture
# ═════════════════════════════════════════════════════════════════════════════

def build_custom_cnn() -> tf.keras.Model:
    """Build lightweight custom CNN for 48x48 grayscale input."""
    inputs = layers.Input(shape=(IMG_SIZE, IMG_SIZE, 1))

    x = layers.Conv2D(32, 3, padding="same", activation="relu")(inputs)
    x = layers.BatchNormalization()(x)
    x = layers.Conv2D(32, 3, padding="same", activation="relu")(x)
    x = layers.MaxPooling2D(2)(x)
    x = layers.Dropout(0.25)(x)

    x = layers.Conv2D(64, 3, padding="same", activation="relu")(x)
    x = layers.BatchNormalization()(x)
    x = layers.Conv2D(64, 3, padding="same", activation="relu")(x)
    x = layers.MaxPooling2D(2)(x)
    x = layers.Dropout(0.25)(x)

    x = layers.Conv2D(128, 3, padding="same", activation="relu")(x)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling2D(2)(x)
    x = layers.Dropout(0.25)(x)

    x = layers.Flatten()(x)
    x = layers.Dense(512, activation="relu")(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.5)(x)
    x = layers.Dense(256, activation="relu")(x)
    x = layers.Dropout(0.3)(x)
    outputs = layers.Dense(NUM_CLASSES, activation="softmax")(x)

    model = models.Model(inputs, outputs, name="EmotionCNN")
    logger.info(f"Custom CNN parameters: {model.count_params():,}")
    return model


def build_mobilenetv2_model() -> tf.keras.Model:
    """
    Build MobileNetV2-based transfer learning model.
    Faster convergence, better accuracy than custom CNN.
    Input: 48x48 grayscale → upscaled to 96x96 RGB for MobileNet.
    """
    inputs = layers.Input(shape=(IMG_SIZE, IMG_SIZE, 1))

    # Upscale and convert to 3-channel for MobileNetV2
    x = layers.UpSampling2D(size=(2, 2))(inputs)  # 96x96
    x = layers.Concatenate()([x, x, x])            # 96x96x3

    base = MobileNetV2(
        input_shape=(96, 96, 3),
        include_top=False,
        weights="imagenet",
        alpha=0.35  # Lightweight version
    )
    base.trainable = False  # Freeze for initial training

    x = base(x, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dense(256, activation="relu")(x)
    x = layers.Dropout(0.4)(x)
    outputs = layers.Dense(NUM_CLASSES, activation="softmax")(x)

    model = models.Model(inputs, outputs, name="EmotionMobileNetV2")
    logger.info(f"MobileNetV2 parameters: {model.count_params():,}")
    return model


# ═════════════════════════════════════════════════════════════════════════════
# Training pipeline
# ═════════════════════════════════════════════════════════════════════════════

def train(
    X: np.ndarray,
    y: np.ndarray,
    model_type: str = "cnn",
    epochs: int = 50,
    use_augmentation: bool = True
):
    """
    Full training pipeline with callbacks, augmentation, and evaluation.

    Args:
        X: Input images (N, 48, 48, 1)
        y: Labels (N,)
        model_type: 'cnn' or 'mobilenet'
        epochs: Training epochs
        use_augmentation: Whether to use data augmentation
    """
    # ── Split dataset ─────────────────────────────────────────────────────
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.15, random_state=42, stratify=y
    )
    logger.info(f"Train: {len(X_train)} | Val: {len(X_val)}")

    # ── One-hot encode labels ─────────────────────────────────────────────
    y_train_cat = tf.keras.utils.to_categorical(y_train, NUM_CLASSES)
    y_val_cat = tf.keras.utils.to_categorical(y_val, NUM_CLASSES)

    # ── Class weights ─────────────────────────────────────────────────────
    class_weights = apply_class_weights(y_train)
    logger.info(f"Class weights: {class_weights}")

    # ── Build model ───────────────────────────────────────────────────────
    if model_type == "mobilenet":
        model = build_mobilenetv2_model()
    else:
        model = build_custom_cnn()

    model.compile(
        optimizer=optimizers.Adam(learning_rate=1e-3),
        loss="categorical_crossentropy",
        metrics=["accuracy"]
    )
    model.summary()

    # ── Data augmentation ─────────────────────────────────────────────────
    if use_augmentation:
        datagen = ImageDataGenerator(
            rotation_range=15,
            width_shift_range=0.1,
            height_shift_range=0.1,
            horizontal_flip=True,
            zoom_range=0.1,
            brightness_range=[0.8, 1.2]
        )
        train_gen = datagen.flow(X_train, y_train_cat, batch_size=BATCH_SIZE)
    else:
        train_gen = tf.data.Dataset.from_tensor_slices(
            (X_train, y_train_cat)
        ).batch(BATCH_SIZE)

    # ── Callbacks ─────────────────────────────────────────────────────────
    os.makedirs("ai_models", exist_ok=True)
    cbs = [
        callbacks.ModelCheckpoint(
            MODEL_OUTPUT_PATH,
            monitor="val_accuracy",
            save_best_only=True,
            verbose=1
        ),
        callbacks.EarlyStopping(
            monitor="val_accuracy",
            patience=10,
            restore_best_weights=True,
            verbose=1
        ),
        callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=5,
            min_lr=1e-6,
            verbose=1
        ),
        callbacks.TensorBoard(log_dir="outputs/tensorboard_logs")
    ]

    # ── Train ─────────────────────────────────────────────────────────────
    history = model.fit(
        train_gen,
        epochs=epochs,
        validation_data=(X_val, y_val_cat),
        class_weight=class_weights,
        callbacks=cbs,
        verbose=1
    )

    # ── Evaluate ─────────────────────────────────────────────────────────
    logger.info("Evaluating on validation set...")
    y_pred = np.argmax(model.predict(X_val, verbose=0), axis=1)

    print("\nClassification Report:")
    print(classification_report(y_val, y_pred, target_names=EMOTION_LABELS))

    # Save training plot
    _save_training_plot(history)

    # Save confusion matrix
    _save_confusion_matrix(y_val, y_pred)

    logger.success(f"Model saved: {MODEL_OUTPUT_PATH}")
    return model


def _save_training_plot(history):
    """Save accuracy/loss training curves."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
    fig.patch.set_facecolor("#0d0d0d")

    for ax, metric, title in [
        (ax1, "accuracy", "Accuracy"),
        (ax2, "loss", "Loss")
    ]:
        ax.set_facecolor("#141414")
        ax.plot(history.history[metric], label="Train", color="#00ff88")
        ax.plot(history.history[f"val_{metric}"], label="Val", color="#ff6b6b")
        ax.set_title(title, color="white")
        ax.legend(facecolor="#222", labelcolor="white")
        ax.tick_params(colors="gray")
        for spine in ax.spines.values():
            spine.set_color("#333")

    plt.tight_layout()
    plt.savefig("ai_models/training_curves.png", dpi=100, facecolor=fig.get_facecolor())
    plt.close()
    logger.info("Training curves saved: ai_models/training_curves.png")


def _save_confusion_matrix(y_true, y_pred):
    """Save confusion matrix visualization."""
    cm = confusion_matrix(y_true, y_pred)
    fig, ax = plt.subplots(figsize=(9, 7))
    fig.patch.set_facecolor("#0d0d0d")
    ax.set_facecolor("#141414")

    im = ax.imshow(cm, cmap="Blues")
    plt.colorbar(im, ax=ax)

    ax.set_xticks(range(NUM_CLASSES))
    ax.set_yticks(range(NUM_CLASSES))
    ax.set_xticklabels(EMOTION_LABELS, rotation=45, ha="right", color="white")
    ax.set_yticklabels(EMOTION_LABELS, color="white")
    ax.set_title("Confusion Matrix", color="white", pad=12)
    ax.set_xlabel("Predicted", color="gray")
    ax.set_ylabel("True", color="gray")

    for i in range(NUM_CLASSES):
        for j in range(NUM_CLASSES):
            ax.text(j, i, str(cm[i, j]),
                    ha="center", va="center",
                    color="white" if cm[i, j] < cm.max() / 2 else "black",
                    fontsize=9)

    plt.tight_layout()
    plt.savefig("ai_models/confusion_matrix.png", dpi=100, facecolor=fig.get_facecolor())
    plt.close()
    logger.info("Confusion matrix saved: ai_models/confusion_matrix.png")


# ═════════════════════════════════════════════════════════════════════════════
# Entry point
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if not TF_AVAILABLE:
        print("TensorFlow not installed. Run: pip install tensorflow")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Train emotion CNN model")
    parser.add_argument("--data", required=True, help="Path to fer2013.csv")
    parser.add_argument("--model", default="cnn", choices=["cnn", "mobilenet"])
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--no-augment", action="store_true")
    args = parser.parse_args()

    X, y = load_fer2013_csv(args.data)
    train(X, y, model_type=args.model, epochs=args.epochs, use_augmentation=not args.no_augment)
