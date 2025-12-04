#!/usr/bin/env python3
"""
Camera Input Handler for Pigeon Detection System
Supports: Webcam, Intel RealSense, Image files, Video files
"""

import cv2
import numpy as np
from abc import ABC, abstractmethod
from typing import Optional, Tuple, Generator
from pathlib import Path


class CameraBase(ABC):
    """Abstract base class for camera inputs"""

    @abstractmethod
    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Read a frame from the camera"""
        pass

    @abstractmethod
    def release(self):
        """Release camera resources"""
        pass

    @abstractmethod
    def is_opened(self) -> bool:
        """Check if camera is opened"""
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


class WebcamCamera(CameraBase):
    """Webcam input handler using OpenCV"""

    def __init__(
        self,
        device_id: int = 0,
        width: int = 640,
        height: int = 480,
        fps: int = 30
    ):
        """
        Initialize webcam.

        Args:
            device_id: Camera device ID
            width: Frame width
            height: Frame height
            fps: Target FPS
        """
        self.device_id = device_id
        self.cap = cv2.VideoCapture(device_id)

        if self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            self.cap.set(cv2.CAP_PROP_FPS, fps)
            print(f"Webcam {device_id} opened: {width}x{height} @ {fps}fps")
        else:
            print(f"Warning: Could not open webcam {device_id}")

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        return self.cap.read()

    def release(self):
        self.cap.release()

    def is_opened(self) -> bool:
        return self.cap.isOpened()


class RealSenseCamera(CameraBase):
    """Intel RealSense camera handler (for Intel Aero drone)"""

    def __init__(
        self,
        width: int = 640,
        height: int = 480,
        fps: int = 30,
        enable_depth: bool = False
    ):
        """
        Initialize RealSense camera.

        Args:
            width: Frame width
            height: Frame height
            fps: Target FPS
            enable_depth: Enable depth stream
        """
        self.width = width
        self.height = height
        self.fps = fps
        self.enable_depth = enable_depth
        self.pipeline = None
        self.align = None

        try:
            import pyrealsense2 as rs

            self.pipeline = rs.pipeline()
            config = rs.config()

            # Enable RGB stream
            config.enable_stream(
                rs.stream.color, width, height, rs.format.bgr8, fps
            )

            # Optionally enable depth
            if enable_depth:
                config.enable_stream(
                    rs.stream.depth, width, height, rs.format.z16, fps
                )
                self.align = rs.align(rs.stream.color)

            self.pipeline.start(config)
            print(f"RealSense camera started: {width}x{height} @ {fps}fps")

        except ImportError:
            print("Error: pyrealsense2 not installed. Install with: pip install pyrealsense2")
            self.pipeline = None
        except Exception as e:
            print(f"Error initializing RealSense: {e}")
            self.pipeline = None

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        if self.pipeline is None:
            return False, None

        try:
            frames = self.pipeline.wait_for_frames()

            if self.align:
                frames = self.align.process(frames)

            color_frame = frames.get_color_frame()
            if not color_frame:
                return False, None

            frame = np.asanyarray(color_frame.get_data())
            return True, frame

        except Exception as e:
            print(f"Error reading RealSense frame: {e}")
            return False, None

    def read_with_depth(self) -> Tuple[bool, Optional[np.ndarray], Optional[np.ndarray]]:
        """Read RGB and depth frames"""
        if self.pipeline is None or not self.enable_depth:
            return False, None, None

        try:
            frames = self.pipeline.wait_for_frames()

            if self.align:
                frames = self.align.process(frames)

            color_frame = frames.get_color_frame()
            depth_frame = frames.get_depth_frame()

            if not color_frame or not depth_frame:
                return False, None, None

            color = np.asanyarray(color_frame.get_data())
            depth = np.asanyarray(depth_frame.get_data())

            return True, color, depth

        except Exception as e:
            print(f"Error reading RealSense frames: {e}")
            return False, None, None

    def release(self):
        if self.pipeline:
            self.pipeline.stop()

    def is_opened(self) -> bool:
        return self.pipeline is not None


class ImageSource(CameraBase):
    """Image file input handler"""

    def __init__(self, image_path: str):
        """
        Initialize image source.

        Args:
            image_path: Path to image file
        """
        self.image_path = Path(image_path)
        self.frame = cv2.imread(str(self.image_path))
        self.read_once = False

        if self.frame is not None:
            print(f"Loaded image: {self.image_path} ({self.frame.shape[1]}x{self.frame.shape[0]})")
        else:
            print(f"Error: Could not load image {self.image_path}")

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        if self.frame is not None and not self.read_once:
            self.read_once = True
            return True, self.frame.copy()
        return False, None

    def release(self):
        self.frame = None

    def is_opened(self) -> bool:
        return self.frame is not None


class VideoSource(CameraBase):
    """Video file input handler"""

    def __init__(self, video_path: str, loop: bool = False):
        """
        Initialize video source.

        Args:
            video_path: Path to video file
            loop: Loop video when finished
        """
        self.video_path = Path(video_path)
        self.loop = loop
        self.cap = cv2.VideoCapture(str(self.video_path))

        if self.cap.isOpened():
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(self.cap.get(cv2.CAP_PROP_FPS))
            frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            print(f"Loaded video: {self.video_path} ({width}x{height} @ {fps}fps, {frames} frames)")
        else:
            print(f"Error: Could not load video {self.video_path}")

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        ret, frame = self.cap.read()

        if not ret and self.loop:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.cap.read()

        return ret, frame

    def release(self):
        self.cap.release()

    def is_opened(self) -> bool:
        return self.cap.isOpened()


class ImageFolderSource(CameraBase):
    """Image folder input handler for batch processing"""

    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}

    def __init__(self, folder_path: str, sort: bool = True):
        """
        Initialize image folder source.

        Args:
            folder_path: Path to folder containing images
            sort: Sort images by name
        """
        self.folder_path = Path(folder_path)
        self.images = [
            p for p in self.folder_path.iterdir()
            if p.suffix.lower() in self.SUPPORTED_FORMATS
        ]

        if sort:
            self.images.sort()

        self.index = 0
        print(f"Found {len(self.images)} images in {self.folder_path}")

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        if self.index >= len(self.images):
            return False, None

        image_path = self.images[self.index]
        frame = cv2.imread(str(image_path))
        self.index += 1

        if frame is not None:
            return True, frame
        return False, None

    def release(self):
        self.images = []

    def is_opened(self) -> bool:
        return len(self.images) > 0 and self.index < len(self.images)

    def get_current_image_name(self) -> str:
        """Get name of current image"""
        if 0 < self.index <= len(self.images):
            return self.images[self.index - 1].name
        return ""


def create_camera(
    source_type: str,
    **kwargs
) -> CameraBase:
    """
    Factory function to create camera instance.

    Args:
        source_type: One of "webcam", "realsense", "image", "video", "folder"
        **kwargs: Arguments passed to camera constructor

    Returns:
        CameraBase instance
    """
    sources = {
        "webcam": WebcamCamera,
        "realsense": RealSenseCamera,
        "image": ImageSource,
        "video": VideoSource,
        "folder": ImageFolderSource
    }

    if source_type not in sources:
        raise ValueError(f"Unknown source type: {source_type}. Choose from {list(sources.keys())}")

    return sources[source_type](**kwargs)


if __name__ == "__main__":
    # Test webcam
    print("Testing webcam...")
    with create_camera("webcam", device_id=0) as cam:
        if cam.is_opened():
            for _ in range(10):
                ret, frame = cam.read()
                if ret:
                    print(f"Frame shape: {frame.shape}")
                    cv2.imshow("Test", frame)
                    if cv2.waitKey(100) & 0xFF == ord('q'):
                        break
    cv2.destroyAllWindows()
    print("Webcam test complete")
