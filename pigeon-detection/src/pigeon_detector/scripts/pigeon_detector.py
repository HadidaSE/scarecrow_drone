#!/usr/bin/env python3
"""
Pigeon Detection Module using YOLOv8
Designed for Intel Aero drone with RealSense camera
"""

import cv2
import numpy as np
from ultralytics import YOLO
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Detection:
    """Represents a single detection result"""
    class_name: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    center: Tuple[int, int]


class PigeonDetector:
    """YOLO-based pigeon detector optimized for drone deployment"""

    # COCO class ID for bird (pigeons detected as birds)
    BIRD_CLASS_ID = 14

    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        confidence_threshold: float = 0.5,
        iou_threshold: float = 0.45,
        device: str = "cpu",
        img_size: int = 640
    ):
        """
        Initialize the pigeon detector.

        Args:
            model_path: Path to YOLO weights (yolov8n.pt recommended for Intel Aero)
            confidence_threshold: Minimum confidence for detections
            iou_threshold: IoU threshold for NMS
            device: 'cpu' for Intel Aero, 'cuda' for GPU
            img_size: Inference image size
        """
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.device = device
        self.img_size = img_size

        # Load YOLO model
        print(f"Loading YOLO model: {model_path}")
        self.model = YOLO(model_path)
        self.model.to(device)
        print(f"Model loaded successfully on {device}")

        # Get class names from model
        self.class_names = self.model.names

    def detect(self, frame: np.ndarray) -> List[Detection]:
        """
        Detect pigeons (birds) in a frame.

        Args:
            frame: BGR image from camera

        Returns:
            List of Detection objects for birds found
        """
        # Run inference
        results = self.model(
            frame,
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
            imgsz=self.img_size,
            classes=[self.BIRD_CLASS_ID],  # Only detect birds
            verbose=False
        )

        detections = []

        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue

            for box in boxes:
                # Extract detection info
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                class_name = self.class_names[class_id]

                # Calculate center point
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2

                detection = Detection(
                    class_name=class_name,
                    confidence=confidence,
                    bbox=(x1, y1, x2, y2),
                    center=(center_x, center_y)
                )
                detections.append(detection)

        return detections

    def detect_and_annotate(
        self,
        frame: np.ndarray,
        box_color: Tuple[int, int, int] = (0, 255, 0),
        thickness: int = 2
    ) -> Tuple[np.ndarray, List[Detection]]:
        """
        Detect pigeons and draw bounding boxes on frame.

        Args:
            frame: BGR image from camera
            box_color: BGR color for bounding boxes
            thickness: Line thickness for boxes

        Returns:
            Tuple of (annotated_frame, detections)
        """
        detections = self.detect(frame)
        annotated = frame.copy()

        for det in detections:
            x1, y1, x2, y2 = det.bbox

            # Draw bounding box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), box_color, thickness)

            # Draw label with confidence
            label = f"Pigeon: {det.confidence:.2f}"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)

            # Background for label
            cv2.rectangle(
                annotated,
                (x1, y1 - label_size[1] - 10),
                (x1 + label_size[0], y1),
                box_color,
                -1
            )

            # Label text
            cv2.putText(
                annotated,
                label,
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 0),
                2
            )

            # Draw center point
            cv2.circle(annotated, det.center, 5, (0, 0, 255), -1)

        return annotated, detections


def run_webcam_demo(
    model_path: str = "yolov8n.pt",
    camera_id: int = 0,
    confidence: float = 0.5
):
    """
    Run pigeon detection on webcam feed.

    Args:
        model_path: Path to YOLO weights
        camera_id: Webcam device ID
        confidence: Detection confidence threshold
    """
    detector = PigeonDetector(
        model_path=model_path,
        confidence_threshold=confidence
    )

    cap = cv2.VideoCapture(camera_id)
    if not cap.isOpened():
        print(f"Error: Could not open camera {camera_id}")
        return

    print("Starting webcam detection. Press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame")
            break

        # Detect and annotate
        annotated, detections = detector.detect_and_annotate(frame)

        # Display detection count
        cv2.putText(
            annotated,
            f"Pigeons detected: {len(detections)}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

        # Show frame
        cv2.imshow("Pigeon Detector", annotated)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


def run_image_detection(
    image_path: str,
    model_path: str = "yolov8n.pt",
    confidence: float = 0.5,
    output_path: Optional[str] = None
):
    """
    Run pigeon detection on a single image.

    Args:
        image_path: Path to input image
        model_path: Path to YOLO weights
        confidence: Detection confidence threshold
        output_path: Optional path to save annotated image
    """
    detector = PigeonDetector(
        model_path=model_path,
        confidence_threshold=confidence
    )

    frame = cv2.imread(image_path)
    if frame is None:
        print(f"Error: Could not read image {image_path}")
        return

    annotated, detections = detector.detect_and_annotate(frame)

    print(f"Found {len(detections)} pigeon(s)")
    for i, det in enumerate(detections):
        print(f"  {i+1}. Confidence: {det.confidence:.2f}, Center: {det.center}")

    if output_path:
        cv2.imwrite(output_path, annotated)
        print(f"Saved annotated image to {output_path}")

    cv2.imshow("Pigeon Detection", annotated)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Pigeon Detection System")
    parser.add_argument("--mode", choices=["webcam", "image"], default="webcam",
                        help="Detection mode")
    parser.add_argument("--image", type=str, help="Path to image (for image mode)")
    parser.add_argument("--model", type=str, default="yolov8n.pt",
                        help="Path to YOLO model weights")
    parser.add_argument("--confidence", type=float, default=0.5,
                        help="Detection confidence threshold")
    parser.add_argument("--camera", type=int, default=0,
                        help="Webcam device ID")
    parser.add_argument("--output", type=str, help="Output path for annotated image")

    args = parser.parse_args()

    if args.mode == "webcam":
        run_webcam_demo(
            model_path=args.model,
            camera_id=args.camera,
            confidence=args.confidence
        )
    elif args.mode == "image":
        if not args.image:
            print("Error: --image required for image mode")
        else:
            run_image_detection(
                image_path=args.image,
                model_path=args.model,
                confidence=args.confidence,
                output_path=args.output
            )
