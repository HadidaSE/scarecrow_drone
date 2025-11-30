#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cv2
import time
import sys

print "=== Intel Aero Camera Test ==="

# Use GStreamer pipeline for Intel RealSense camera
gst_pipeline = (
    "v4l2src device=/dev/video13 ! "
    "video/x-raw,width=640,height=480,framerate=30/1 ! "
    "videoconvert ! "
    "appsink"
)

print "Opening camera with GStreamer..."
camera = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)

if not camera.isOpened():
    print "ERROR: Cannot open camera with GStreamer pipeline"
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
cv2.imwrite('/home/root/camera_frame.jpg', frame)
print "Saved test frame to: /home/root/camera_frame.jpg"

print "\n=== CAMERA INFO ==="
print "Device: /dev/video13 (Intel RealSense)"
print "Resolution: %dx%d" % (width, height)

# Record a short test video
print "\nRecording 5 second test video..."

# Use MJPG codec which is more compatible
fourcc = cv2.VideoWriter_fourcc(*'MJPG')
# Match the recording fps to capture fps (30 instead of 20)
out = cv2.VideoWriter('/home/root/camera_test.avi', fourcc, 30.0, (width, height))

if not out.isOpened():
    print "ERROR: Failed to open video writer"
    camera.release()
    sys.exit(1)

start_time = time.time()
frame_count = 0

try:
    while (time.time() - start_time) < 5:
        ret, frame = camera.read()
        if ret:
            # Verify frame has correct dimensions
            if frame.shape[0] == height and frame.shape[1] == width:
                out.write(frame)
                frame_count += 1
                if frame_count % 30 == 0:
                    print "Recording... %d seconds" % int(time.time() - start_time)
            else:
                print "WARNING: Frame size mismatch: %dx%d" % (frame.shape[1], frame.shape[0])
        else:
            print "WARNING: Dropped frame"
except Exception as e:
    print "ERROR during recording: %s" % str(e)
finally:
    # Properly release resources - THIS IS CRITICAL
    print "\nReleasing camera and video writer..."
    camera.release()
    out.release()
    cv2.destroyAllWindows()

print "\n=== RESULTS ==="
print "Frames captured: %d" % frame_count
print "Expected frames: ~150 (30 fps x 5 seconds)"
print "Video saved to: /home/root/camera_test.avi"
print "Camera access: SUCCESS"
print "\nDone!"