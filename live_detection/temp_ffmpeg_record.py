"""
Test FFmpeg Video Recording from Drone Stream

Simple script to test recording video from the drone's RTP stream using FFmpeg.

Usage:
    python temp_ffmpeg_record.py
"""

import subprocess
import time
from pathlib import Path
from datetime import datetime


class FFmpegVideoRecorder:
    """Records video from RTP stream using FFmpeg."""
    
    def __init__(self, sdp_file: str = "drone.sdp", duration: int = 20):
        self.sdp_file = sdp_file
        self.duration = duration
        self.ffmpeg_process = None
        self.video_file_path = None
        self.start_time = 0.0
        
    def start_recording(self) -> bool:
        """Start FFmpeg to record video."""
        # Create recordings directory
        recordings_dir = Path("recordings")
        recordings_dir.mkdir(exist_ok=True)
        
        # Generate timestamped filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.video_file_path = recordings_dir / f"flight_{timestamp}.mp4"
        
        print("=" * 60)
        print("FFMPEG VIDEO RECORDER TEST")
        print("=" * 60)
        print(f"Stream: {self.sdp_file}")
        print(f"Duration: {self.duration} seconds")
        print(f"Output: {self.video_file_path.absolute()}")
        print("=" * 60)
        
        # FFmpeg command to record from SDP to MP4
        ffmpeg_cmd = [
            'ffmpeg',
            '-hide_banner',
            '-loglevel', 'error',
            '-protocol_whitelist', 'file,udp,rtp',
            '-i', self.sdp_file,
            '-c:v', 'libx264',           # H.264 video codec
            '-preset', 'ultrafast',      # Fast encoding
            '-tune', 'zerolatency',      # Low latency
            '-movflags', '+faststart',   # Optimize for streaming
            '-t', str(self.duration),    # Duration limit
            '-y',                        # Overwrite output file
            str(self.video_file_path)
        ]
        
        try:
            print("\nStarting FFmpeg recording...")
            self.ffmpeg_process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            time.sleep(1)
            
            # Check if process started successfully
            if self.ffmpeg_process.poll() is not None:
                stderr = self.ffmpeg_process.stderr.read().decode('utf-8', errors='ignore')
                print(f"ERROR: FFmpeg failed to start:\n{stderr}")
                return False
            
            print("Recording started successfully!")
            print(f"Recording for {self.duration} seconds...\n")
            self.start_time = time.time()
            return True
            
        except FileNotFoundError:
            print("\nERROR: FFmpeg not found. Please install ffmpeg and add it to PATH.")
            return False
        except Exception as e:
            print(f"\nERROR: Failed to start FFmpeg: {e}")
            return False
    
    def wait_for_completion(self) -> None:
        """Wait for FFmpeg to complete recording."""
        if not self.ffmpeg_process:
            return
        
        try:
            # Monitor process
            while True:
                # Check if process finished
                if self.ffmpeg_process.poll() is not None:
                    break
                
                # Show progress
                elapsed = time.time() - self.start_time
                remaining = max(0, self.duration - elapsed)
                
                if int(elapsed) % 5 == 0 and elapsed > 0:
                    print(f"Recording... {int(elapsed)}s / {self.duration}s (remaining: {int(remaining)}s)")
                    time.sleep(1)
                else:
                    time.sleep(0.1)
                
                # Auto-stop if duration exceeded (safety)
                if elapsed >= self.duration + 5:
                    print("\nDuration exceeded, stopping...")
                    break
                    
        except KeyboardInterrupt:
            print("\n\nStopped by user")
            self.stop_recording()
    
    def stop_recording(self) -> None:
        """Stop recording and finalize video file."""
        if not self.ffmpeg_process:
            return
        
        print("\n" + "=" * 60)
        print("Stopping recording...")
        
        try:
            # Terminate process if still running
            if self.ffmpeg_process.poll() is None:
                self.ffmpeg_process.terminate()
                
                # Wait for graceful shutdown
                try:
                    self.ffmpeg_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print("Forcing kill...")
                    self.ffmpeg_process.kill()
                    self.ffmpeg_process.wait()
            
            duration = time.time() - self.start_time
            
            print("=" * 60)
            print("RECORDING COMPLETE")
            print("=" * 60)
            print(f"Duration: {duration:.1f} seconds")
            
            # Give filesystem time to finalize
            time.sleep(1)
            
            if self.video_file_path and self.video_file_path.exists():
                file_size_mb = self.video_file_path.stat().st_size / (1024 * 1024)
                print(f"File: {self.video_file_path.absolute()}")
                print(f"Size: {file_size_mb:.2f} MB")
                
                if file_size_mb > 0.1:
                    print(f"\n✓ Video saved successfully!")
                    print(f"\nVIDEO_FILE:{self.video_file_path.absolute()}")
                else:
                    print(f"\n✗ Warning: Video file is very small ({file_size_mb:.2f} MB)")
            else:
                print(f"\n✗ Warning: Video file not found at {self.video_file_path}")
            
            print("=" * 60)
            
        except Exception as e:
            print(f"Error stopping recording: {e}")
    
    def run(self) -> None:
        """Main run loop."""
        if not self.start_recording():
            return
        
        self.wait_for_completion()
        self.stop_recording()


def main():
    recorder = FFmpegVideoRecorder(sdp_file="drone.sdp", duration=20)
    recorder.run()


if __name__ == "__main__":
    main()
