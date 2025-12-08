#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
"""
DroneKit Altitude Monitor - Internal Sensors Only
Displays relative altitude updates every 1 second
No motors - safe for hand-lifting the drone to test altitude readings
Uses ONLY DroneKit methods (no direct MAVLink)
Compatible with Python 2.7 and Intel Aero RTF
"""

from dronekit import connect
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


class AltitudeMonitor:
    """Monitors altitude using DroneKit internal sensors"""

    def __init__(self, connection_string='/dev/ttyS1', baud=1500000):
        self.raw_altitude = None
        self.baro_altitude = None  # From VFR_HUD
        self.accel_x = 0.0
        self.accel_y = 0.0
        self.accel_z = 9.8
        self.alt_filter = AltitudeFilter()
        self.imu_updates = 0
        self.alt_updates = 0

        print "=" * 60
        print "DroneKit Altitude Monitor - Internal Sensors Only"
        print "=" * 60
        print "Connecting to drone on %s..." % connection_string

        # Connect to vehicle using DroneKit
        self.vehicle = connect(connection_string, baud=baud, wait_ready=False)

        print "Connected! System %u Component %u" % (
            self.vehicle._master.target_system,
            self.vehicle._master.target_component
        )

        # Register message listeners for sensor data (DroneKit method)
        self.vehicle.add_message_listener('LOCAL_POSITION_NED', self._local_position_callback)
        self.vehicle.add_message_listener('VFR_HUD', self._vfr_hud_callback)
        self.vehicle.add_message_listener('HIGHRES_IMU', self._highres_imu_callback)  # Intel Aero uses HIGHRES_IMU
        self.vehicle.add_message_listener('SCALED_IMU', self._imu_callback)  # Fallback
        self.vehicle.add_message_listener('SCALED_IMU2', self._imu_callback)
        self.vehicle.add_message_listener('RAW_IMU', self._raw_imu_callback)

        print "Sensor listeners registered"
        print "Initializing altitude filter (3 seconds)..."
        time.sleep(3)
        print "IMU updates received: %d, Alt updates: %d" % (self.imu_updates, self.alt_updates)
        print "Ready! Lift the drone to see altitude changes"
        print ""

    def _local_position_callback(self, vehicle, name, message):
        """Callback for barometer altitude data - DroneKit method"""
        # NED frame: z is negative when above home
        self.raw_altitude = -message.z
        self.alt_updates += 1

    def _vfr_hud_callback(self, vehicle, name, message):
        """Callback for VFR HUD data which includes barometric altitude"""
        self.baro_altitude = message.alt

    def _highres_imu_callback(self, vehicle, name, message):
        """Callback for HIGHRES_IMU data - Intel Aero uses this"""
        # HIGHRES_IMU provides acceleration in m/s^2 directly
        self.accel_x = message.xacc
        self.accel_y = message.yacc
        self.accel_z = message.zacc
        self.imu_updates += 1

    def _imu_callback(self, vehicle, name, message):
        """Callback for IMU accelerometer data - DroneKit method"""
        # Convert from millig to m/s^2
        self.accel_x = message.xacc / 1000.0 * 9.8
        self.accel_y = message.yacc / 1000.0 * 9.8
        self.accel_z = message.zacc / 1000.0 * 9.8
        self.imu_updates += 1

    def _raw_imu_callback(self, vehicle, name, message):
        """Callback for RAW IMU data"""
        # RAW_IMU is in raw sensor units, typically millig
        self.accel_x = message.xacc / 1000.0 * 9.8
        self.accel_y = message.yacc / 1000.0 * 9.8
        self.accel_z = message.zacc / 1000.0 * 9.8
        self.imu_updates += 1

    def get_filtered_altitude(self):
        """Get current filtered altitude estimate"""
        return self.alt_filter.update(
            self.raw_altitude,
            self.accel_x,
            self.accel_y,
            self.accel_z
        )

    def monitor(self, update_interval=1.0):
        """Monitor and display altitude updates"""
        print "-" * 75
        print "Time      | Baro Alt | Raw Alt  | Filtered | Accel    | IMU | Status"
        print "-" * 75

        try:
            while True:
                # Get filtered altitude
                filtered_alt = self.get_filtered_altitude()

                # Calculate total acceleration magnitude
                total_accel = math.sqrt(
                    self.accel_x**2 +
                    self.accel_y**2 +
                    self.accel_z**2
                )

                # Display update
                raw_display = "N/A" if self.raw_altitude is None else "%6.2fm" % self.raw_altitude
                baro_display = "N/A" if self.baro_altitude is None else "%6.2fm" % self.baro_altitude
                status = "STILL" if self.alt_filter.stationary_count >= 3 else "MOVING"

                print "%s | %8s | %8s | %7.2fm | %5.2fm/s2 | %3d | %s" % (
                    time.strftime("%H:%M:%S"),
                    baro_display,
                    raw_display,
                    filtered_alt,
                    total_accel,
                    self.imu_updates,
                    status
                )

                time.sleep(update_interval)

        except KeyboardInterrupt:
            print ""
            print "-" * 75
            print "Monitoring stopped by user"

    def close(self):
        """Close connection to vehicle"""
        print "Closing connection..."
        self.vehicle.close()
        print "Connection closed."


if __name__ == "__main__":
    monitor = None

    try:
        # Create altitude monitor using DroneKit
        monitor = AltitudeMonitor(connection_string='/dev/ttyS1', baud=1500000)

        # Start monitoring (updates every 1 second)
        monitor.monitor(update_interval=1.0)

    except Exception as e:
        print "\nERROR: %s" % str(e)

    finally:
        if monitor:
            monitor.close()
