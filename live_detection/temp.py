"""
Test GStreamer Video Recording from Drone Stream

Simple script to test recording video from the drone's RTP stream.

Usage:
    python temp.py
"""

import subprocess
import time
from pathlib import Path
from datetime import datetime


class VideoRecorder:
    """Records video from RTP stream using GStreamer."""
    
    def __init__(self, port: int = 5000, duration: int = 20):
        self.port = port
        self.duration = duration
        self.gstreamer_process = None
        self.video_file_path = None
        self.start_time = 0.0
        
    def start_recording(self) -> bool:
        """Start GStreamer pipeline to record video."""
        # Create recordings directory
        recordings_dir = Path("recordings")
        recordings_dir.mkdir(exist_ok=True)
        
        # Generate timestamped filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.video_file_path = recordings_dir / f"flight_{timestamp}.mp4"
        
        print("=" * 60)
        print("VIDEO RECORDER TEST")
        print("=" * 60)
        print(f"Port: {self.port}")
        print(f"Duration: {self.duration} seconds")
        print(f"Output: {self.video_file_path.absolute()}")
        print("=" * 60)
        
        # GStreamer path (known location)
        gst_launch = r"C:\Program Files\GStreamer\1.0\msvc_x86_64\bin\gst-launch-1.0.exe"
        
        if not Path(gst_launch).exists():
            print(f"\nERROR: GStreamer not found at: {gst_launch}")
            return False
        
        # Simple GStreamer pipeline for MP4 recording
        gst_cmd = [
            gst_launch,
            'udpsrc', f'port={self.port}',
            '!', 'application/x-rtp,encoding-name=JPEG,payload=26',
            '!', 'rtpjpegdepay',
            '!', 'jpegdec',
            '!', 'videoconvert',
            '!', 'x264enc', 'speed-preset=ultrafast', 'tune=zerolatency',
            '!', 'mp4mux',
            '!', 'filesink', f'location={self.video_file_path}'
        ]
        
        try:
            print("\nStarting GStreamer pipeline...")
            self.gstreamer_process = subprocess.Popen(
                gst_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            time.sleep(1)
            
            # Check if process started successfully
            if self.gstreamer_process.poll() is not None:
                stderr = self.gstreamer_process.stderr.read().decode('utf-8', errors='ignore')
                print(f"ERROR: GStreamer failed to start:\n{stderr}")
                return False
            
            print("Recording started successfully!")
            print("Press Ctrl+C to stop early\n")
            self.start_time = time.time()
            return True
            
        except Exception as e:
            print(f"\nERROR: Failed to start GStreamer: {e}")
            return False
    
    def stop_recording(self) -> None:
        """Stop recording and finalize video file."""
        if not self.gstreamer_process:
            return
        
        print("\n" + "=" * 60)
        print("Stopping recording...")
        
        try:
            # Terminate process
            self.gstreamer_process.terminate()
            
            # Wait for process to finish
            try:
                self.gstreamer_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print("Forcing kill...")
                self.gstreamer_process.kill()
                self.gstreamer_process.wait()
            
            duration = time.time() - self.start_time
            
            print("=" * 60)
            print("RECORDING COMPLETE")
            print("=" * 60)
            print(f"Duration: {duration:.1f} seconds")
            
            if self.video_file_path and self.video_file_path.exists():
                file_size_mb = self.video_file_path.stat().st_size / (1024 * 1024)
                print(f"File: {self.video_file_path.absolute()}")
                print(f"Size: {file_size_mb:.2f} MB")
                print(f"\n✓ Video saved successfully!")
            else:
                print(f"\n✗ Warning: Video file not found")
            
            print("=" * 60)
            
        except Exception as e:
            print(f"Error stopping recording: {e}")
    
    def run(self) -> None:
        """Main run loop."""
        if not self.start_recording():
            return
        
        try:
            # Wait for duration or user interrupt
            while True:
                # Check if process is still running
                if self.gstreamer_process.poll() is not None:
                    print("\nGStreamer process ended unexpectedly")
                    break
                
                # Check if duration reached
                elapsed = time.time() - self.start_time
                if elapsed >= self.duration:
                    print(f"\n✓ Duration reached ({self.duration}s)")
                    break
                
                # Status update every 5 seconds
                if int(elapsed) % 5 == 0 and elapsed > 0:
                    remaining = self.duration - elapsed
                    print(f"Recording... {int(elapsed)}s / {self.duration}s")
                    time.sleep(1)
                else:
                    time.sleep(0.1)
                    
        except KeyboardInterrupt:
            print("\n\nStopped by user")
        finally:
            self.stop_recording()


def main():
    recorder = VideoRecorder(port=5000, duration=20)
    recorder.run()


if __name__ == "__main__":
    main()
