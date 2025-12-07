
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Altitude Streaming Script for Intel Aero RTF
Continuously streams drone altitude every second in JSON format
Compatible with Python 2.7
Usage: python stream_altitude.py [-d|--debug]
Press Ctrl+C to stop
"""

from dronekit import connect
from pymavlink import mavutil
import json
import time
import sys
import math


# Global debug flag
DEBUG = False


def debug_print(message):
    """Print debug message only if DEBUG is enabled"""
    if DEBUG:
        print "DEBUG: %s" % message


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
    """Get raw altitude from available MAVLink messages"""
    try:
        # Try multiple altitude sources in order of preference
        altitude_sources = [
            ('LOCAL_POSITION_NED', lambda msg: -msg.z),
            ('GLOBAL_POSITION_INT', lambda msg: msg.relative_alt / 1000.0),
            ('ALTITUDE', lambda msg: msg.altitude_relative),
            ('VFR_HUD', lambda msg: msg.alt)
        ]
        
        for msg_type, get_alt in altitude_sources:
            for _ in range(3):
                msg = master.recv_match(type=msg_type, blocking=False, timeout=0.01)
                if msg:
                    alt = get_alt(msg)
                    debug_print("Got altitude from %s: %.3f" % (msg_type, alt))
                    return alt
                    
    except Exception as e:
        debug_print("Error reading altitude: %s" % str(e))
    return None


def get_imu_data(master):
    """Get accelerometer data from IMU"""
    try:
        # Try multiple message types for IMU data
        for msg_type in ['SCALED_IMU2', 'SCALED_IMU', 'RAW_IMU']:
            msg = master.recv_match(type=msg_type, blocking=False, timeout=0.001)
            if msg:
                # Convert from millig to m/s^2
                accel_x = msg.xacc / 1000.0 * 9.8
                accel_y = msg.yacc / 1000.0 * 9.8
                accel_z = msg.zacc / 1000.0 * 9.8
                return accel_x, accel_y, accel_z
    except Exception as e:
        debug_print("Error reading IMU: %s" % str(e))
    return 0.0, 0.0, 9.8  # Default to stationary


def stream_altitude():
    """
    Continuously stream altitude data every second
    """
    vehicle = None
    altitude_filter = AltitudeFilter()

    try:
        # Connect to flight controller
        debug_print("Connecting to flight controller on /dev/ttyS1...")
        vehicle = connect('/dev/ttyS1',
                         wait_ready=False,
                         baud=1500000,
                         heartbeat_timeout=30,
                         source_system=255)

        debug_print("Connected successfully")
        
        # Wait for initial data and clear buffer
        debug_print("Waiting for stable MAVLink connection...")
        time.sleep(2)
        
        # Flush any bad messages from buffer
        debug_print("Clearing message buffer...")
        start_flush = time.time()
        while time.time() - start_flush < 1.0:
            try:
                vehicle._master.recv_match(blocking=False)
            except:
                pass

        # Get drone ID
        drone_id = None
        try:
            drone_id = vehicle._master.target_system
            debug_print("Drone ID = %s" % drone_id)
        except Exception:
            drone_id = "unknown"

        # Initialize altitude filter
        debug_print("Initializing altitude filter...")
        init_count = 0
        for i in range(30):
            raw_alt = get_raw_altitude(vehicle._master)
            accel = get_imu_data(vehicle._master)
            if raw_alt is not None:
                altitude_filter.update(raw_alt, accel[0], accel[1], accel[2])
                init_count += 1
                if init_count >= 5:
                    break
            time.sleep(0.2)
        
        if init_count == 0:
            raise Exception("Failed to initialize altitude - no valid readings")
        
        debug_print("Altitude filter initialized with %d readings" % init_count)
        debug_print("Starting altitude stream (Ctrl+C to stop)...")
        
        if DEBUG:
            print ""

        # Main streaming loop
        consecutive_errors = 0
        while True:
            try:
                # Get current altitude
                raw_alt = get_raw_altitude(vehicle._master)
                accel = get_imu_data(vehicle._master)
                
                if raw_alt is not None:
                    filtered_alt = altitude_filter.update(raw_alt, accel[0], accel[1], accel[2])
                    consecutive_errors = 0  # Reset error counter on success
                else:
                    filtered_alt = altitude_filter.altitude
                    consecutive_errors += 1

                # Check if too many consecutive errors
                if consecutive_errors > 10:
                    raise Exception("Lost connection - no altitude data for 10 seconds")

                # Create altitude data packet
                altitude_data = {
                    "drone_id": drone_id,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                    "altitude_meters": round(filtered_alt, 3),
                    "raw_altitude_meters": round(raw_alt, 3) if raw_alt is not None else None,
                    "vertical_velocity_ms": round(altitude_filter.velocity, 3)
                }

                # Output JSON
                print json.dumps(altitude_data)
                sys.stdout.flush()  # Ensure immediate output

            except Exception as loop_error:
                debug_print("Loop error: %s" % str(loop_error))
                if "Lost connection" in str(loop_error):
                    raise  # Re-raise connection loss

            # Wait 1 second
            time.sleep(1.0)

    except KeyboardInterrupt:
        debug_print("\nStopping altitude stream...")

    except Exception as e:
        error_data = {
            "error": str(e),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        }
        print json.dumps(error_data)

    finally:
        # Close connection
        if vehicle:
            debug_print("Closing connection...")
            vehicle.close()
            debug_print("Connection closed")


if __name__ == "__main__":
    # Parse command line arguments for debug flag
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-d', '--debug', '-debug']:
            DEBUG = True
            debug_print("Debug mode enabled")

    # Start streaming altitude
    stream_altitude()
