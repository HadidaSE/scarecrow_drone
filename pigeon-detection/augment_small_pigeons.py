"""
Augment training data with scaled-down images to improve small object detection.
Creates copies of training images with pigeons appearing smaller (simulating distance).
"""

import os
import cv2
import numpy as np
import shutil
from pathlib import Path

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data", "combined")
TRAIN_IMAGES = os.path.join(DATA_DIR, "train", "images")
TRAIN_LABELS = os.path.join(DATA_DIR, "train", "labels")

# Output directories for augmented data
AUG_DIR = os.path.join(DATA_DIR, "train_augmented")
AUG_IMAGES = os.path.join(AUG_DIR, "images")
AUG_LABELS = os.path.join(AUG_DIR, "labels")

# Scale factors (smaller = pigeons appear farther away)
SCALE_FACTORS = [0.5, 0.4, 0.3]


def scale_image_and_labels(img_path, label_path, scale_factor, output_img_path, output_label_path):
    """
    Scale down the content of an image (zoom out effect) and adjust labels.
    The image size stays the same, but content is shrunk and padded.
    """
    # Read image
    img = cv2.imread(img_path)
    if img is None:
        return False

    h, w = img.shape[:2]

    # Calculate new dimensions for the scaled content
    new_w = int(w * scale_factor)
    new_h = int(h * scale_factor)

    # Resize image content
    scaled = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

    # Create output image with padding (gray background simulating sky/ground)
    output = np.full((h, w, 3), 128, dtype=np.uint8)  # Gray background

    # Center the scaled image
    x_offset = (w - new_w) // 2
    y_offset = (h - new_h) // 2
    output[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = scaled

    # Save scaled image
    cv2.imwrite(output_img_path, output)

    # Adjust labels (YOLO format: class x_center y_center width height)
    if os.path.exists(label_path):
        with open(label_path, 'r') as f:
            lines = f.readlines()

        new_lines = []
        for line in lines:
            parts = line.strip().split()
            if len(parts) >= 5:
                cls = parts[0]
                x_center = float(parts[1])
                y_center = float(parts[2])
                bbox_w = float(parts[3])
                bbox_h = float(parts[4])

                # Scale and offset the coordinates
                new_x = x_center * scale_factor + (1 - scale_factor) / 2
                new_y = y_center * scale_factor + (1 - scale_factor) / 2
                new_bw = bbox_w * scale_factor
                new_bh = bbox_h * scale_factor

                # Only keep if bbox is still reasonable size (at least 1% of image)
                if new_bw > 0.01 and new_bh > 0.01:
                    new_lines.append(f"{cls} {new_x:.6f} {new_y:.6f} {new_bw:.6f} {new_bh:.6f}\n")

        # Only save if we have valid labels
        if new_lines:
            with open(output_label_path, 'w') as f:
                f.writelines(new_lines)
            return True

    return False


def add_motion_blur(img_path, output_path, kernel_size=15):
    """Add motion blur to image to augment for drone movement."""
    img = cv2.imread(img_path)
    if img is None:
        return False

    # Create motion blur kernel (horizontal)
    kernel = np.zeros((kernel_size, kernel_size))
    kernel[kernel_size // 2, :] = 1.0 / kernel_size

    # Apply blur
    blurred = cv2.filter2D(img, -1, kernel)
    cv2.imwrite(output_path, blurred)
    return True


def add_noise(img_path, output_path, noise_level=25):
    """Add Gaussian noise to image."""
    img = cv2.imread(img_path)
    if img is None:
        return False

    noise = np.random.normal(0, noise_level, img.shape).astype(np.float32)
    noisy = np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)
    cv2.imwrite(output_path, noisy)
    return True


def main():
    print("=" * 60)
    print("Small Object Augmentation for Pigeon Detection")
    print("=" * 60)

    # Create output directories
    os.makedirs(AUG_IMAGES, exist_ok=True)
    os.makedirs(AUG_LABELS, exist_ok=True)

    # Get list of training images
    image_files = [f for f in os.listdir(TRAIN_IMAGES) if f.endswith(('.jpg', '.jpeg', '.png'))]
    print(f"\nFound {len(image_files)} training images")

    # First, copy all original images and labels
    print("\nCopying original training data...")
    copied = 0
    for img_file in image_files:
        src_img = os.path.join(TRAIN_IMAGES, img_file)
        dst_img = os.path.join(AUG_IMAGES, img_file)
        shutil.copy2(src_img, dst_img)

        # Copy label if exists
        label_file = os.path.splitext(img_file)[0] + '.txt'
        src_label = os.path.join(TRAIN_LABELS, label_file)
        if os.path.exists(src_label):
            dst_label = os.path.join(AUG_LABELS, label_file)
            shutil.copy2(src_label, dst_label)
        copied += 1
    print(f"  Copied {copied} original images")

    # Generate scaled versions
    total_scaled = 0
    for scale in SCALE_FACTORS:
        print(f"\nGenerating {int(scale*100)}% scale images...")
        scale_count = 0

        for img_file in image_files:
            img_path = os.path.join(TRAIN_IMAGES, img_file)
            label_file = os.path.splitext(img_file)[0] + '.txt'
            label_path = os.path.join(TRAIN_LABELS, label_file)

            # Output filenames
            base_name = os.path.splitext(img_file)[0]
            ext = os.path.splitext(img_file)[1]
            out_img = os.path.join(AUG_IMAGES, f"{base_name}_scale{int(scale*100)}{ext}")
            out_label = os.path.join(AUG_LABELS, f"{base_name}_scale{int(scale*100)}.txt")

            if scale_image_and_labels(img_path, label_path, scale, out_img, out_label):
                scale_count += 1

        print(f"  Created {scale_count} images at {int(scale*100)}% scale")
        total_scaled += scale_count

    # Generate motion blur versions (mild)
    print(f"\nGenerating motion blur augmentations...")
    blur_count = 0
    for img_file in image_files[:len(image_files)//2]:  # Only half to avoid too much data
        img_path = os.path.join(TRAIN_IMAGES, img_file)
        label_file = os.path.splitext(img_file)[0] + '.txt'
        label_path = os.path.join(TRAIN_LABELS, label_file)

        base_name = os.path.splitext(img_file)[0]
        ext = os.path.splitext(img_file)[1]
        out_img = os.path.join(AUG_IMAGES, f"{base_name}_motionblur{ext}")
        out_label = os.path.join(AUG_LABELS, f"{base_name}_motionblur.txt")

        if add_motion_blur(img_path, out_img, kernel_size=15):
            if os.path.exists(label_path):
                shutil.copy2(label_path, out_label)
            blur_count += 1
    print(f"  Created {blur_count} motion blur images")

    # Generate noisy versions (moderate)
    print(f"\nGenerating noise augmentations...")
    noise_count = 0
    for img_file in image_files[:len(image_files)//2]:  # Only half
        img_path = os.path.join(TRAIN_IMAGES, img_file)
        label_file = os.path.splitext(img_file)[0] + '.txt'
        label_path = os.path.join(TRAIN_LABELS, label_file)

        base_name = os.path.splitext(img_file)[0]
        ext = os.path.splitext(img_file)[1]
        out_img = os.path.join(AUG_IMAGES, f"{base_name}_noisy{ext}")
        out_label = os.path.join(AUG_LABELS, f"{base_name}_noisy.txt")

        if add_noise(img_path, out_img, noise_level=30):
            if os.path.exists(label_path):
                shutil.copy2(label_path, out_label)
            noise_count += 1
    print(f"  Created {noise_count} noisy images")

    # Count total
    total_images = len(os.listdir(AUG_IMAGES))
    total_labels = len([f for f in os.listdir(AUG_LABELS) if f.endswith('.txt')])

    print("\n" + "=" * 60)
    print("AUGMENTATION COMPLETE")
    print("=" * 60)
    print(f"Original images: {len(image_files)}")
    print(f"Total augmented images: {total_images}")
    print(f"Total labels: {total_labels}")
    print(f"\nAugmented data saved to: {AUG_DIR}")

    # Create updated data.yaml
    aug_yaml = os.path.join(DATA_DIR, "data_augmented.yaml")
    with open(aug_yaml, 'w') as f:
        f.write(f"# Augmented dataset for improved small object detection\n")
        f.write(f"path: {DATA_DIR}\n")
        f.write(f"train: train_augmented/images\n")
        f.write(f"val: valid/images\n")
        f.write(f"test: test/images\n\n")
        f.write(f"names:\n")
        f.write(f"  0: pigeon\n")

    print(f"\nNew data config: {aug_yaml}")
    print("\nTo train with augmented data, update train_gpu.py to use:")
    print(f'  DATA_YAML = "{aug_yaml}"')


if __name__ == "__main__":
    main()
