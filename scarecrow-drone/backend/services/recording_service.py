"""
Recording Service
Manages video recording from RTP stream during flights
"""
import subprocess
import os
from pathlib import Path
from typing import Optional
from datetime import datetime


class RecordingService:
    """Manages video recording process lifecycle"""

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
        self._recording_process: Optional[subprocess.Popen] = None
        self._current_flight_id: Optional[int] = None
        self._video_path: Optional[str] = None

        # Path to recordings directory
        self._project_root = Path(__file__).parent.parent.parent.parent
        self._recordings_dir = self._project_root / "recordings"

        # Create recordings directory if it doesn't exist
        self._recordings_dir.mkdir(exist_ok=True)

    def start_recording(self, flight_id: int, stream_port: int = 5000) -> dict:
        """
        Start recording video from RTP stream

        Args:
            flight_id: Database flight ID to associate recording with
            stream_port: UDP port receiving RTP stream (default 5000)

        Returns:
            dict with success status and video path
        """
        print("\n=== STARTING RECORDING ===")
        print(f"Flight ID: {flight_id}")
        print(f"Stream Port: {stream_port}")

        # Check if process reference exists
        if self._recording_process is not None:
            # Check if process is actually still running
            if self._recording_process.poll() is None:
                print("[ERROR] Recording already running!")
                return {"success": False, "error": "Recording already running"}
            else:
                # Process reference exists but process is dead - clean it up
                print("[WARNING] Found dead recording process, cleaning up...")
                self._recording_process = None
                self._current_flight_id = None
                self._video_path = None

        # Generate video filename with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        video_filename = f"flight_{flight_id}_{timestamp}.mp4"
        self._video_path = str(self._recordings_dir / video_filename)

        print(f"[INFO] Video will be saved to: {self._video_path}")

        try:
            # Detect GStreamer path (use full path if not in PATH)
            import shutil
            gst_exe = shutil.which("gst-launch-1.0")
            if gst_exe is None:
                # Try common Windows installation path
                gst_exe = r"C:\Program Files\GStreamer\1.0\msvc_x86_64\bin\gst-launch-1.0.exe"
                if not os.path.exists(gst_exe):
                    gst_exe = "gst-launch-1.0"  # Fallback to PATH

            # GStreamer command to capture RTP stream and save to file
            # This captures the same stream that detect.py is reading
            gst_command = [
                gst_exe,
                "-e",  # Handle EOS signal properly for clean file closure
                "udpsrc", f"port={stream_port}",
                "!",
                "application/x-rtp,encoding-name=JPEG,payload=26",
                "!",
                "rtpjpegdepay",
                "!",
                "jpegdec",
                "!",
                "videoconvert",
                "!",
                "x264enc", "speed-preset=ultrafast", "tune=zerolatency",
                "!",
                "mp4mux",
                "!",
                "filesink", f"location={self._video_path}"
            ]

            print(f"[INFO] Starting recording subprocess...")
            print(f"[INFO] Command: {' '.join(gst_command)}")

            self._recording_process = subprocess.Popen(
                gst_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            self._current_flight_id = flight_id

            print(f"[SUCCESS] Recording process started with PID: {self._recording_process.pid}")
            print(f"[INFO] Recording to: {video_filename}")
            print("=== RECORDING STARTED ===")

            return {
                "success": True,
                "message": f"Recording started for flight {flight_id}",
                "video_path": self._video_path,
                "pid": self._recording_process.pid
            }

        except FileNotFoundError:
            return {
                "success": False,
                "error": "GStreamer not found. Please install GStreamer on your PC."
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to start recording: {str(e)}"}

    def stop_recording(self) -> dict:
        """
        Stop the recording process

        Returns:
            dict with success status and video path
        """
        print("\n=== STOPPING RECORDING ===")

        if self._recording_process is None:
            print("[WARNING] No recording process running")
            return {"success": False, "error": "No recording process running"}

        try:
            print(f"[INFO] Stopping recording process (PID: {self._recording_process.pid})...")

            # Send SIGINT (Ctrl+C) to GStreamer for clean shutdown
            # This allows GStreamer to finalize the MP4 file properly
            self._recording_process.send_signal(subprocess.signal.SIGINT)

            # Wait for process to finish (with timeout)
            try:
                print("[INFO] Waiting for recording process to finish...")
                stdout, stderr = self._recording_process.communicate(timeout=10)

                if stdout:
                    print(f"[INFO] Recording stdout:\n{stdout}")
                if stderr:
                    print(f"[INFO] Recording stderr:\n{stderr}")

            except subprocess.TimeoutExpired:
                # Force kill if doesn't terminate
                print("[WARNING] Recording process didn't terminate, forcing kill...")
                self._recording_process.kill()
                stdout, stderr = self._recording_process.communicate()

            video_path = self._video_path
            flight_id = self._current_flight_id

            # Check if video file was created and has content
            video_exists = os.path.exists(video_path) if video_path else False
            video_size = os.path.getsize(video_path) if video_exists else 0

            # Reset state
            self._recording_process = None
            self._current_flight_id = None
            self._video_path = None

            print(f"[SUCCESS] Recording stopped")
            if video_exists:
                print(f"[INFO] Video saved: {video_path}")
                print(f"[INFO] File size: {video_size / 1024 / 1024:.2f} MB")
            else:
                print(f"[WARNING] Video file not found or empty")
            print("=== RECORDING STOPPED ===")

            return {
                "success": True,
                "flight_id": flight_id,
                "video_path": video_path,
                "video_exists": video_exists,
                "video_size_mb": round(video_size / 1024 / 1024, 2) if video_exists else 0,
                "message": f"Recording stopped. Video saved to {os.path.basename(video_path)}" if video_exists else "Recording stopped but video file not found"
            }

        except Exception as e:
            self._recording_process = None
            return {"success": False, "error": f"Error stopping recording: {str(e)}"}

    def is_running(self) -> bool:
        """Check if recording is currently running"""
        if self._recording_process is None:
            return False

        # Check if process is still alive
        if self._recording_process.poll() is not None:
            # Process has ended
            self._recording_process = None
            return False

        return True

    def get_status(self) -> dict:
        """Get current recording status"""
        return {
            "running": self.is_running(),
            "flight_id": self._current_flight_id,
            "video_path": self._video_path
        }

    def force_cleanup(self) -> dict:
        """
        Force cleanup of recording process state
        Use this when recording is in bad state
        """
        print("\n=== FORCE CLEANUP RECORDING ===")

        if self._recording_process is not None:
            try:
                # Try to terminate if still running
                if self._recording_process.poll() is None:
                    print(f"[INFO] Killing recording process (PID: {self._recording_process.pid})...")
                    self._recording_process.kill()
                    self._recording_process.wait(timeout=5)
                    print("[INFO] Process killed")
                else:
                    print("[INFO] Process already dead")
            except Exception as e:
                print(f"[WARNING] Error during kill: {e}")

        # Reset all state
        self._recording_process = None
        self._current_flight_id = None
        self._video_path = None

        print("[SUCCESS] Recording state reset")
        print("=== CLEANUP COMPLETE ===")

        return {"success": True, "message": "Recording state reset"}
