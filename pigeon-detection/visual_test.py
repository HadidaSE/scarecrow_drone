"""
Visual test of pigeon detection model.
Tests on multiple image categories and saves all results in one folder.
Files are named with category prefix and detection count for easy sorting.
"""

from ultralytics import YOLO
from pathlib import Path
import random
import shutil
import cv2

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "test_results"

# Model to test
MODEL_PATH = BASE_DIR / "models" / "best_v4.pt"

# Test image sources (use valid as fallback if test doesn't exist)
TEST_SOURCES = {
    "pigeon": DATA_DIR / "combined" / "test" / "images",
    "bird": DATA_DIR / "Birds.v1i.yolov8" / "test" / "images",
    "harmful": DATA_DIR / "harmful objects.v1i.yolov8" / "test" / "images",
    "random": DATA_DIR / "random objects.v8i.yolov8" / "valid" / "images",  # no test folder
}

CONF_THRESHOLD = 0.5
IMAGES_PER_CATEGORY = 50  # 5x larger test


def get_sample_images(directory, count=50):
    """Get random sample of images from directory."""
    if not directory.exists():
        print(f"  Directory not found: {directory}")
        return []

    images = list(directory.glob("*.jpg")) + list(directory.glob("*.png")) + list(directory.glob("*.jpeg"))
    if len(images) > count:
        images = random.sample(images, count)
    return images


def main():
    print("=" * 60)
    print("VISUAL TEST - Pigeon Detection Model v4")
    print("=" * 60)
    print(f"Model: {MODEL_PATH}")
    print(f"Confidence threshold: {CONF_THRESHOLD}")
    print(f"Images per category: {IMAGES_PER_CATEGORY}")
    print()

    # Clean and create output directory
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)

    # Load model
    print("Loading model...")
    model = YOLO(str(MODEL_PATH))
    print()

    total_stats = {}
    all_results = []

    for category, source_dir in TEST_SOURCES.items():
        print(f"--- Testing {category.upper()} ---")

        images = get_sample_images(source_dir, IMAGES_PER_CATEGORY)
        if not images:
            print(f"  No images found, skipping...")
            total_stats[category] = {"images": 0, "detections": 0, "images_with_det": 0}
            continue

        print(f"  Testing {len(images)} images...")

        detections = 0
        images_with_det = 0

        for img_path in images:
            # Run inference
            results = model(str(img_path), conf=CONF_THRESHOLD, verbose=False)

            num_det = len(results[0].boxes)
            detections += num_det
            if num_det > 0:
                images_with_det += 1

            # Save result image with boxes
            result_img = results[0].plot()

            # Name: category_Xdet_originalname.jpg (easy to sort)
            out_name = f"{category}_{num_det}det_{img_path.name}"
            out_path = OUTPUT_DIR / out_name

            cv2.imwrite(str(out_path), result_img)
            all_results.append((category, num_det, out_name))

        total_stats[category] = {
            "images": len(images),
            "detections": detections,
            "images_with_det": images_with_det
        }

        print(f"  Found {detections} detections in {images_with_det}/{len(images)} images")
        print()

    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for cat, stats in total_stats.items():
        if cat == "pigeon":
            expected = "SHOULD detect"
            status = "OK" if stats['detections'] > 0 else "BAD"
        else:
            expected = "should be 0"
            status = "OK" if stats['detections'] == 0 else f"FALSE POSITIVES!"

        print(f"  {cat:10}: {stats['detections']:3} detections in {stats['images_with_det']:2}/{stats['images']:2} images ({expected}) [{status}]")

    # Count false positives
    false_positives = sum(
        stats['detections']
        for cat, stats in total_stats.items()
        if cat != "pigeon"
    )

    print()
    print(f"Total false positives: {false_positives}")
    print(f"All {len(all_results)} results saved to: {OUTPUT_DIR}")
    print()
    print("Tip: Sort by name to group by category, or by 'Xdet' to see detections first")


if __name__ == "__main__":
    main()
