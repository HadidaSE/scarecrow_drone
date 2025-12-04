#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cv2
import sys
import time
import subprocess

print "=== Intel Aero Camera - Take Picture ==="

# Set camera controls using v4l2-ctl before opening with OpenCV
print "Configuring camera settings..."
subprocess.call(['v4l2-ctl', '-d', '/dev/video13', '-c', 'exposure_auto=3'])  # Auto aperture priority
subprocess.call(['v4l2-ctl', '-d', '/dev/video13', '-c', 'exposure_absolute=400'])  # Higher exposure
subprocess.call(['v4l2-ctl', '-d', '/dev/video13', '-c', 'backlight_compensation=4'])  # Max backlight compensation
subprocess.call(['v4l2-ctl', '-d', '/dev/video13', '-c', 'white_balance_temperature_auto=1'])  # Auto WB
subprocess.call(['v4l2-ctl', '-d', '/dev/video13', '-c', 'gain=128'])  # Increase gain
subprocess.call(['v4l2-ctl', '-d', '/dev/video13', '-c', 'brightness=128'])  # Higher brightness

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

print "Camera opened successfully"
print "Letting camera stabilize..."

# Let camera stabilize with new settings
time.sleep(2)

# Capture frame
print "Capturing image..."
ret, frame = camera.read()

if not ret:
    print "ERROR: Failed to capture image"
    camera.release()
    sys.exit(1)

# Remove the artificial brightness boost - let camera settings handle it
import numpy as np

# Generate filename with timestamp
timestamp = time.strftime("%Y%m%d_%H%M%S")
filename = "/home/root/photo_%s.jpg" % timestamp

# Save image with high quality
cv2.imwrite(filename, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])

# Get image dimensions
height, width = frame.shape[:2]

camera.release()

print "\n=== SUCCESS ==="
print "Image saved: %s" % filename
print "Resolution: %dx%d" % (width, height)
print "Done!"
