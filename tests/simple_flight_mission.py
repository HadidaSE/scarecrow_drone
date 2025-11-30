#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
"""
Simple Flight Mission for Intel Aero RTF Drone
Mission: Takeoff to 1 meter, hover, land at position 0
Uses DroneKit for flight control with continuous telemetry
Compatible with Python 2.7 and Yocto factory version
"""

from dronekit import connect, VehicleMode, LocationGlobalRelative
import time
import sys
import threading


# Global flag to control telemetry thread
telemetry_active = True


def print_telemetry(vehicle):
    """Print current telemetry data"""
    print "[TELEMETRY] Mode: %s | Armed: %s | Alt: %.2fm | Battery: %s%%" % (
        vehicle.mode.name,
        vehicle.armed,
        vehicle.location.global_relative_frame.alt or 0.0,
        vehicle.battery.level or 0
    )


def continuous_telemetry(vehicle, interval=1.0):
    """
    Continuously print telemetry in background thread

    Args:
        vehicle: DroneKit vehicle object
        interval: Seconds between telemetry updates
    """
    global telemetry_active

    while telemetry_active:
        try:
            print_telemetry(vehicle)
        except:
            pass
        time.sleep(interval)


def wait_for_arm(vehicle, timeout=30):
    """Wait for vehicle to arm"""
    print "Waiting for arming..."
    start_time = time.time()
    while not vehicle.armed:
        if time.time() - start_time > timeout:
            print "ERROR: Arming timeout!"
            return False
        time.sleep(1)
    print "Vehicle ARMED!"
    return True


def wait_for_altitude(vehicle, target_altitude, tolerance=0.1, timeout=30):
    """
    Wait until vehicle reaches target altitude

    Args:
        vehicle: DroneKit vehicle object
        target_altitude: Target altitude in meters
        tolerance: Acceptable altitude tolerance in meters
        timeout: Maximum wait time in seconds

    Returns:
        True if reached, False if timeout
    """
    print "Waiting to reach %.2fm altitude..." % target_altitude
    start_time = time.time()

    while True:
        current_alt = vehicle.location.global_relative_frame.alt

        if current_alt is None:
            current_alt = 0.0

        print "Target: %.2fm | Current: %.2fm" % (target_altitude, current_alt)

        # Check if we've reached target altitude
        if abs(current_alt - target_altitude) <= tolerance:
            print ">>> REACHED TARGET ALTITUDE: %.2fm <<<" % current_alt
            return True

        # Check timeout
        if time.time() - start_time > timeout:
            print "WARNING: Altitude timeout! Current: %.2fm" % current_alt
            return False

        time.sleep(0.5)


