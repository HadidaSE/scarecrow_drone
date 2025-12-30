#!/usr/bin/env python3
"""
Train YOLOv8 model on Pigeon Dataset - GPU Version
For BGU HPC Cluster with CUDA support
"""

from ultralytics import YOLO
import os
import torch

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_YAML = os.path.join(BASE_DIR, "data", "combined", "data_augmented.yaml")
OUTPUT_DIR = os.path.join(BASE_DIR, "runs")


def check_gpu():
    """Check GPU availability and print info"""
    print("=" * 50)
    print("GPU Check")
    print("=" * 50)

    if torch.cuda.is_available():
        print(f"CUDA available: Yes")
        print(f"CUDA version: {torch.version.cuda}")
        print(f"GPU count: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            props = torch.cuda.get_device_properties(i)
            print(f"  GPU {i}: {props.name}")
            print(f"    Memory: {props.total_memory / 1024**3:.1f} GB")
        device = "0"  # Use first GPU
    else:
        print("CUDA available: No - using CPU")
        device = "cpu"

    print("=" * 50)
    return device


def train():
    """Train YOLOv8 nano model on pigeon dataset with GPU"""

    device = check_gpu()

    print("\n" + "=" * 50)
    print("Pigeon Detection Model Training (GPU)")
    print("=" * 50)
    print(f"Data: {DATA_YAML}")
    print(f"Output: {OUTPUT_DIR}")
    print(f"Device: {device}")
    print("=" * 50 + "\n")

    # Check data exists
    if not os.path.exists(DATA_YAML):
        print(f"ERROR: Dataset not found at {DATA_YAML}")
        print("Please download the pigeon dataset from Roboflow:")
        print("  https://universe.roboflow.com/spirosmakris/pigeons-qbzpj")
        return None

    # Load YOLOv8 nano (smallest, fastest)
    model = YOLO("yolov8n.pt")

    # Train with GPU-optimized settings
    results = model.train(
        data=DATA_YAML,
        epochs=100,             # Full training - 100 epochs
        imgsz=640,              # Standard size for better accuracy
        batch=32,               # Larger batch with GPU (adjust if OOM)
        name="pigeon_detector_gpu",
        project=OUTPUT_DIR,
        patience=15,            # Early stopping after 15 epochs no improvement
        save=True,
        plots=True,
        device=device,          # Use GPU
        workers=4,              # Data loading workers
        cache="disk",           # Cache to disk (RAM caused OOM with 10k images)
        amp=True,               # Automatic mixed precision (faster on GPU)
        verbose=True,
    )

    print("\n" + "=" * 50)
    print("Training Complete!")
    print("=" * 50)

    best_model = os.path.join(OUTPUT_DIR, "pigeon_detector_gpu", "weights", "best.pt")
    print(f"\nBest model saved to: {best_model}")

    # Print final metrics
    if results:
        print("\nFinal Metrics:")
        print(f"  mAP50: {results.results_dict.get('metrics/mAP50(B)', 'N/A'):.4f}")
        print(f"  mAP50-95: {results.results_dict.get('metrics/mAP50-95(B)', 'N/A'):.4f}")
        print(f"  Precision: {results.results_dict.get('metrics/precision(B)', 'N/A'):.4f}")
        print(f"  Recall: {results.results_dict.get('metrics/recall(B)', 'N/A'):.4f}")

    return results


if __name__ == "__main__":
    train()
