#!/bin/bash
# Drone Video Stream Startup Script
# Streams video from Intel Aero to PC at 192.168.1.2:5000

# Start the stream
gst-launch-1.0 -v \
  v4l2src device=/dev/video13 ! \
  video/x-raw,width=640,height=480,framerate=30/1 ! \
  videoconvert ! \
  jpegenc quality=85 ! \
  rtpjpegpay ! \
  udpsink host=192.168.1.2 port=5000

echo "Stream stopped."
