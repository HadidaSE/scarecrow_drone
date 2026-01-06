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
        print("\n=== STARTING DETECTION ===")
        print(f"Flight ID: {flight_id}")
        print(f"Stream Source: {stream_source}")
        
        if self._detection_process is not None:
            print("[ERROR] Detection already running!")
            return {"success": False, "error": "Detection already running"}
        
        # Check if detection script exists
        if not self._detection_script.exists():
            print(f"[ERROR] Detection script not found at {self._detection_script}")
            return {
                "success": False, 
                "error": f"Detection script not found at {self._detection_script}"
            }
        
        # Determine SDP file
        sdp_file = self._project_root / "live_detection" / f"{stream_source}.sdp"
        if not sdp_file.exists():
            sdp_file = self._drone_sdp
        
        print(f"[INFO] Detection script: {self._detection_script}")
        print(f"[INFO] SDP file: {sdp_file}")
            
        if not sdp_file.exists():
            print(f"[ERROR] SDP file not found at {sdp_file}")
            return {
                "success": False,
                "error": f"SDP file not found at {sdp_file}"
            }
        
        try:
            # Use the project's global venv Python (at project root .venv)
            # Navigate up from backend to project root
            project_root = self._project_root
            python_exe = project_root / ".venv" / "Scripts" / "python.exe"
            
            # Fallback to system Python if venv not found
            if not python_exe.exists():
                print(f"[WARNING] Project venv not found at {python_exe}, using system Python")
                python_exe = "python"
            else:
                python_exe = str(python_exe)
                print(f"[INFO] Using project venv Python: {python_exe}")
            
            # Start detection process in background
            # The detect.py script will handle video stream and detection
            print(f"[INFO] Starting detection subprocess...")
            print(f"[INFO] Detection script: {self._detection_script}")
            print(f"[INFO] Args: --stream {sdp_file} --flight-id {flight_id} --save-detections")
            
            self._detection_process = subprocess.Popen(
                [str(python_exe), "-u", str(self._detection_script),
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
            
            print(f"[SUCCESS] Detection process started with PID: {self._detection_process.pid}")
            print(f"[INFO] Detection is now listening for video stream...")
            print("=== DETECTION STARTED ===")
            
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
            dict with success status, detection count, and frames processed
        """
        import json

        print("\n=== STOPPING DETECTION ===")

        if self._detection_process is None:
            print("[WARNING] No detection process running")
            return {"success": False, "error": "No detection process running"}

        try:
            print(f"[INFO] Terminating detection process (PID: {self._detection_process.pid})...")
            # Terminate the process
            self._detection_process.terminate()

            # Wait for process to finish (with timeout)
            detection_result = None
            frames_processed = 0
            frames_received = 0
            total_pigeons = 0
            duration = 0.0
            average_fps = 0.0

            try:
                print("[INFO] Waiting for detection process to finish...")
                stdout, stderr = self._detection_process.communicate(timeout=10)

                print(f"[INFO] Detection process output:")
                if stdout:
                    print(f"STDOUT:\n{stdout}")
                if stderr:
                    print(f"STDERR:\n{stderr}")

                # Parse JSON result from detect.py (use LAST occurrence for most recent stats)
                json_lines = [line for line in stdout.split('\n') if line.startswith('DETECTION_RESULT_JSON:')]
                if json_lines:
                    try:
                        # Use the last JSON line (most recent stats)
                        last_json_line = json_lines[-1]
                        json_str = last_json_line.replace('DETECTION_RESULT_JSON:', '', 1).strip()
                        detection_result = json.loads(json_str)
                        frames_processed = detection_result.get('frames_processed', 0)
                        frames_received = detection_result.get('frames_received', 0)
                        self._detection_count = detection_result.get('detections_count', 0)
                        total_pigeons = detection_result.get('total_pigeons', 0)
                        duration = detection_result.get('duration_seconds', 0.0)
                        average_fps = detection_result.get('average_fps', 0.0)
                        print(f"[INFO] Parsed JSON result (from {len(json_lines)} updates): {detection_result}")
                    except Exception as e:
                        print(f"[WARNING] Failed to parse JSON: {e}")
                else:
                    print(f"[WARNING] No JSON stats found in output")

            except subprocess.TimeoutExpired:
                # Force kill if doesn't terminate
                print("[WARNING] Detection process didn't terminate, forcing kill...")
                self._detection_process.kill()
                stdout, stderr = self._detection_process.communicate()

            flight_id = self._current_flight_id
            detection_count = self._detection_count

            # Reset state
            self._detection_process = None
            self._current_flight_id = None
            self._detection_count = 0

            print(f"[SUCCESS] Detection stopped")
            print(f"[SUMMARY] Frames received: {frames_received}")
            print(f"[SUMMARY] Frames processed: {frames_processed}")
            print(f"[SUMMARY] Detections: {detection_count}")
            print(f"[SUMMARY] Total pigeons: {total_pigeons}")
            print(f"[SUMMARY] Duration: {duration}s")
            print(f"[SUMMARY] Average FPS: {average_fps}")
            print("=== DETECTION STOPPED ===")

            return {
                "success": True,
                "flight_id": flight_id,
                "frames_received": frames_received,
                "frames_processed": frames_processed,
                "detection_count": detection_count,
                "total_pigeons": total_pigeons,
                "duration_seconds": duration,
                "average_fps": average_fps,
                "message": f"Detection stopped. Processed {frames_processed} frames, found {detection_count} frames with pigeons ({total_pigeons} total pigeons)."
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
