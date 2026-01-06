"""
Detection Service
Manages pigeon detection from video stream during flights
"""
import subprocess
import os
import sys
from pathlib import Path
from typing import Optional
import threading


class DetectionService:
    """Manages detection process lifecycle"""

    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._detection_process: Optional[subprocess.Popen] = None
        self._current_flight_id: Optional[int] = None
        self._detection_count = 0
        
        # Path to detection script
        self._project_root = Path(__file__).parent.parent.parent.parent
        self._detection_script = self._project_root / "live_detection" / "detect.py"
        self._drone_sdp = self._project_root / "live_detection" / "drone.sdp"
        
    def start_detection(self, flight_id: int, stream_source: str = "drone") -> dict:
        """
        Start pigeon detection from video stream
        
        Args:
            flight_id: Database flight ID to associate detections with
            stream_source: "drone" for drone.sdp or "droneb5" for droneb5.sdp
            
        Returns:
            dict with success status
        """
        if self._detection_process is not None:
            return {"success": False, "error": "Detection already running"}
        
        # Check if detection script exists
        if not self._detection_script.exists():
            return {
                "success": False, 
                "error": f"Detection script not found at {self._detection_script}"
            }
        
        # Determine SDP file
        sdp_file = self._project_root / "live_detection" / f"{stream_source}.sdp"
        if not sdp_file.exists():
            sdp_file = self._drone_sdp
            
        if not sdp_file.exists():
            return {
                "success": False,
                "error": f"SDP file not found at {sdp_file}"
            }
        
        try:
            # Start detection process in background
            # The detect.py script will handle video stream and detection
            self._detection_process = subprocess.Popen(
                [sys.executable, str(self._detection_script), 
                 "--stream", str(sdp_file),
                 "--flight-id", str(flight_id),
                 "--save-detections"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(self._detection_script.parent)
            )
            
            self._current_flight_id = flight_id
            self._detection_count = 0
            
            return {
                "success": True,
                "message": f"Detection started for flight {flight_id}",
                "pid": self._detection_process.pid
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to start detection: {str(e)}"}
    
    def stop_detection(self) -> dict:
        """
        Stop the detection process
        
        Returns:
            dict with success status and detection count
        """
        if self._detection_process is None:
            return {"success": False, "error": "No detection process running"}
        
        try:
            # Terminate the process
            self._detection_process.terminate()
            
            # Wait for process to finish (with timeout)
            try:
                stdout, stderr = self._detection_process.communicate(timeout=5)
                
                # Parse detection count from output if available
                # detect.py should print "Total detections: X"
                for line in stdout.split('\n'):
                    if 'Total detections:' in line or 'Frames with pigeons:' in line:
                        try:
                            count = int(line.split(':')[-1].strip())
                            self._detection_count = count
                        except:
                            pass
                            
            except subprocess.TimeoutExpired:
                # Force kill if doesn't terminate
                self._detection_process.kill()
                stdout, stderr = self._detection_process.communicate()
            
            flight_id = self._current_flight_id
            detection_count = self._detection_count
            
            # Reset state
            self._detection_process = None
            self._current_flight_id = None
            self._detection_count = 0
            
            return {
                "success": True,
                "flight_id": flight_id,
                "detection_count": detection_count,
                "message": f"Detection stopped. Found {detection_count} frames with pigeons."
            }
            
        except Exception as e:
            self._detection_process = None
            return {"success": False, "error": f"Error stopping detection: {str(e)}"}
    
    def is_running(self) -> bool:
        """Check if detection is currently running"""
        if self._detection_process is None:
            return False
        
        # Check if process is still alive
        if self._detection_process.poll() is not None:
            # Process has ended
            self._detection_process = None
            return False
            
        return True
    
    def get_status(self) -> dict:
        """Get current detection status"""
        return {
            "running": self.is_running(),
            "flight_id": self._current_flight_id,
            "detection_count": self._detection_count
        }
    
    def start_drone_stream(self) -> dict:
        """
        Start video stream on the drone
        Command drone to start streaming video via gstreamer
        
        Returns:
            dict with success status
        """
        # This would SSH to drone and run gstreamer command
        # For now, assume stream is manually started or handled elsewhere
        return {
            "success": True,
            "message": "Drone stream should be started manually with gstreamer"
        }
    
    def stop_drone_stream(self) -> dict:
        """Stop video stream on the drone"""
        # Would SSH and kill gstreamer process
        return {"success": True}
