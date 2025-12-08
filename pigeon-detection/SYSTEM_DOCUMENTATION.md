# Pigeon Detection System - Technical Documentation

## Overview

This is a production-ready YOLOv8-based pigeon detection system designed for deployment on Intel Aero drones. It uses ROS (Robot Operating System) for camera integration and provides real-time detection capabilities.

---

## Directory Structure

```
pigeon-detection/
├── README.md                    # Project overview
├── SYSTEM_DOCUMENTATION.md      # This file
├── requirements.txt             # Python dependencies
├── train.py                     # Model training script
├── test_model.py                # Model testing/inference script
├── data/                        # Training dataset (not in repo)
│   └── images/pigeons.v1i.yolov8/data.yaml
├── runs/                        # Training outputs
│   └── pigeon_detector_v2/
│       ├── weights/
│       │   ├── best.pt          # Best model weights (6.0 MB)
│       │   └── last.pt          # Last checkpoint
│       ├── results.csv          # Training metrics per epoch
│       ├── args.yaml            # Training configuration
│       ├── confusion_matrix.png
│       ├── F1_curve.png
│       ├── P_curve.png
│       ├── R_curve.png
│       ├── PR_curve.png
│       └── results.png
└── src/pigeon_detector/         # ROS Package
    ├── CMakeLists.txt           # ROS build config
    ├── package.xml              # ROS package metadata
    ├── config/
    │   └── detector_config.yaml # Runtime configuration
    ├── launch/
    │   ├── detector.launch      # Development launch (webcam)
    │   └── intel_aero.launch    # Production launch (drone)
    └── scripts/
        ├── __init__.py
        ├── pigeon_detector.py   # Core YOLO detection module
        ├── detector_node.py     # ROS detector node
        ├── camera_handler.py    # Multi-source camera interface
        └── camera_node.py       # ROS camera publisher node
```

---

## Model Performance

| Metric | Value |
|--------|-------|
| **Model** | YOLOv8 Nano |
| **Size** | 6.0 MB |
| **Precision** | 95.8% |
| **Recall** | 89% |
| **mAP50** | 94.12% |
| **mAP50-95** | 43.5% |
| **Confidence Threshold** | 0.5 |
| **IoU Threshold** | 0.45 |
| **Target Class** | COCO class 14 (birds) |
| **Input Size** | 640x640 |

### Training Progress (Selected Epochs)

| Epoch | Precision | Recall | mAP50 | Train Loss | Val Loss |
|-------|-----------|--------|-------|------------|----------|
| 1     | 57.98%    | 20.20% | 47.23%| 5.61       | 7.94     |
| 12    | 85.47%    | 78.90% | 81.71%| 3.24       | 3.60     |
| 18    | 92.27%    | 87.81% | 93.34%| 3.05       | 3.28     |
| 25    | 93.60%    | 89.12% | 94.12%| 2.68       | 3.42     |

---

## Core Components

### 1. PigeonDetector (`pigeon_detector.py`)

Main detection class using YOLOv8.

```python
from pigeon_detector import PigeonDetector, Detection

# Initialize
detector = PigeonDetector(
    model_path="runs/pigeon_detector_v2/weights/best.pt",
    confidence_threshold=0.5,
    iou_threshold=0.45,
    device="cpu"  # or "cuda"
)

# Detect without annotation
detections: List[Detection] = detector.detect(frame)

# Detect with annotation
annotated_frame, detections = detector.detect_and_annotate(frame)

# Run webcam demo
detector.run_webcam_demo()
```

**Detection Dataclass:**
```python
@dataclass
class Detection:
    class_name: str      # Always "bird"
    confidence: float    # 0.0 - 1.0
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
    center: Tuple[int, int]          # (cx, cy)
```

### 2. Camera Handler (`camera_handler.py`)

Abstraction layer for multiple camera sources.

