#!/usr/bin/env python2.7
"""
Simple altitude test using DroneKit's built-in location property
"""

from dronekit import connect
import time

CONNECTION_STRING = '/dev/ttyS1'
BAUD_RATE = 1500000

print "=" * 50
print "Simple Altitude Test"
print "=" * 50
print "Connecting..."

vehicle = connect(CONNECTION_STRING, baud=BAUD_RATE, wait_ready=False)
print "Connected!"

print "Waiting 3 seconds for data..."
time.sleep(3)

print ""
print "-" * 60
print "Time     | Location Alt | Attitude | Mode"
print "-" * 60

initial_alt = None

try:
    while True:
        # Get location data (uses GPS + baro fusion)
        loc = vehicle.location.global_relative_frame
        loc_alt = loc.alt if loc else None

        # Get attitude
        att = vehicle.attitude
        pitch = att.pitch if att else 0
        roll = att.roll if att else 0

        # Get mode
        mode = vehicle.mode.name if vehicle.mode else "N/A"

        if loc_alt is not None:
            if initial_alt is None:
                initial_alt = loc_alt

            relative = loc_alt - initial_alt

            print "%s | %.2fm (rel: %+.2fm) | P:%.1f R:%.1f | %s" % (
                time.strftime("%H:%M:%S"),
                loc_alt,
                relative,
                pitch * 57.3,  # rad to deg
                roll * 57.3,
                mode
            )
        else:
            print "%s | No location data | %s" % (time.strftime("%H:%M:%S"), mode)

        time.sleep(1)

except KeyboardInterrupt:
    print ""
    print "-" * 60
    print "Test stopped"

vehicle.close()
print "Done"
