#!/usr/bin/env python3
"""
Train YOLOv8 model on Pigeon Dataset
For Intel Aero Drone Detection System
"""

from ultralytics import YOLO
import os

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_YAML = os.path.join(BASE_DIR, "data", "images", "pigeons.v1i.yolov8", "data.yaml")
OUTPUT_DIR = os.path.join(BASE_DIR, "runs")

def train():
    """Train YOLOv8 nano model on pigeon dataset"""

    print("=" * 50)
    print("Pigeon Detection Model Training (Fast + Fixed)")
    print("=" * 50)

    # Load YOLOv8 nano
    model = YOLO("yolov8n.pt")

    # Train - FAST but no early stopping
    results = model.train(
        data=DATA_YAML,
        epochs=20,              # Enough epochs
        imgsz=416,              # Smaller = faster
        batch=16,
        name="pigeon_detector_v3",
        project=OUTPUT_DIR,
        patience=0,             # NO early stopping
        save=True,
        plots=True,
        device="cpu",
        workers=8,
        cache="ram",
    )

    print("\n" + "=" * 50)
    print("Training Complete!")
    print("=" * 50)
    print(f"\nModel saved to: {OUTPUT_DIR}/pigeon_detector_v3/weights/best.pt")

    return results


if __name__ == "__main__":
    train()
