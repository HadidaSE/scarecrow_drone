"""
Pigeon Detection from Video Stream

This module provides real-time pigeon detection from an RTP video stream sent by a drone.
Uses ffmpeg to decode the RTP stream and YOLO model for object detection.

Drone Setup Command:
    Run this command on the drone to stream video at 1fps (recommended):
    
    gst-launch-1.0 -v \\
        v4l2src device=/dev/video13 ! \\
        video/x-raw,width=640,height=480,framerate=30/1 ! \\
        videorate ! video/x-raw,framerate=1/1 ! \\
        videoconvert ! \\
        jpegenc quality=85 ! \\
        rtpjpegpay ! \\
        udpsink host=192.168.1.3 port=5000
    
    Explanation:
    - v4l2src: Captures video from camera device /dev/video13
    - framerate=30/1: Camera captures at 30fps
    - videorate: Reduces framerate for efficient transmission
    - framerate=1/1: Outputs 1 frame per second (reduces bandwidth)
    - videoconvert: Converts to compatible format
    - jpegenc quality=85: Compresses with JPEG at 85% quality
    - rtpjpegpay: Packages as RTP stream
    - udpsink: Sends to PC at 192.168.1.3:5000
    
    Alternative (30fps - higher bandwidth):
    If you prefer processing on PC side, use framerate=30/1 without videorate.

Requirements:
    - ffmpeg installed and in PATH
    - drone.sdp file with stream configuration
    - YOLO model weights file
    - Required Python packages: opencv-python, numpy, ultralytics

Author: Scarecrow Drone Project
Date: December 30, 2025
"""

from __future__ import annotations

import shutil
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np
from ultralytics import YOLO
from ultralytics.engine.results import Results


@dataclass
class DetectionConfig:
    """Configuration settings for pigeon detection system."""
    
    model_path: str = "..\\pigeon-detection\\runs\\best_v3.pt"
    confidence_threshold: float = 0.5
    sdp_file: str = "drone.sdp"
    frames_dir: str = "frames"
    detections_dir: str = "pigeon_detections"
    save_detections: bool = True
    save_all_frames: bool = False
    process_interval: float = 1.0  # Process 1 frame per second
    frame_width: int = 640
    frame_height: int = 480
    ffmpeg_buffer_size: int = 10**8
    stats_interval: int = 30  # Print stats every N processed frames


@dataclass
class DetectionStats:
    """Statistics for detection session."""
    
    frames_received: int = 0
    frames_processed: int = 0
    detections_count: int = 0
    total_pigeons: int = 0
    start_time: float = 0.0
    
    def get_elapsed_time(self) -> float:
        """Get elapsed time since start."""
        return time.time() - self.start_time
    
    def get_process_fps(self) -> float:
        """Calculate processing frames per second."""
        elapsed = self.get_elapsed_time()
        return self.frames_processed / elapsed if elapsed > 0 else 0.0


