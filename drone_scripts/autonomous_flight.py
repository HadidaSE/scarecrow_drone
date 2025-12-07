#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Autonomous Flight Script for Intel Aero RTF
Performs controlled flight to 0.5m altitude, hovers for 5 seconds, then lands
Records complete flight statistics and outputs JSON
Compatible with Python 2.7
"""

from dronekit import connect, VehicleMode
from pymavlink import mavutil
import json
import time
import math
import sys


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
        # Should be ~9.8 m/s^2 if stationary (just gravity)
        if abs(total_accel - 9.8) < 0.5:
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

        # If stationary for 3+ readings, reset drift
        if self.stationary_count >= 3:
            self.altitude = self.altitude * 0.95 + relative_alt * 0.05
            self.velocity = 0.0
        else:
            # Apply complementary filter when moving
            if self.last_update is not None and self.last_raw_alt is not None:
                dt = current_time - self.last_update

                if dt > 0 and dt < 1.0:
                    raw_velocity = (raw_altitude - self.last_raw_alt) / dt

                    if abs(raw_velocity) < 5.0:
                        self.velocity = self.velocity * 0.8 + raw_velocity * 0.2
                        self.altitude += self.velocity * dt
                        self.altitude = self.altitude * 0.9 + relative_alt * 0.1

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
    """Get accelerometer data from IMU"""
    msg = master.recv_match(type='SCALED_IMU2', blocking=False, timeout=0.01)
    if msg:
        # Convert from millig to m/s^2
        accel_x = msg.xacc / 1000.0 * 9.8
        accel_y = msg.yacc / 1000.0 * 9.8
        accel_z = msg.zacc / 1000.0 * 9.8
        return accel_x, accel_y, accel_z
    return 0.0, 0.0, 9.8  # Default to stationary


def get_battery_percentage(vehicle):
    """Get battery percentage from vehicle"""
    try:
        if vehicle.battery:
            # Try to get battery level directly
            if vehicle.battery.level is not None:
                return vehicle.battery.level
            # Fallback: estimate from voltage if available (4S LiPo)
            elif vehicle.battery.voltage is not None and vehicle.battery.voltage < 60:
                voltage = vehicle.battery.voltage
                # 4S LiPo: 16.8V = 100%, 14.0V = 0%
                percentage = ((voltage - 14.0) / (16.8 - 14.0)) * 100
                percentage = max(0, min(100, percentage))
                return int(round(percentage))
    except Exception:
        pass
    return None


def send_ned_velocity(vehicle, velocity_x, velocity_y, velocity_z, duration=1):
    """
    Send velocity command in NED frame (safer than RC override)
    velocity_z: negative = up, positive = down
    """
    msg = vehicle.message_factory.set_position_target_local_ned_encode(
        0,       # time_boot_ms (not used)
        0, 0,    # target system, target component
        mavutil.mavlink.MAV_FRAME_LOCAL_NED,  # frame
        0b0000111111000111,  # type_mask (only speeds enabled)
        0, 0, 0,  # x, y, z positions (not used)
        velocity_x, velocity_y, velocity_z,  # velocities in m/s
        0, 0, 0,  # x, y, z acceleration (not used)
        0, 0)     # yaw, yaw_rate (not used)

    # Send command multiple times for reliability
    for _ in range(int(duration * 10)):
        vehicle.send_mavlink(msg)
        time.sleep(0.1)


def goto_altitude_ned(vehicle, target_altitude, altitude_filter, duration=10):
    """
    Safely reach target altitude using NED velocity commands
    Returns True if successful, False if timeout
    """
    start_time = time.time()
    CLIMB_RATE = 0.3  # m/s - gentle climb rate
    DESCENT_RATE = 0.2  # m/s - gentle descent rate
    ALTITUDE_TOLERANCE = 0.05  # meters

    print "LOG: Moving to altitude %.2fm..." % target_altitude

    while time.time() - start_time < duration:
        # Get current altitude
        raw_alt = get_raw_altitude(vehicle._master)
        accel = get_imu_data(vehicle._master)
        current_alt = altitude_filter.update(raw_alt, accel[0], accel[1], accel[2])

        altitude_error = target_altitude - current_alt

        # Check if reached target
        if abs(altitude_error) < ALTITUDE_TOLERANCE:
            print "LOG: Target altitude reached: %.3fm" % current_alt
            # Hover in place
            send_ned_velocity(vehicle, 0, 0, 0, duration=0.5)
            return True

        # Calculate velocity command (negative z = up in NED)
        if altitude_error > 0:
            # Need to climb
            velocity_z = -min(CLIMB_RATE, abs(altitude_error))
        else:
            # Need to descend
            velocity_z = min(DESCENT_RATE, abs(altitude_error))

        # Send velocity command
        send_ned_velocity(vehicle, 0, 0, velocity_z, duration=0.1)

        print "LOG: Alt=%.3fm | Target=%.2fm | Error=%.3fm | Vz=%.2fm/s" % (
            current_alt, target_altitude, altitude_error, -velocity_z)

    print "WARNING: Altitude timeout"
    return False


def autonomous_flight():
    """
    Perform autonomous flight:
    1. Capture initial flight stats
    2. Ascend to 0.5m
    3. Hover for 5 seconds
    4. Descend gently to ground
    5. Capture final stats and output JSON
    """

    # Initialize flight stats
    flight_stats = {
        "flight_id": None,
        "drone_id": None,
        "start_time": None,
        "end_time": None,
        "max_altitude": 0.0,
        "start_battery_percentage": None,
        "end_battery_percentage": None,
        "duration": None
    }

    # Flight parameters
    TARGET_ALTITUDE = 0.5  # meters
    HOVER_DURATION = 5.0   # seconds
    ALTITUDE_TOLERANCE = 0.05  # meters

    print "="*60
    print "AUTONOMOUS FLIGHT SCRIPT - Intel Aero RTF"
    print "="*60
    print "Flight Plan:"
    print "  1. Ascend to %.1f meters" % TARGET_ALTITUDE
    print "  2. Hover for %d seconds" % HOVER_DURATION
    print "  3. Descend gently to ground"
    print "  4. Output flight statistics as JSON"
    print "="*60
    print ""

    vehicle = None
    altitude_filter = AltitudeFilter()

    try:
        # Connect to flight controller
        print "LOG: Connecting to flight controller on /dev/ttyS1..."
        vehicle = connect('/dev/ttyS1',
                         wait_ready=False,
                         baud=1500000,
                         heartbeat_timeout=30,
                         source_system=255)

        print "LOG: Connected successfully"
        time.sleep(2)  # Wait for initial data

        # Get drone ID
        try:
            flight_stats["drone_id"] = vehicle._master.target_system
            print "LOG: Drone ID = %s" % flight_stats["drone_id"]
        except Exception:
            flight_stats["drone_id"] = "unknown"

        # Check battery before flight
        battery_pct = get_battery_percentage(vehicle)
        print "LOG: Current battery level: %s%%" % battery_pct

        if battery_pct is not None and battery_pct < 30:
            print "ERROR: Battery too low for safe flight (%s%%). Aborting." % battery_pct
            return flight_stats

        # Pre-flight checks
        print "\nLOG: Performing pre-flight checks..."
        print "LOG: Current mode: %s" % vehicle.mode.name
        print "LOG: Armed status: %s" % vehicle.armed
        print "LOG: Is armable: %s" % vehicle.is_armable

        # Set to GUIDED mode (safer - autopilot maintains stability)
        print "\nLOG: Setting mode to GUIDED..."
        vehicle.mode = VehicleMode("GUIDED")
        time.sleep(1)

        while vehicle.mode.name != "GUIDED":
            print "LOG: Waiting for GUIDED mode..."
            time.sleep(0.5)
        print "LOG: Mode set to GUIDED (autopilot-assisted flight)"

        # Wait for armable
        print "\nLOG: Waiting for vehicle to be armable..."
        while not vehicle.is_armable:
            print "LOG: Vehicle not armable yet, waiting..."
            time.sleep(1)
        print "LOG: Vehicle is armable"

        # Arm the vehicle
        print "\nLOG: Arming motors..."
        vehicle.armed = True

        while not vehicle.armed:
            print "LOG: Waiting for arming..."
            time.sleep(0.5)
        print "LOG: Motors ARMED"

        # Record flight start
        start_timestamp = time.time()
        flight_stats["flight_id"] = int(start_timestamp)
        flight_stats["start_time"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_timestamp))
        flight_stats["start_battery_percentage"] = get_battery_percentage(vehicle)

        print "\n" + "="*60
        print "FLIGHT STARTED"
        print "="*60
        print "Start Time: %s" % flight_stats["start_time"]
        print "Start Battery: %s%%" % flight_stats["start_battery_percentage"]
        print ""

        # Initialize altitude filter
        print "LOG: Initializing altitude filter..."
        for _ in range(10):
            raw_alt = get_raw_altitude(vehicle._master)
            accel = get_imu_data(vehicle._master)
            if raw_alt is not None:
                altitude_filter.update(raw_alt, accel[0], accel[1], accel[2])
            time.sleep(0.1)
        print "LOG: Altitude filter initialized"

        # PHASE 1: ASCEND TO TARGET ALTITUDE
        print "\n" + "-"*60
        print "PHASE 1: ASCENDING TO %.2f METERS" % TARGET_ALTITUDE
        print "-"*60

        max_altitude = 0.0

        # Use DroneKit's safe velocity commands to reach altitude
        success = goto_altitude_ned(vehicle, TARGET_ALTITUDE, altitude_filter, duration=30)

        if not success:
            print "ERROR: Failed to reach target altitude - aborting flight"
            raise Exception("Altitude target failed")

        # Get current altitude for max tracking
        raw_alt = get_raw_altitude(vehicle._master)
        accel = get_imu_data(vehicle._master)
        current_alt = altitude_filter.update(raw_alt, accel[0], accel[1], accel[2])
        max_altitude = max(max_altitude, current_alt)

        # PHASE 2: HOVER AT TARGET ALTITUDE
        print "\n" + "-"*60
        print "PHASE 2: HOVERING FOR %d SECONDS" % HOVER_DURATION
        print "-"*60

        hover_start = time.time()

        while time.time() - hover_start < HOVER_DURATION:
            # Get current altitude
            raw_alt = get_raw_altitude(vehicle._master)
            accel = get_imu_data(vehicle._master)
            current_alt = altitude_filter.update(raw_alt, accel[0], accel[1], accel[2])

            # Update max altitude
            if current_alt > max_altitude:
                max_altitude = current_alt

            # Maintain position using velocity commands (GUIDED mode handles stabilization)
            altitude_error = TARGET_ALTITUDE - current_alt

            # Small velocity correction to maintain altitude
            velocity_z = 0
            if abs(altitude_error) > 0.05:
                velocity_z = max(-0.1, min(0.1, altitude_error * -0.5))

            send_ned_velocity(vehicle, 0, 0, velocity_z, duration=0.1)

            elapsed = time.time() - hover_start
            remaining = HOVER_DURATION - elapsed
            print "LOG: Hovering... Alt=%.3fm | Time remaining=%.1fs" % (current_alt, remaining)

        print "LOG: HOVER COMPLETE"

        # PHASE 3: GENTLE DESCENT
        print "\n" + "-"*60
        print "PHASE 3: DESCENDING TO GROUND"
        print "-"*60

        # Use DroneKit's safe descent to 0m
        success = goto_altitude_ned(vehicle, 0.0, altitude_filter, duration=30)

        if not success:
            print "WARNING: Descent timeout - attempting emergency land"

        # Final landing phase - slow descent to ensure safe touchdown
        print "LOG: Final landing phase..."
        descent_start = time.time()
        LAND_DESCENT_RATE = 0.1  # Very slow final descent

        while time.time() - descent_start < 10:
            raw_alt = get_raw_altitude(vehicle._master)
            accel = get_imu_data(vehicle._master)
            current_alt = altitude_filter.update(raw_alt, accel[0], accel[1], accel[2])

            if current_alt < 0.03 and altitude_filter.stationary_count >= 5:
                print "LOG: LANDED - Vehicle is stationary on ground"
                break

            # Very gentle descent
            send_ned_velocity(vehicle, 0, 0, LAND_DESCENT_RATE, duration=0.1)
            print "LOG: Landing... Alt=%.3fm" % current_alt

        # Stop all movement
        print "\nLOG: Stopping all movement..."
        send_ned_velocity(vehicle, 0, 0, 0, duration=0.5)

        # Disarm
        print "LOG: Disarming motors..."
        vehicle.armed = False

        while vehicle.armed:
            print "LOG: Waiting for disarm..."
            time.sleep(0.5)
        print "LOG: Motors DISARMED"

        # Record flight end
        end_timestamp = time.time()
        flight_stats["end_time"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end_timestamp))
        flight_stats["max_altitude"] = round(max_altitude, 2)
        flight_stats["end_battery_percentage"] = get_battery_percentage(vehicle)
        flight_stats["duration"] = round((end_timestamp - start_timestamp) / 60.0, 2)

        print "\n" + "="*60
        print "FLIGHT COMPLETED SUCCESSFULLY"
        print "="*60
        print "End Time: %s" % flight_stats["end_time"]
        print "End Battery: %s%%" % flight_stats["end_battery_percentage"]
        print "Max Altitude: %.2f meters" % flight_stats["max_altitude"]
        print "Duration: %.2f minutes" % flight_stats["duration"]
        print ""

    except KeyboardInterrupt:
        print "\n\nWARNING: Flight interrupted by user!"
        if vehicle:
            try:
                # Stop all movement
                send_ned_velocity(vehicle, 0, 0, 0, duration=0.5)
                # Switch to LAND mode for safe emergency landing
                vehicle.mode = VehicleMode("LAND")
                time.sleep(2)
                vehicle.armed = False
                print "LOG: Emergency shutdown complete"
            except:
                pass

    except Exception as e:
        print "\n\nERROR: %s" % str(e)
        if vehicle:
            try:
                # Stop all movement
                send_ned_velocity(vehicle, 0, 0, 0, duration=0.5)
                # Switch to LAND mode for safe emergency landing
                vehicle.mode = VehicleMode("LAND")
                time.sleep(2)
                vehicle.armed = False
                print "LOG: Emergency shutdown complete"
            except:
                pass

    finally:
        # Close connection
        if vehicle:
            print "\nLOG: Closing connection..."
            vehicle.close()
            print "LOG: Connection closed"

    return flight_stats


if __name__ == "__main__":
    # Run autonomous flight
    stats = autonomous_flight()

    # Output final JSON
    print "\n" + "="*60
    print "FLIGHT STATISTICS JSON OUTPUT"
    print "="*60
    print json.dumps(stats, indent=2)
    print "="*60
