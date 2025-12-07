#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Drone Stats Script for Intel Aero RTF
Returns drone_id, battery_percentage, and connected_status in JSON format
Compatible with Python 2.7
Usage: python stats.py [-d|--debug]
"""

from dronekit import connect
import json
import time
import sys

# Global debug flag
DEBUG = False


def debug_print(message):
    """Print debug message only if DEBUG is enabled"""
    if DEBUG:
        print "DEBUG: %s" % message


def get_drone_stats():
    """
    Connects to drone and retrieves stats
    Returns dict with drone_id, battery_percentage, connected_status
    """
    stats = {
        "drone_id": None,
        "battery_percentage": None,
        "connected_status": False
    }

    try:
        # Connect to flight controller
        debug_print("Attempting to connect to /dev/ttyS1...")
        vehicle = connect('/dev/ttyS1',
                         wait_ready=False,
                         baud=1500000,
                         heartbeat_timeout=30,
                         source_system=255)

        # Connection successful
        stats["connected_status"] = True
        debug_print("Connection successful")

        # Wait for data to be received from flight controller
        debug_print("Waiting 1 second for data...")
        time.sleep(1)

        # Get drone ID (using system ID)
        try:
            stats["drone_id"] = vehicle._master.target_system
            debug_print("Drone ID = %s" % stats["drone_id"])
        except Exception as e:
            debug_print("Error getting drone ID: %s" % str(e))
            stats["drone_id"] = "unknown"

        # Get battery percentage
        try:
            debug_print("Checking battery object...")
            debug_print("vehicle.battery = %s" % vehicle.battery)
            if vehicle.battery:
                debug_print("Battery object exists")
                debug_print("battery.level = %s" % vehicle.battery.level)
                debug_print("battery.voltage = %s" % vehicle.battery.voltage)
                debug_print("battery.current = %s" % vehicle.battery.current)

                # Try to get battery level directly
                if vehicle.battery.level is not None:
                    stats["battery_percentage"] = vehicle.battery.level
                    debug_print("Using battery.level = %s" % stats["battery_percentage"])
                # Fallback: estimate from voltage if available
                elif vehicle.battery.voltage is not None and vehicle.battery.voltage < 60:
                    # LiPo battery voltage to percentage estimation (4S battery: 14.0-16.8V)
                    voltage = vehicle.battery.voltage
                    debug_print("Calculating from voltage = %s V" % voltage)
                    # 4S LiPo: 16.8V = 100%, 14.0V = 0%
                    percentage = ((voltage - 14.0) / (16.8 - 14.0)) * 100
                    percentage = max(0, min(100, percentage))  # Clamp between 0-100
                    stats["battery_percentage"] = int(round(percentage))
                    debug_print("Calculated percentage = %s%%" % stats["battery_percentage"])
                else:
                    debug_print("No valid battery data (voltage may be >= 60 or None)")
                    stats["battery_percentage"] = None
            else:
                debug_print("Battery object is None")
                stats["battery_percentage"] = None
        except Exception as e:
            debug_print("Exception getting battery: %s" % str(e))
            stats["battery_percentage"] = None

        # Close connection
        debug_print("Closing connection...")
        vehicle.close()

    except Exception as e:
        # Connection failed
        debug_print("Connection failed: %s" % str(e))
        stats["connected_status"] = False
        stats["drone_id"] = "unknown"
        stats["battery_percentage"] = None

    return stats


if __name__ == "__main__":
    # Parse command line arguments for debug flag
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-d', '--debug', '-debug']:
            DEBUG = True
            debug_print("Debug mode enabled")

    # Get drone stats
    drone_stats = get_drone_stats()

    # Print separator (only in debug mode)
    if DEBUG:
        print "\n=== FINAL JSON OUTPUT ==="
    
    # Print as JSON
    print json.dumps(drone_stats, indent=2)