class PigeonDetector:
    """
    Real-time pigeon detection from RTP video stream.
    
    This class handles:
    - Stream decoding via ffmpeg
    - Frame processing and rate limiting
    - YOLO-based pigeon detection
    - Detection visualization and logging
    """
    
    def __init__(self, config: Optional[DetectionConfig] = None) -> None:
        """
        Initialize the pigeon detector.
        
        Args:
            config: Detection configuration. If None, uses default config.
        """
        self.config = config or DetectionConfig()
        self.model: Optional[YOLO] = None
        self.ffmpeg_process: Optional[subprocess.Popen] = None
        self.stats = DetectionStats()
        self.frames_dir: Optional[Path] = None
        self.detections_dir: Optional[Path] = None
        self.last_process_time: float = 0.0
        self.first_frame: bool = True
    
    def setup_directories(self) -> None:
        """Setup output directories for frames and detections."""
        # Setup frames directory
        self.frames_dir = Path(self.config.frames_dir)
        if self.frames_dir.exists():
            print(f"Clearing existing frames in {self.config.frames_dir}/...")
            shutil.rmtree(self.frames_dir)
        self.frames_dir.mkdir(exist_ok=True)
        print(f"Frames directory ready: {self.config.frames_dir}/")
        
        # Setup detections directory (always clear and create, regardless of save setting)
        self.detections_dir = Path(self.config.detections_dir)
        if self.detections_dir.exists():
            print(f"Clearing existing detections in {self.config.detections_dir}/...")
            shutil.rmtree(self.detections_dir)
        self.detections_dir.mkdir(exist_ok=True)
        print(f"Detections directory ready: {self.config.detections_dir}/")
    
    def load_model(self) -> bool:
        """
        Load YOLO model from configured path.
        
        Returns:
            True if model loaded successfully, False otherwise.
        """
        print("Loading YOLO model...")
        model_path = Path(self.config.model_path)
        
        if not model_path.exists():
            print(f"ERROR: Model not found at {self.config.model_path}")
            return False
        
        self.model = YOLO(str(model_path))
        print("Model loaded!")
        return True
    
    def start_ffmpeg_stream(self) -> bool:
        """
        Start ffmpeg subprocess to decode RTP stream.
        
        Returns:
            True if ffmpeg started successfully, False otherwise.
        """
        print("Starting ffmpeg to decode stream...")
        
        ffmpeg_cmd = [
            'ffmpeg',
            '-hide_banner',
            '-loglevel', 'error',
            '-protocol_whitelist', 'file,udp,rtp',
            '-i', self.config.sdp_file,
            '-f', 'rawvideo',
            '-pix_fmt', 'bgr24',
            '-an',
            'pipe:1'
        ]
        
        try:
            self.ffmpeg_process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=self.config.ffmpeg_buffer_size
            )
            return True
        except FileNotFoundError:
            print("ERROR: ffmpeg not found. Please install ffmpeg and add it to PATH.")
            print("Download from: https://www.gyan.dev/ffmpeg/builds/")
            return False
    
    def should_process_frame(self) -> bool:
        """
        Determine if enough time has passed to process next frame.
        
        Returns:
            True if frame should be processed, False otherwise.
        """
        current_time = time.time()
        if current_time - self.last_process_time >= self.config.process_interval:
            self.last_process_time = current_time
            return True
        return False
    
    def read_frame(self) -> Optional[bytes]:
        """
        Read raw frame data from ffmpeg stdout.
        
        Returns:
            Raw frame bytes if successful, None if stream ended.
        """
        if not self.ffmpeg_process:
            return None
        
        frame_size = self.config.frame_width * self.config.frame_height * 3
        raw_frame = self.ffmpeg_process.stdout.read(frame_size)
        
        if len(raw_frame) != frame_size:
            return None
        
        return raw_frame
    
    def convert_frame(self, raw_frame: bytes) -> np.ndarray:
        """
        Convert raw frame bytes to numpy array.
        
        Args:
            raw_frame: Raw frame data from ffmpeg.
            
        Returns:
            Frame as numpy array in BGR format.
        """
        return np.frombuffer(raw_frame, dtype=np.uint8).reshape(
            (self.config.frame_height, self.config.frame_width, 3)
        )
    
    def save_frame(self, frame: np.ndarray) -> None:
        """
        Save frame to disk if enabled.
        
        Args:
            frame: Frame to save as numpy array.
        """
        if self.config.save_all_frames and self.frames_dir:
            filename = self.frames_dir / f"frame_{self.stats.frames_processed:06d}.jpg"
            cv2.imwrite(str(filename), frame)
    
    def detect_pigeons(self, frame: np.ndarray) -> Results:
        """
        Run YOLO detection on frame.
        
        Args:
            frame: Input frame as numpy array.
            
        Returns:
            YOLO detection results.
        """
        if not self.model:
            raise RuntimeError("Model not loaded")
        
        results = self.model(frame, conf=self.config.confidence_threshold, verbose=False)
        return results[0]
    
    def process_detection(self, result: Results, frame: np.ndarray) -> int:
        """
        Process detection results and log findings.
        
        Args:
            result: YOLO detection result.
            frame: Original frame for saving annotated image.
            
        Returns:
            Number of pigeons detected in frame.
        """
        num_pigeons = len(result.boxes)
        
        if num_pigeons == 0:
            return 0
        
        self.stats.detections_count += 1
        self.stats.total_pigeons += num_pigeons
        
        # Log detection
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] PIGEON DETECTED! Processed frame {self.stats.frames_processed} "
              f"(received frame {self.stats.frames_received}): {num_pigeons} pigeon(s)")
        
        # Print bounding box details
        for i, box in enumerate(result.boxes):
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            confidence = box.conf[0].cpu().numpy()
            width = x2 - x1
            height = y2 - y1
            print(f"            Box {i+1}: [x={int(x1)}, y={int(y1)}, "
                  f"w={int(width)}, h={int(height)}] confidence={confidence:.2f}")
        
        # Save annotated image
        if self.config.save_detections and self.detections_dir:
            annotated = result.plot()
            timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = self.detections_dir / f"pigeon_{timestamp_str}_frame{self.stats.frames_processed}.jpg"
            cv2.imwrite(str(filename), annotated)
            print(f"            Saved: {filename.name}")
        
        return num_pigeons
    
    def print_stats(self) -> None:
        """Print periodic statistics."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        fps = self.stats.get_process_fps()
        print(f"[{timestamp}] Received: {self.stats.frames_received:,} | "
              f"Processed: {self.stats.frames_processed} | "
              f"Process FPS: {fps:.1f} | "
              f"Detections: {self.stats.detections_count}")
    
    def print_summary(self) -> None:
        """Print final detection summary."""
        elapsed = self.stats.get_elapsed_time()
        
        print()
        print("=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Duration: {elapsed:.1f} seconds")
        print(f"Frames Received: {self.stats.frames_received:,}")
        print(f"Frames Processed: {self.stats.frames_processed:,}")
        
        if self.stats.frames_processed > 0:
            print(f"Average Process FPS: {self.stats.get_process_fps():.1f}")
            print(f"Frames with Pigeons: {self.stats.detections_count}")
            print(f"Total Pigeons: {self.stats.total_pigeons}")
        
        if self.config.save_all_frames:
            print(f"All frames saved to: {self.config.frames_dir}/")
        
        if self.config.save_detections and self.stats.detections_count > 0:
            print(f"Detection images saved to: {self.config.detections_dir}/")
        
        print("=" * 60)
    
    def cleanup(self) -> None:
        """Cleanup resources and terminate ffmpeg process."""
        if self.ffmpeg_process:
            self.ffmpeg_process.terminate()
            self.ffmpeg_process.wait()
    
    def run(self) -> None:
        """Main detection loop."""
    def run(self) -> None:
        """Main detection loop."""
        print("=" * 60)
        print("PIGEON DETECTION SYSTEM")
        print("=" * 60)
        print(f"Stream: {self.config.sdp_file}")
        print(f"Model: {self.config.model_path}")
        print(f"Confidence: {self.config.confidence_threshold}")
        print(f"Process Interval: {self.config.process_interval}s")
        print("=" * 60)
        
        # Setup
        self.setup_directories()
        
        if not self.load_model():
            return
        
        if not self.start_ffmpeg_stream():
            return
        
        print("=" * 60)
        print("Waiting for stream... (this may take a few seconds)")
        print("=" * 60)
        
        # Initialize timing
        self.stats.start_time = time.time()
        self.last_process_time = 0.0
        
        try:
            while True:
                # Read raw frame (MUST read all frames or pipe blocks)
                raw_frame = self.read_frame()
                if raw_frame is None:
                    print("Stream ended or incomplete frame")
                    break
                
                # First frame info
                if self.first_frame:
                    print(f"First frame received! Size: {self.config.frame_width}x{self.config.frame_height}")
                    print(f"Processing 1 frame per {self.config.process_interval} second(s)")
                    print()
                    self.first_frame = False
                
                self.stats.frames_received += 1
                
                # Skip frame if not enough time has passed
                if not self.should_process_frame():
                    continue
                
                self.stats.frames_processed += 1
                
                # Convert frame only when we need to process it
                frame = self.convert_frame(raw_frame)
                
                # Save frame if enabled
                self.save_frame(frame)
                
                # Run detection
                result = self.detect_pigeons(frame)
                
                # Process detections
                self.process_detection(result, frame)
                
                # Periodic stats
                if (self.stats.frames_processed > 0 and 
                    self.stats.frames_processed % self.config.stats_interval == 0):
                    self.print_stats()
        
        except KeyboardInterrupt:
            print("\nStopping...")
        
        finally:
            self.cleanup()
            self.print_summary()


def main() -> None:
    """Main entry point for the detection script."""
    config = DetectionConfig()
    
    detector = PigeonDetector(config)
    detector.run()


if __name__ == "__main__":
    main()

