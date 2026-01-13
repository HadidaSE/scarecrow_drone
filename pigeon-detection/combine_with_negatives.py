"""
Combine pigeon dataset with negative examples (other birds, random objects).
Negative examples get empty label files (no pigeon = nothing to detect).
Maintains ~1:2 ratio of positives to negatives (best practice).
"""

import os
import shutil
import random
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

# Source datasets
PIGEON_DIR = DATA_DIR / "combined"
BIRDS_DIR = DATA_DIR / "Birds.v1i.yolov8"
HARMFUL_DIR = DATA_DIR / "harmful objects.v1i.yolov8"
RANDOM_DIR = DATA_DIR / "random objects.v8i.yolov8"

# Output
OUTPUT_DIR = DATA_DIR / "final_dataset"

# Ratio: for every 1 pigeon image, include ~2 negative images
NEGATIVE_RATIO = 2


def copy_with_labels(src_images, src_labels, dst_images, dst_labels, prefix, empty_labels=False, max_images=None):
    """Copy images and labels with a prefix to avoid name collisions."""
    count = 0
    if not src_images.exists():
        print(f"  Skipping {src_images} (not found)")
        return 0

    # Get all image files
    all_images = [f for f in src_images.iterdir() if f.suffix.lower() in ['.jpg', '.jpeg', '.png']]

    # Randomly sample if max_images specified
    if max_images and len(all_images) > max_images:
        all_images = random.sample(all_images, max_images)

    for img_file in all_images:
        # New filename with prefix
        new_name = f"{prefix}_{img_file.name}"

        # Copy image
        shutil.copy2(img_file, dst_images / new_name)

        # Handle label
        label_file = src_labels / (img_file.stem + '.txt')
        new_label = dst_labels / (f"{prefix}_{img_file.stem}.txt")

        if empty_labels:
            # Create empty label file (no objects)
            new_label.touch()
        elif label_file.exists():
            shutil.copy2(label_file, new_label)
        else:
            # No label = empty file
            new_label.touch()

        count += 1

    return count


def main():
    print("=" * 60)
    print("Combining Datasets with Negative Examples")
    print("=" * 60)

    # Create output directories
    for split in ['train', 'valid', 'test']:
        (OUTPUT_DIR / split / 'images').mkdir(parents=True, exist_ok=True)
        (OUTPUT_DIR / split / 'labels').mkdir(parents=True, exist_ok=True)

    total_pigeon = 0
    total_negative = 0

    for split in ['train', 'valid', 'test']:
        print(f"\n--- Processing {split} split ---")

        dst_images = OUTPUT_DIR / split / 'images'
        dst_labels = OUTPUT_DIR / split / 'labels'

        # 1. Copy pigeon images (with their labels)
        src_img = PIGEON_DIR / split / 'images'
        src_lbl = PIGEON_DIR / split / 'labels'
        pigeon_count = copy_with_labels(src_img, src_lbl, dst_images, dst_labels, 'pigeon', empty_labels=False)
        print(f"  Pigeons: {pigeon_count} images")
        total_pigeon += pigeon_count

        # Calculate how many negatives to include (1:2 ratio)
        # Split evenly among 3 negative sources
        max_negatives = pigeon_count * NEGATIVE_RATIO
        per_source = max_negatives // 3

        # 2. Copy birds (EMPTY labels - these are NOT pigeons)
        src_img = BIRDS_DIR / split / 'images'
        src_lbl = BIRDS_DIR / split / 'labels'
        count = copy_with_labels(src_img, src_lbl, dst_images, dst_labels, 'birds', empty_labels=True, max_images=per_source)
        print(f"  Other birds (negative): {count} images")
        total_negative += count

        # 3. Copy harmful objects (EMPTY labels)
        src_img = HARMFUL_DIR / split / 'images'
        src_lbl = HARMFUL_DIR / split / 'labels'
        count = copy_with_labels(src_img, src_lbl, dst_images, dst_labels, 'harmful', empty_labels=True, max_images=per_source)
        print(f"  Harmful objects (negative): {count} images")
        total_negative += count

        # 4. Copy random objects (EMPTY labels)
        src_img = RANDOM_DIR / split / 'images'
        src_lbl = RANDOM_DIR / split / 'labels'
        count = copy_with_labels(src_img, src_lbl, dst_images, dst_labels, 'random', empty_labels=True, max_images=per_source)
        print(f"  Random objects (negative): {count} images")
        total_negative += count

    # Create data.yaml
    yaml_content = f"""# Final dataset with pigeon positives and negative examples
path: {OUTPUT_DIR}
train: train/images
val: valid/images
test: test/images

nc: 1
names: ['pigeon']
"""

    with open(OUTPUT_DIR / 'data.yaml', 'w') as f:
        f.write(yaml_content)

    print("\n" + "=" * 60)
    print("COMBINATION COMPLETE")
    print("=" * 60)
    print(f"Total pigeon images: {total_pigeon}")
    print(f"Total negative images: {total_negative}")
    print(f"Output: {OUTPUT_DIR}")
    print(f"Config: {OUTPUT_DIR / 'data.yaml'}")


if __name__ == "__main__":
    main()