def mission_takeoff_and_land(vehicle, target_altitude=1.0):
    """
    Execute mission: Takeoff to target altitude and land

    Args:
        vehicle: DroneKit vehicle object
        target_altitude: Takeoff altitude in meters (default: 1.0m)
    """
    print "\n" + "="*60
    print "MISSION START: Takeoff to %.2fm and Land" % target_altitude
    print "="*60

    # Step 1: Check initial position and status
    print "\n[STEP 1] Checking initial status..."
    print "Initial Location: %s" % vehicle.location.global_relative_frame
    print "Initial Attitude: %s" % vehicle.attitude
    print "GPS: %s" % vehicle.gps_0

    # Step 2: Set mode to POSCTL (Position Control mode for PX4)
    print "\n[STEP 2] Setting mode to POSCTL (Position Control)..."
    vehicle.mode = VehicleMode("POSCTL")

    # Wait for mode change
    while vehicle.mode.name != "POSCTL":
        print "Waiting for POSCTL mode... Current: %s" % vehicle.mode.name
        time.sleep(1)
    print "Mode set to POSCTL"

    # Step 3: Arm the vehicle
    print "\n[STEP 3] Arming vehicle..."
    vehicle.armed = True

    if not wait_for_arm(vehicle):
        print "ERROR: Failed to arm vehicle"
        return False

    # Step 4: Takeoff
    print "\n[STEP 4] Taking off to %.2fm..." % target_altitude
    vehicle.simple_takeoff(target_altitude)

    # Step 5: Monitor altitude during ascent
    print "\n[STEP 5] Monitoring altitude during ascent..."
    if not wait_for_altitude(vehicle, target_altitude, tolerance=0.15, timeout=30):
        print "WARNING: Did not reach exact target altitude, proceeding..."

    # Step 6: Hover at altitude
    print "\n[STEP 6] Hovering at altitude for 3 seconds..."
    for i in range(3):
        print "Hovering... %d seconds remaining" % (3 - i)
        time.sleep(1)

    # Step 7: Get confirmation we're at 1 meter
    current_alt = vehicle.location.global_relative_frame.alt or 0.0
    print "\n[STEP 7] Altitude confirmation: %.2fm" % current_alt
    if current_alt >= 0.8:
        print ">>> CONFIRMED: Hovering at approximately 1 meter <<<"
    else:
        print "WARNING: Altitude lower than expected"

    # Step 8: Begin landing
    print "\n[STEP 8] Initiating landing sequence..."
    vehicle.mode = VehicleMode("LAND")

    # Wait for mode change
    while vehicle.mode.name != "LAND":
        print "Waiting for LAND mode... Current: %s" % vehicle.mode.name
        time.sleep(1)
    print "Mode set to LAND"

    # Step 9: Monitor descent
    print "\n[STEP 9] Monitoring descent to position 0..."
    while vehicle.armed:
        current_alt = vehicle.location.global_relative_frame.alt or 0.0
        print "Descending... Altitude: %.2fm" % current_alt
        time.sleep(1)

    # Step 10: Mission complete
    print "\n[STEP 10] Vehicle has landed and disarmed"
    print "Final Location: %s" % vehicle.location.global_relative_frame

    print "\n" + "="*60
    print "MISSION COMPLETED SUCCESSFULLY!"
    print "="*60

    return True


if __name__ == "__main__":
    print "="*60
    print "Intel Aero Simple Flight Mission"
    print "="*60
    print "Mission: Takeoff to 1 meter, hover, land safely"
    print "WARNING: Ensure area is clear and drone is ready!"
    print ""
    print "Starting in 3 seconds..."
    time.sleep(3)

    # Connect to vehicle
    print "\nConnecting to flight controller on /dev/ttyS1..."
    try:
        vehicle = connect('/dev/ttyS1',
                        wait_ready=False,
                        baud=1500000,
                        heartbeat_timeout=10,
                        source_system=255)

        print "Connected! System ready."
        time.sleep(1)

    except Exception as e:
        print "ERROR: Could not connect to flight controller"
        print "Details: %s" % str(e)
        sys.exit(1)

    try:
        # Start continuous telemetry in background thread
        print "\nStarting continuous telemetry monitoring..."
        telemetry_thread = threading.Thread(target=continuous_telemetry, args=(vehicle, 1.0))
        telemetry_thread.daemon = True
        telemetry_thread.start()
        time.sleep(1)

        # Execute mission
        success = mission_takeoff_and_land(vehicle, target_altitude=1.0)

        if success:
            print "\nMission executed successfully!"
        else:
            print "\nMission failed!"
            sys.exit(1)

    except KeyboardInterrupt:
        print "\n\nMission interrupted by user!"
        print "Attempting emergency landing..."
        try:
            vehicle.mode = VehicleMode("LAND")
        except:
            pass

    except Exception as e:
        print "\n\nERROR during mission: %s" % str(e)
        print "Attempting emergency landing..."
        try:
            vehicle.mode = VehicleMode("LAND")
        except:
            pass
        sys.exit(1)

    finally:
        # Stop telemetry thread
        try:
            global telemetry_active
            telemetry_active = False
            time.sleep(1.5)  # Give thread time to finish
        except:
            pass

        print "\nClosing connection..."
        vehicle.close()
        print "Connection closed."
