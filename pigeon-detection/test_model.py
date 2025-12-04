#!/usr/bin/env python3
"""
Test the trained pigeon detection model
"""

from ultralytics import YOLO
import os

# Find the best model
MODEL_PATH = "runs/pigeon_detector_v2/weights/best.pt"
TEST_IMAGES = "data/images/pigeons.v1i.yolov8/test/images"

print("Loading model...")
model = YOLO(MODEL_PATH)

print(f"Testing on images in: {TEST_IMAGES}")
print("=" * 50)

# Run prediction with lower confidence
results = model.predict(
    source=TEST_IMAGES,
    save=True,
    conf=0.5,  # Balanced confidence threshold
    save_txt=True,  # Save detection results
    project="runs/test_results",
    name="pigeons"
)

# Print detection summary
total_detections = 0
for r in results:
    num_detections = len(r.boxes)
    total_detections += num_detections
    if num_detections > 0:
        print(f"{os.path.basename(r.path)}: {num_detections} pigeon(s) detected")

print("=" * 50)
print(f"Total: {total_detections} pigeons detected across {len(results)} images")
print(f"\nResults saved to: runs/test_results/pigeons/")
