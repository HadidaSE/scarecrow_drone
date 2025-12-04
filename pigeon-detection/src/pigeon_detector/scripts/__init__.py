# Pigeon Detector Package
from .pigeon_detector import PigeonDetector, Detection
from .camera_handler import (
    CameraBase,
    WebcamCamera,
    RealSenseCamera,
    ImageSource,
    VideoSource,
    ImageFolderSource,
    create_camera
)

__all__ = [
    'PigeonDetector',
    'Detection',
    'CameraBase',
    'WebcamCamera',
    'RealSenseCamera',
    'ImageSource',
    'VideoSource',
    'ImageFolderSource',
    'create_camera'
]
