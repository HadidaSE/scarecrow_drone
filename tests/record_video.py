#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cv2
import sys
import time

print "=== Intel Aero Camera - Video Recording ==="

# Use GStreamer pipeline for Intel RealSense camera
gst_pipeline = (
    "v4l2src device=/dev/video13 ! "
    "video/x-raw,width=640,height=480,framerate=30/1 ! "
    "videoconvert ! "
    "appsink"
)

print "Opening camera..."
camera = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)

if not camera.isOpened():
    print "ERROR: Cannot open camera"
    sys.exit(1)

# Test reading a frame to get actual dimensions
print "\nTesting frame capture..."
ret, frame = camera.read()
if not ret:
    print "ERROR: Failed to capture frame"
    camera.release()
    sys.exit(1)

# Get actual frame dimensions
height, width = frame.shape[:2]

print "Frame captured successfully!"
print "\n=== CAMERA INFO ==="
print "Device: /dev/video13 (Intel RealSense)"
print "Resolution: %dx%d" % (width, height)

# Record video
print "\nRecording 10 second video..."

# Use fixed filename
filename = "/home/root/test_vid.avi"

# Use MJPG codec which is more compatible
fourcc = cv2.VideoWriter_fourcc(*'MJPG')
# Match the recording fps to capture fps (30)
out = cv2.VideoWriter(filename, fourcc, 30.0, (width, height))

if not out.isOpened():
    print "ERROR: Failed to open video writer"
    camera.release()
    sys.exit(1)

# Recording parameters
duration = 10  # seconds

start_time = time.time()
frame_count = 0

print "\n=== RECORDING ==="
print "Duration: %d seconds" % duration
print "Press Ctrl+C to stop early"
print "Recording started..."

try:
    while (time.time() - start_time) < duration:
        ret, frame = camera.read()
        if ret:
            # Verify frame has correct dimensions
            if frame.shape[0] == height and frame.shape[1] == width:
                out.write(frame)
                frame_count += 1
                if frame_count % 30 == 0:
                    elapsed = int(time.time() - start_time)
                    print "Recording... %d seconds" % elapsed
            else:
                print "WARNING: Frame size mismatch: %dx%d" % (frame.shape[1], frame.shape[0])
        else:
            print "WARNING: Dropped frame"
except Exception as e:
    print "ERROR during recording: %s" % str(e)
finally:
    # Properly release resources
    print "\nReleasing camera and video writer..."
    camera.release()
    out.release()
    cv2.destroyAllWindows()
    
    actual_duration = time.time() - start_time
    
    print "\n=== RESULTS ==="
    print "Frames captured: %d" % frame_count
    print "Expected frames: ~300 (30 fps x 10 seconds)"
    print "Video saved to: %s" % filename
    print "Duration: %.1f seconds" % actual_duration
    print "Resolution: %dx%d" % (width, height)
    print "\nDone!"
