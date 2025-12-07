#!/usr/bin/env python
# -*- coding: utf-8 -*-
#type:ignore

from dronekit import connect
from pymavlink import mavutil
import time
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


print "Connecting directly to flight controller on /dev/ttyS1..."

try:
    vehicle = connect('/dev/ttyS1',
                    wait_ready=False,
                    baud=1500000,
                    heartbeat_timeout=30,
                    source_system=255)

    print "Connected! Fetching data..."

    # Only wait for heartbeat, nothing else
    time.sleep(1)

    print "\n=== DRONE INFORMATION ==="
    
    # Basic System Info
    print "\n-- System Information --"
    try:
        if hasattr(vehicle.version, 'autopilot') and vehicle.version.autopilot is not None:
            print "Autopilot Type: %s" % vehicle.version.autopilot
        if hasattr(vehicle.version, 'vehicle_type') and vehicle.version.vehicle_type is not None:
            print "Vehicle Type: %s" % vehicle.version.vehicle_type
        if hasattr(vehicle.version, 'major') and vehicle.version.major is not None:
            print "Firmware Version: %s.%s.%s" % (vehicle.version.major, vehicle.version.minor, vehicle.version.patch)
    except Exception as e:
        print "Version info error: %s" % str(e)
    
    # Flight Controller Info
    print "\n-- Flight Controller --"
    try:
        print "System ID: %s" % vehicle._master.target_system
        print "Component ID: %s" % vehicle._master.target_component
    except Exception as e:
        print "Flight controller info error: %s" % str(e)

    # Current State
    print "\n-- Current State --"
    try:
        if hasattr(vehicle, 'mode') and vehicle.mode is not None:
            print "Mode: %s" % vehicle.mode.name
        if hasattr(vehicle, 'armed') and vehicle.armed is not None:
            print "Armed: %s" % vehicle.armed
        if hasattr(vehicle, 'system_status') and vehicle.system_status is not None:
            print "System Status: %s" % vehicle.system_status.state
        if hasattr(vehicle, 'is_armable') and vehicle.is_armable is not None:
            print "Is Armable: %s" % vehicle.is_armable
    except Exception as e:
        print "Current state error: %s" % str(e)
    
    # Battery Information
    print "\n-- Battery --"
    try:
        if vehicle.battery:
            # Only show valid battery values
            if vehicle.battery.voltage is not None and vehicle.battery.voltage < 60:
                print "Battery Voltage: %s V" % vehicle.battery.voltage
            if vehicle.battery.current is not None:
                print "Battery Current: %s A" % vehicle.battery.current
            if vehicle.battery.level is not None:
                print "Battery Level: %s%%" % vehicle.battery.level
            
            # If no valid battery data
            if (vehicle.battery.voltage is None or vehicle.battery.voltage >= 60) and \
               vehicle.battery.current is None and vehicle.battery.level is None:
                print "Battery info not available"
        else:
            print "Battery info not available"
    except Exception as e:
        print "Battery error: %s" % str(e)

    # Last Heartbeat
    print "\n-- Connection --"
    try:
        if hasattr(vehicle, 'last_heartbeat') and vehicle.last_heartbeat is not None:
            print "Last Heartbeat: %s seconds ago" % vehicle.last_heartbeat
    except Exception as e:
        print "Heartbeat error: %s" % str(e)

    vehicle.close()
    print "\n=== Connection Closed ==="

except Exception as e:
    print "\nError: %s" % str(e)
    print "Flight controller may not be connected or powered on."