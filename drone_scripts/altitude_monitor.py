#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Altitude Monitoring Script
Reads altitude from drone and sends averaged updates every second
Compatible with Python 2.7
"""

from dronekit import connect
from pymavlink import mavutil
import time
import json


def get_raw_altitude(master):
    """Get raw altitude from LOCAL_POSITION_NED"""
    try:
        msg = master.recv_match(type='LOCAL_POSITION_NED', blocking=False, timeout=0.01)
        if msg:
            return -msg.z  # Negative Z is altitude (NED frame)
    except Exception:
        pass  # Ignore MAVLink parsing errors
    return None


def altitude_monitoring():
    """
    Continuously monitor altitude and send averaged updates every second
    """
    print "Starting altitude monitoring..."

    vehicle = None

    try:
        # Connect to flight controller
        print "Connecting to /dev/ttyS1..."
        vehicle = connect('/dev/ttyS1',
                         wait_ready=False,
                         baud=1500000,
                         heartbeat_timeout=30,
                         source_system=255)

        print "Connected successfully"
        time.sleep(1)

        # Flush any stale messages from the buffer
        print "Flushing message buffer..."
        for _ in range(10):
            try:
                vehicle._master.recv_match(blocking=False, timeout=0.01)
            except Exception:
                pass

        # Initialize tracking variables
        altitude_samples = []
        last_update_time = time.time()
        home_altitude = None
        UPDATE_INTERVAL = 0.2  # Output every 0.2 seconds (5 Hz updates)

        print "Starting altitude stream (5 updates/sec)..."
        print "Press Ctrl+C to stop"
        print ""

        while True:
            current_time = time.time()

            # Get raw altitude reading
            raw_alt = get_raw_altitude(vehicle._master)

            if raw_alt is not None:
                # Set home altitude on first reading
                if home_altitude is None:
                    home_altitude = raw_alt
                    print "Home altitude set: %.3f meters" % home_altitude

                # Calculate relative altitude from home
                relative_alt = raw_alt - home_altitude

                # Add to samples for averaging
                altitude_samples.append(relative_alt)

            # Check if update interval has passed
            if current_time - last_update_time >= UPDATE_INTERVAL:
                if len(altitude_samples) > 0:
                    # Calculate average altitude over the interval
                    avg_altitude = sum(altitude_samples) / float(len(altitude_samples))

                    # Create update message
                    update = {
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(current_time)),
                        "altitude_meters": round(avg_altitude, 3),
                        "samples_count": len(altitude_samples)
                    }

                    # Send update (print as JSON)
                    print json.dumps(update)

                    # Reset for next interval
                    altitude_samples = []
                    last_update_time = current_time

            # High-speed sampling for fast response
            time.sleep(0.02)  # 50Hz sampling rate

    except KeyboardInterrupt:
        print "\nStopping altitude monitoring..."

    except Exception as e:
        print "ERROR: %s" % str(e)

    finally:
        if vehicle:
            print "Closing connection..."
            vehicle.close()
            print "Connection closed"


if __name__ == "__main__":
    altitude_monitoring()
