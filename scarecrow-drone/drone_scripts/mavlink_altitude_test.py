#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
"""
Simple Altitude Monitor for Intel Aero RTF
Displays relative altitude updates every 1 second using internal sensors
Uses AltitudeFilter with MAVLink data (no motor control)
Compatible with Python 2.7 and Yocto factory version
"""

from pymavlink import mavutil
import time
import sys
import math


class AltitudeFilter:
    """Custom altitude filter to stabilize estimates without GPS"""

    def __init__(self):
        self.altitude = 0.0
        self.velocity = 0.0
        self.last_update = None
        self.stationary_count = 0
        self.home_altitude = None
        self.last_raw_alt = None

    def is_stationary(self, accel_x, accel_y, accel_z):
        """Check if drone is stationary based on accelerometer"""
        total_accel = math.sqrt(accel_x**2 + accel_y**2 + accel_z**2)
        # Should be ~9.8-10.0 m/s^2 if stationary (just gravity)
        # HIGHRES_IMU zacc is negative (~-10), so magnitude still ~10
        if abs(total_accel - 9.8) < 1.5:  # Wider tolerance
            return True
        return False

    def update(self, raw_altitude, accel_x, accel_y, accel_z):
        """Update filtered altitude estimate"""
        current_time = time.time()

        # Initialize home altitude on first reading
        if self.home_altitude is None and raw_altitude is not None:
            self.home_altitude = raw_altitude
            self.altitude = 0.0
            self.last_raw_alt = raw_altitude
            self.last_update = current_time
            return 0.0

        if raw_altitude is None:
            return self.altitude

        # Calculate relative altitude from home
        relative_alt = raw_altitude - self.home_altitude

        # Check if stationary
        stationary = self.is_stationary(accel_x, accel_y, accel_z)

        if stationary:
            self.stationary_count += 1
        else:
            self.stationary_count = 0

        # Calculate velocity
        if self.last_update is not None and self.last_raw_alt is not None:
            dt = current_time - self.last_update
            if dt > 0 and dt < 2.0:
                self.velocity = (raw_altitude - self.last_raw_alt) / dt
            else:
                self.velocity = 0.0

        # Just use raw relative altitude directly - no filtering needed
        self.altitude = relative_alt

        self.last_raw_alt = raw_altitude
        self.last_update = current_time

        return self.altitude


def get_raw_altitude(master):
    """Get raw altitude from LOCAL_POSITION_NED"""
    msg = master.recv_match(type='LOCAL_POSITION_NED', blocking=False, timeout=0.01)
    if msg:
        return -msg.z
    return None


def get_imu_data(master):
    """Get accelerometer data from IMU - Intel Aero uses HIGHRES_IMU"""
    msg = master.recv_match(type='HIGHRES_IMU', blocking=False, timeout=0.01)
    if msg:
        # HIGHRES_IMU provides acceleration in m/s^2 directly
        return msg.xacc, msg.yacc, msg.zacc
    return 0.0, 0.0, 9.8  # Default to stationary


def monitor_altitude():
    """Monitor and display altitude every second - NO MOTOR CONTROL"""
    print "="*60
    print "Intel Aero Altitude Monitor (No Motor Control)"
    print "="*60
    print "Lift the drone by hand to see altitude changes"
    print "Press Ctrl+C to stop"
    print ""

    # Connect to flight controller
    print "Connecting to flight controller on /dev/ttyS1..."
    try:
        master = mavutil.mavlink_connection('/dev/ttyS1', baud=1500000)
        master.wait_heartbeat()
        print "Connected! System %u Component %u" % (master.target_system, master.target_component)
    except Exception as e:
        print "ERROR: Could not connect"
        print "Details: %s" % str(e)
        sys.exit(1)

    # Create altitude filter
    alt_filter = AltitudeFilter()

    # Initialize filter with ground readings
    print "\nInitializing altitude filter (2 seconds)..."
    init_start = time.time()
    while (time.time() - init_start) < 2.0:
        raw_alt = get_raw_altitude(master)
        accel_x, accel_y, accel_z = get_imu_data(master)
        if raw_alt is not None:
            alt_filter.update(raw_alt, accel_x, accel_y, accel_z)
        time.sleep(0.05)

    if alt_filter.home_altitude is not None:
        print "Filter initialized. Home altitude set at %.3fm" % alt_filter.home_altitude
    else:
        print "WARNING: Could not initialize home altitude"

    print ""
    print "="*60
    print "Starting altitude monitoring (updates every 1 second)..."
    print "="*60
    print ""
    print "Time      | Filtered Alt | Raw Alt  | Velocity  | Status"
    print "-"*60

    try:
        while True:
            # Poll multiple times within 1 second to catch sporadic messages
            # (same strategy as flight mission - runs at 10Hz internally)
            raw_alt = None
            accel_x, accel_y, accel_z = 0.0, 0.0, 9.8

            # Try to get data over 1 second period (10 attempts at 0.1s intervals)
            for i in range(10):
                temp_alt = get_raw_altitude(master)
                temp_accel = get_imu_data(master)

                if temp_alt is not None:
                    raw_alt = temp_alt
                    accel_x, accel_y, accel_z = temp_accel

                time.sleep(0.1)

            if raw_alt is not None:
                # Update filter and get current altitude
                current_alt = alt_filter.update(raw_alt, accel_x, accel_y, accel_z)

                # Calculate raw relative (same as what filter uses)
                raw_relative = raw_alt - alt_filter.home_altitude if alt_filter.home_altitude else 0

                # Determine status
                status = "STILL " if alt_filter.stationary_count >= 3 else "MOVING"

                # Display altitude information (both columns now show relative altitude)
                print "%s |   %7.3fm   | %7.3fm | %+7.3fm/s | %s" % (
                    time.strftime("%H:%M:%S"),
                    current_alt,
                    raw_relative,
                    alt_filter.velocity,
                    status
                )
            else:
                print "%s | WARNING: No altitude data received" % time.strftime("%H:%M:%S")

    except KeyboardInterrupt:
        print "\n"
        print "="*60
        print "Altitude monitoring stopped by user"
        print "="*60

    except Exception as e:
        print "\nERROR: %s" % str(e)
        sys.exit(1)

    finally:
        print "\nClosing connection..."
        master.close()
        print "Connection closed."


if __name__ == "__main__":
    monitor_altitude()
