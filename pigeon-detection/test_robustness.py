#!/usr/bin/env python3
"""
Robustness Testing for Pigeon Detection Model
Tests model performance under various challenging conditions
"""

import os
import cv2
import numpy as np
from pathlib import Path
from ultralytics import YOLO
import shutil

# Paths
BASE_DIR = Path(__file__).parent
MODEL_PATH = BASE_DIR / "runs" / "pigeon_detector_gpu7" / "weights" / "best.pt"
DATA_DIR = BASE_DIR / "data" / "combined"
VALID_IMAGES = DATA_DIR / "valid" / "images"
VALID_LABELS = DATA_DIR / "valid" / "labels"
OUTPUT_DIR = BASE_DIR / "robustness_test"


def apply_blur(img, severity="mild"):
    """Apply Gaussian blur"""
    kernel_size = 5 if severity == "mild" else 15 if severity == "medium" else 25
    return cv2.GaussianBlur(img, (kernel_size, kernel_size), 0)


def apply_motion_blur(img, severity="mild"):
    """Apply motion blur (simulates camera movement)"""
    size = 7 if severity == "mild" else 15 if severity == "medium" else 25
    kernel = np.zeros((size, size))
    kernel[int((size-1)/2), :] = np.ones(size)
    kernel = kernel / size
    return cv2.filter2D(img, -1, kernel)


def apply_noise(img, severity="mild"):
    """Apply Gaussian noise"""
    std = 10 if severity == "mild" else 25 if severity == "medium" else 50
    noise = np.random.normal(0, std, img.shape).astype(np.float32)
    noisy = img.astype(np.float32) + noise
    return np.clip(noisy, 0, 255).astype(np.uint8)


def apply_scale_down(img, scale=0.5):
    """Scale down image (simulates far away objects)"""
    h, w = img.shape[:2]
    new_h, new_w = int(h * scale), int(w * scale)
    scaled = cv2.resize(img, (new_w, new_h))
    # Pad back to original size (center)
    result = np.zeros_like(img)
    y_off = (h - new_h) // 2
    x_off = (w - new_w) // 2
    result[y_off:y_off+new_h, x_off:x_off+new_w] = scaled
    return result


def apply_brightness(img, factor=0.5):
    """Adjust brightness (factor < 1 = darker, > 1 = brighter)"""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    hsv = hsv.astype(np.float32)
    hsv[:, :, 2] = np.clip(hsv[:, :, 2] * factor, 0, 255)
    hsv = hsv.astype(np.uint8)
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)


def apply_compression(img, quality=20):
    """Apply JPEG compression artifacts"""
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    _, encoded = cv2.imencode('.jpg', img, encode_param)
    return cv2.imdecode(encoded, cv2.IMREAD_COLOR)


def apply_rain(img, severity="mild"):
    """Simulate rain effect"""
    rain = img.copy()
    drops = 100 if severity == "mild" else 300 if severity == "medium" else 600
    for _ in range(drops):
        x = np.random.randint(0, img.shape[1])
        y = np.random.randint(0, img.shape[0])
        length = np.random.randint(10, 30)
        cv2.line(rain, (x, y), (x + 2, y + length), (200, 200, 200), 1)
    return cv2.addWeighted(img, 0.7, rain, 0.3, 0)


def scale_labels(label_path, scale, img_w, img_h):
    """Scale label bounding boxes for scale_down transform"""
    if not label_path.exists():
        return []

    with open(label_path, 'r') as f:
        lines = f.readlines()

    scaled_labels = []
    for line in lines:
        parts = line.strip().split()
        if len(parts) >= 5:
            cls, x, y, w, h = int(parts[0]), float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
            # Scale and offset
            new_x = 0.5 + (x - 0.5) * scale
            new_y = 0.5 + (y - 0.5) * scale
            new_w = w * scale
            new_h = h * scale
            scaled_labels.append(f"{cls} {new_x} {new_y} {new_w} {new_h}")

    return scaled_labels


# Define test conditions
TEST_CONDITIONS = [
    ("original", lambda img: img, None),
    ("blur_mild", lambda img: apply_blur(img, "mild"), None),
    ("blur_heavy", lambda img: apply_blur(img, "heavy"), None),
    ("motion_blur_mild", lambda img: apply_motion_blur(img, "mild"), None),
    ("motion_blur_heavy", lambda img: apply_motion_blur(img, "heavy"), None),
    ("noise_mild", lambda img: apply_noise(img, "mild"), None),
    ("noise_heavy", lambda img: apply_noise(img, "heavy"), None),
    ("scale_50pct", lambda img: apply_scale_down(img, 0.5), 0.5),  # 50% = far away
    ("scale_30pct", lambda img: apply_scale_down(img, 0.3), 0.3),  # 30% = very far
    ("dark", lambda img: apply_brightness(img, 0.4), None),
    ("very_dark", lambda img: apply_brightness(img, 0.2), None),
    ("bright", lambda img: apply_brightness(img, 1.5), None),
    ("overexposed", lambda img: apply_brightness(img, 2.0), None),
    ("compression_low", lambda img: apply_compression(img, 30), None),
    ("compression_very_low", lambda img: apply_compression(img, 10), None),
    ("rain_mild", lambda img: apply_rain(img, "mild"), None),
    ("rain_heavy", lambda img: apply_rain(img, "heavy"), None),
]


