# Pigeon Detection System

YOLOv8-based pigeon detection model for Intel Aero drone.

## Overview

This system uses a trained YOLOv8 nano model to detect pigeons from drone camera feeds. Designed for real-time detection on Intel Aero's limited compute resources.

## Model Performance

- **Precision**: 95.8%
- **Recall**: 89%
- **mAP50**: 93.3%
- **Confidence Threshold**: 0.5

## Structure

```
pigeon-detection/
├── src/                    # ROS package for drone integration
│   └── pigeon_detector/
│       ├── scripts/
│       │   ├── pigeon_detector.py  # YOLO detection module
│       │   └── camera_handler.py   # Camera input handlers
│       └── config/
│           └── detector_config.yaml
├── runs/                   # Training outputs
│   └── pigeon_detector_v2/
│       └── weights/
│           └── best.pt     # Trained model
├── train.py               # Training script
├── test_model.py          # Testing script
└── requirements.txt       # Python dependencies
```

## Requirements

- Python 3.8+
- ultralytics (YOLOv8)
- opencv-python
- numpy

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Training

```bash
python train.py
```

### Testing

```bash
python test_model.py
```

### Using the Model

```python
from ultralytics import YOLO

model = YOLO("runs/pigeon_detector_v2/weights/best.pt")
results = model.predict(source="image.jpg", conf=0.5)
```

## Dataset

Download the pigeon dataset from Roboflow before training:

1. Go to: https://universe.roboflow.com/spirosmakris/pigeons-qbzpj
2. Download in YOLOv8 format
3. Extract to `data/images/pigeons.v1i.yolov8/`

Dataset info:
- Train: 831 images
- Validation: 76 images
- Test: 37 images

## Hardware Target

- Intel Aero Drone
- Intel Atom processor
- RealSense R200 camera (1920x1080 RGB)
