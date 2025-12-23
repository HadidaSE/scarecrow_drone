#!/usr/bin/env python
"""
stats.py - Drone Status Reporter
Runs on Intel Aero drone, outputs JSON status to stdout for SSH pipe
Compatible with Python 2.7
"""
from __future__ import print_function
import json
import time
import sys

# Try to import dronekit
try:
    from dronekit import connect, VehicleMode
    DRONEKIT_AVAILABLE = True
except ImportError:
    DRONEKIT_AVAILABLE = False
    print(json.dumps({"error": "dronekit not installed"}))
    sys.stdout.flush()


# Connection string for Intel Aero's flight controller
CONNECTION_STRING = "udp:127.0.0.1:14550"

# Drone ID (can be set per drone for fleet management)
DRONE_ID = 1

# Update interval in seconds
UPDATE_INTERVAL = 1.0


def get_vehicle_status(vehicle):
    """Build status dictionary from vehicle state"""
    return {
        "connected_status": vehicle.is_armable is not None,
        "drone_id": DRONE_ID,
        "mode": vehicle.mode.name if vehicle.mode else "UNKNOWN",
        "armed": vehicle.armed,
        "gps": {
            "fix_type": vehicle.gps_0.fix_type if vehicle.gps_0 else 0,
            "satellites": vehicle.gps_0.satellites_visible if vehicle.gps_0 else 0
        },
        "location": {
            "lat": vehicle.location.global_frame.lat if vehicle.location.global_frame else None,
            "lon": vehicle.location.global_frame.lon if vehicle.location.global_frame else None,
            "alt": vehicle.location.global_frame.alt if vehicle.location.global_frame else None
        },
        "attitude": {
            "roll": vehicle.attitude.roll if vehicle.attitude else 0,
            "pitch": vehicle.attitude.pitch if vehicle.attitude else 0,
            "yaw": vehicle.attitude.yaw if vehicle.attitude else 0
        },
        "groundspeed": vehicle.groundspeed or 0,
        "airspeed": vehicle.airspeed or 0,
        "heading": vehicle.heading or 0
    }


def main():
    """Main loop - connect to vehicle and output status"""
    if not DRONEKIT_AVAILABLE:
        sys.exit(1)

    vehicle = None

    try:
        # Connect to the vehicle
        print(json.dumps({"status": "connecting", "drone_id": DRONE_ID}))
        sys.stdout.flush()

        vehicle = connect(CONNECTION_STRING, wait_ready=True)

        print(json.dumps({"status": "connected", "drone_id": DRONE_ID}))
        sys.stdout.flush()

        # Main status loop
        while True:
            try:
                status = get_vehicle_status(vehicle)
                print(json.dumps(status))
                sys.stdout.flush()
            except Exception as e:
                print(json.dumps({
                    "error": str(e),
                    "connected_status": False,
                    "drone_id": DRONE_ID
                }))
                sys.stdout.flush()

            time.sleep(UPDATE_INTERVAL)

    except KeyboardInterrupt:
        print(json.dumps({"status": "interrupted", "drone_id": DRONE_ID}))
        sys.stdout.flush()
    except Exception as e:
        print(json.dumps({
            "error": "Connection failed: " + str(e),
            "connected_status": False,
            "drone_id": DRONE_ID
        }))
        sys.stdout.flush()
        sys.exit(1)
    finally:
        if vehicle:
            vehicle.close()


if __name__ == "__main__":
    main()