def create_test_set(condition_name, transform_fn, scale_factor=None):
    """Create transformed test set"""
    output_images = OUTPUT_DIR / condition_name / "images"
    output_labels = OUTPUT_DIR / condition_name / "labels"
    output_images.mkdir(parents=True, exist_ok=True)
    output_labels.mkdir(parents=True, exist_ok=True)

    for img_path in VALID_IMAGES.glob("*"):
        if img_path.suffix.lower() not in [".jpg", ".jpeg", ".png", ".bmp"]:
            continue

        # Read and transform image
        img = cv2.imread(str(img_path))
        if img is None:
            continue

        transformed = transform_fn(img)
        cv2.imwrite(str(output_images / img_path.name), transformed)

        # Copy or scale labels
        label_path = VALID_LABELS / (img_path.stem + ".txt")
        output_label = output_labels / (img_path.stem + ".txt")

        if scale_factor:
            scaled_labels = scale_labels(label_path, scale_factor, img.shape[1], img.shape[0])
            with open(output_label, 'w') as f:
                f.write('\n'.join(scaled_labels))
        elif label_path.exists():
            shutil.copy(label_path, output_label)


def evaluate_condition(model, condition_name):
    """Run validation on a condition"""
    data_yaml = OUTPUT_DIR / condition_name / "data.yaml"

    # Create data.yaml for this condition
    yaml_content = f"""train: {OUTPUT_DIR / condition_name / "images"}
val: {OUTPUT_DIR / condition_name / "images"}
test: {OUTPUT_DIR / condition_name / "images"}

nc: 1
names: ['Pigeon']
"""
    with open(data_yaml, 'w') as f:
        f.write(yaml_content)

    # Run validation
    results = model.val(data=str(data_yaml), verbose=False)

    return {
        "mAP50": results.results_dict.get("metrics/mAP50(B)", 0),
        "mAP50-95": results.results_dict.get("metrics/mAP50-95(B)", 0),
        "precision": results.results_dict.get("metrics/precision(B)", 0),
        "recall": results.results_dict.get("metrics/recall(B)", 0),
    }


def main():
    print("=" * 60)
    print("Pigeon Detection - Robustness Testing")
    print("=" * 60)

    # Check model exists
    if not MODEL_PATH.exists():
        print(f"ERROR: Model not found at {MODEL_PATH}")
        return

    # Load model
    print(f"\nLoading model: {MODEL_PATH}")
    model = YOLO(str(MODEL_PATH))

    # Clean output directory
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)

    results = {}
    baseline = None

    for condition_name, transform_fn, scale_factor in TEST_CONDITIONS:
        print(f"\nTesting: {condition_name}...")

        # Create transformed test set
        create_test_set(condition_name, transform_fn, scale_factor)

        # Evaluate
        metrics = evaluate_condition(model, condition_name)
        results[condition_name] = metrics

        if condition_name == "original":
            baseline = metrics

        # Print results
        diff = metrics["mAP50"] - baseline["mAP50"] if baseline else 0
        sign = "+" if diff >= 0 else ""
        print(f"  mAP50: {metrics['mAP50']*100:.1f}% ({sign}{diff*100:.1f}%)")
        print(f"  Recall: {metrics['recall']*100:.1f}%")

    # Print summary table
    print("\n" + "=" * 60)
    print("ROBUSTNESS TEST RESULTS")
    print("=" * 60)
    print(f"{'Condition':<25} {'mAP50':>10} {'Recall':>10} {'vs Base':>10}")
    print("-" * 60)

    for condition_name, metrics in results.items():
        diff = metrics["mAP50"] - baseline["mAP50"]
        sign = "+" if diff >= 0 else ""
        print(f"{condition_name:<25} {metrics['mAP50']*100:>9.1f}% {metrics['recall']*100:>9.1f}% {sign}{diff*100:>8.1f}%")

    print("-" * 60)

    # Identify weak points
    print("\n" + "=" * 60)
    print("WEAK POINTS (>10% drop)")
    print("=" * 60)

    weak_points = []
    for condition_name, metrics in results.items():
        if condition_name == "original":
            continue
        drop = baseline["mAP50"] - metrics["mAP50"]
        if drop > 0.10:
            weak_points.append((condition_name, drop))
            print(f"  - {condition_name}: -{drop*100:.1f}%")

    if not weak_points:
        print("  None! Model is robust across all conditions.")

    # Save results to file
    with open(OUTPUT_DIR / "results.txt", 'w') as f:
        f.write("ROBUSTNESS TEST RESULTS\n")
        f.write("=" * 60 + "\n")
        f.write(f"{'Condition':<25} {'mAP50':>10} {'Recall':>10} {'vs Base':>10}\n")
        f.write("-" * 60 + "\n")
        for condition_name, metrics in results.items():
            diff = metrics["mAP50"] - baseline["mAP50"]
            sign = "+" if diff >= 0 else ""
            f.write(f"{condition_name:<25} {metrics['mAP50']*100:>9.1f}% {metrics['recall']*100:>9.1f}% {sign}{diff*100:>8.1f}%\n")

    print(f"\nResults saved to: {OUTPUT_DIR / 'results.txt'}")

    return results, weak_points


if __name__ == "__main__":
    main()