```python
from camera_handler import create_camera

# Webcam
cam = create_camera("webcam", device_id=0, width=640, height=480, fps=30)

# Intel RealSense
cam = create_camera("realsense", width=640, height=480, enable_depth=False)

# Video file
cam = create_camera("video", video_path="test.mp4", loop=True)

# Image file
cam = create_camera("image", image_path="test.jpg")

# Image folder
cam = create_camera("folder", folder_path="images/")

# Usage
success, frame = cam.read()
cam.release()
```

**Supported Sources:**
- `WebcamCamera` - USB webcam via OpenCV
- `RealSenseCamera` - Intel RealSense D400/R200 series
- `ImageSource` - Single image file
- `VideoSource` - Video file (with optional loop)
- `ImageFolderSource` - Batch processing from folder

### 3. ROS Detector Node (`detector_node.py`)

Subscribes to camera feed and publishes detections.

**Subscribed Topics:**
- `/camera/rgb/image_raw` (sensor_msgs/Image)

**Published Topics:**
- `/pigeon_detector/count` (std_msgs/Int32) - Number of pigeons detected
- `/pigeon_detector/detections` (std_msgs/String) - JSON detection details
- `/pigeon_detector/centers` (geometry_msgs/Point) - Center coordinates
- `/pigeon_detector/image_annotated` (sensor_msgs/Image) - Annotated frame

**Detection JSON Format:**
```json
{
    "class": "bird",
    "confidence": 0.95,
    "bbox": [100, 50, 200, 150],
    "center": [150, 100]
}
```

### 4. ROS Camera Node (`camera_node.py`)

Publishes camera frames to ROS topic.

**Published Topics:**
- `/camera/rgb/image_raw` (sensor_msgs/Image) at 10 Hz

---

## Configuration

### detector_config.yaml

```yaml
camera:
  source: "webcam"           # webcam, realsense, image, video
  device_id: 0
  width: 640
  height: 480
  fps: 30

model:
  weights: "yolov8n.pt"      # or path to best.pt
  confidence_threshold: 0.5
  iou_threshold: 0.45
  device: "cpu"              # cpu or cuda
  img_size: 640

detection:
  target_class: "bird"
  draw_boxes: true
  box_color: [0, 255, 0]     # BGR green

ros:
  input_topic: "/camera/rgb/image_raw"
  output_topic: "/pigeon_detector/detections"
  image_output_topic: "/pigeon_detector/image_annotated"
  publish_rate: 10           # Hz
```

---

## Launch Files

### Development (Webcam)

```bash
roslaunch pigeon_detector detector.launch
roslaunch pigeon_detector detector.launch use_webcam:=false  # External camera
```

### Production (Intel Aero Drone)

```bash
roslaunch pigeon_detector intel_aero.launch
```

This launch file:
1. Starts RealSense R200 camera driver
2. Remaps camera topic to `/camera/color/image_raw`
3. Launches detector node

---

## Detection Pipeline

```
┌─────────────────┐
│  Camera Source  │  (Webcam / RealSense / Video / Image)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Camera Node    │  Publishes at 10 Hz
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│  /camera/rgb/image_raw      │  ROS Topic (sensor_msgs/Image)
└────────┬────────────────────┘
         │
         ▼
┌─────────────────┐
│  Detector Node  │  YOLOv8 Inference
└────────┬────────┘
         │
    ┌────┴────┬────────────┬─────────────┐
    ▼         ▼            ▼             ▼
┌───────┐ ┌────────┐ ┌──────────┐ ┌────────────┐
│ count │ │ detec- │ │ centers  │ │ annotated  │
│ Int32 │ │ tions  │ │ Point    │ │ image      │
└───────┘ │ JSON   │ └──────────┘ └────────────┘
          └────────┘
```

---

## Training

### Dataset

- **Source**: Roboflow - https://universe.roboflow.com/spirosmakris/pigeons-qbzpj
- **Format**: YOLOv8 format
- **Split**: 831 train / 76 val / 37 test images

### Training Script

