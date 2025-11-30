#!/usr/bin/env python
# -*- coding: utf-8 -*-

from dronekit import connect
import time

print "Connecting directly to flight controller on /dev/ttyS1..."

try:
    # Increased timeouts and added source_system parameter
    vehicle = connect('/dev/ttyS1',
                    wait_ready=False,
                    baud=1500000,
                    heartbeat_timeout=30,
                    source_system=255)

    print "Connected! Waiting for vehicle parameters..."

    # Wait for specific attributes with longer timeout
    vehicle.wait_ready('autopilot_version', timeout=30)

    # Give extra time for all parameters to load
    print "Loading parameters..."
    time.sleep(3)

    print "\n=== DRONE INFO ==="

    # Safely get each attribute with error handling
    try:
        print "Mode: %s" % vehicle.mode.name
    except:
        print "Mode: N/A"

    try:
        print "Armed: %s" % vehicle.armed
    except:
        print "Armed: N/A"

    try:
        print "Battery: %s" % vehicle.battery
    except:
        print "Battery: N/A"

    try:
        print "GPS: %s" % vehicle.gps_0
    except:
        print "GPS: N/A"

    try:
        print "Location: %s" %vehicle.location.global_relative_frame
    except:
        print "Location: N/A"

    try:
        print "Attitude: %s" % vehicle.attitude
    except:
        print "Attitude: N/A"

    try:
        print "Groundspeed: %s m/s" % vehicle.groundspeed
    except:
        print "Groundspeed: N/A"

    vehicle.close()
    print "\nDone!"

except Exception as e:
    print "\nError: %s" % str(e)
    print "Flight controller may not be connected or powered on."