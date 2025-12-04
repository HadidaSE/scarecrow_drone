#!/usr/bin/env python
# -*- coding: utf-8 -*-

from dronekit import connect
import time

print "Connecting directly to flight controller on /dev/ttyS1..."

try:
    vehicle = connect('/dev/ttyS1',
                    wait_ready=False,
                    baud=1500000,
                    heartbeat_timeout=10,
                    source_system=255)

    print "Connected! Fetching data..."

    # Only wait for heartbeat, nothing else
    time.sleep(1)

    print "\n=== DRONE INFO ==="
    print "Mode: %s" % vehicle.mode.name
    print "Armed: %s" % vehicle.armed
    print "Battery: %s" % vehicle.battery
    print "GPS: %s" % vehicle.gps_0
    print "Location: %s" %vehicle.location.global_relative_frame
    print "Attitude: %s" % vehicle.attitude
    print "Groundspeed: %s m/s" % vehicle.groundspeed

    vehicle.close()
    print "\nDone!"

except Exception as e:
    print "\nError: %s" % str(e)
    print "Flight controller may not be connected or powered on."