```python
# train.py
from ultralytics import YOLO

model = YOLO("yolov8n.pt")  # Nano model

model.train(
    data="data/images/pigeons.v1i.yolov8/data.yaml",
    epochs=25,
    batch=16,
    imgsz=640,
    device="cpu",
    cache="ram",
    workers=8,
    patience=0,
    project="runs",
    name="pigeon_detector_v3"
)
```

### Training Configuration (args.yaml)

```yaml
task: detect
mode: train
model: yolov8n.pt
epochs: 25
batch: 16
imgsz: 640
device: cpu
optimizer: auto
lr0: 0.01
lrf: 0.01
momentum: 0.937
weight_decay: 0.0005
warmup_epochs: 3.0

# Data Augmentation
hsv_h: 0.015
hsv_s: 0.7
hsv_v: 0.4
translate: 0.1
scale: 0.5
fliplr: 0.5
mosaic: 1.0
erasing: 0.4
auto_augment: randaugment
```

---

## Dependencies

### requirements.txt

```
ultralytics>=8.0.0,<8.3.0    # YOLOv8
torch>=1.13.0,<2.1.0         # PyTorch
torchvision>=0.14.0,<0.16.0
opencv-python>=4.5.0,<4.9.0
numpy>=1.23.0,<1.25.0
Pillow>=9.0.0,<10.0.0
pyyaml>=6.0
```

### ROS Dependencies

```
rospy
sensor_msgs
std_msgs
geometry_msgs
cv_bridge
realsense_camera  # For Intel Aero
```

### Optional

```
pyrealsense2      # Intel RealSense SDK
```

---

## Hardware Requirements

### Development
- Python 3.8+
- 2+ GB RAM
- USB webcam or video files

### Production (Intel Aero Drone)
- Intel Atom processor
- RealSense R200 camera
- ROS Kinetic/Melodic
- 6+ MB storage for model

---

## Quick Start

### 1. Install Dependencies

```bash
cd pigeon-detection
pip install -r requirements.txt
```

### 2. Test Detection (No ROS)

```python
from src.pigeon_detector.scripts.pigeon_detector import PigeonDetector

detector = PigeonDetector(
    model_path="runs/pigeon_detector_v2/weights/best.pt"
)
detector.run_webcam_demo()
```

### 3. Run with ROS

```bash
# Terminal 1: Start ROS core
roscore

# Terminal 2: Launch detector
roslaunch pigeon_detector detector.launch

# Terminal 3: View detections
rostopic echo /pigeon_detector/count
rostopic echo /pigeon_detector/detections
```

---

## Integration with Scarecrow Drone Backend

The detection results can be consumed by the FastAPI backend via:

1. **ROS Topics** - Subscribe to `/pigeon_detector/count` for real-time updates
2. **WebSocket** - Forward detections to frontend via `/ws/frontend`
3. **Flight Records** - Store `pigeonsDetected` count in flight database

Frontend `Flight` type includes:
```typescript
interface Flight {
    // ...
    pigeonsDetected: number;
}
```

---

## Troubleshooting

### Model not loading
- Check path to `best.pt` is correct
- Ensure ultralytics version compatibility

### Camera not opening
- Verify device_id (try 0, 1, 2)
- Check camera permissions
- For RealSense: install `pyrealsense2`

### Low FPS
- Use CPU mode on Intel Aero (no CUDA)
- Reduce image size to 416
- Lower publish_rate in config

### ROS topics not publishing
- Check `roscore` is running
- Verify topic names in config
- Check cv_bridge installation

---

## File Locations Summary

| File | Purpose |
|------|---------|
| `runs/pigeon_detector_v2/weights/best.pt` | Trained model weights |
| `src/pigeon_detector/config/detector_config.yaml` | Runtime configuration |
| `src/pigeon_detector/scripts/pigeon_detector.py` | Core detection class |
| `src/pigeon_detector/scripts/detector_node.py` | ROS detector node |
| `src/pigeon_detector/scripts/camera_handler.py` | Camera abstraction |
| `src/pigeon_detector/launch/detector.launch` | Development launch |
| `src/pigeon_detector/launch/intel_aero.launch` | Production launch |
