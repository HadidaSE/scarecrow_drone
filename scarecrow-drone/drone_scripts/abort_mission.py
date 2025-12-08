#!/usr/bin/env python
"""
abort_mission.py - Emergency Abort Command
Runs on Intel Aero drone, immediately stops all tasks and lands
Compatible with Python 2.7
"""
from __future__ import print_function
import json
import sys
import time

try:
    from dronekit import connect, VehicleMode
    DRONEKIT_AVAILABLE = True
except ImportError:
    DRONEKIT_AVAILABLE = False
    print(json.dumps({"success": False, "error": "dronekit not installed"}))
    sys.exit(1)

CONNECTION_STRING = "udp:127.0.0.1:14550"


def main():
    vehicle = None
    try:
        # Connect to vehicle
        vehicle = connect(CONNECTION_STRING, wait_ready=True, timeout=15)

        # Set mode to LAND for immediate landing
        vehicle.mode = VehicleMode("LAND")

        # Wait for mode change
        timeout = 10
        while vehicle.mode.name != "LAND" and timeout > 0:
            time.sleep(0.5)
            timeout -= 0.5

        if vehicle.mode.name == "LAND":
            print(json.dumps({
                "success": True,
                "message": "Emergency landing initiated",
                "mode": vehicle.mode.name
            }))
        else:
            print(json.dumps({
                "success": False,
                "error": "Failed to set LAND mode, current mode: " + vehicle.mode.name
            }))

    except Exception as e:
        print(json.dumps({
            "success": False,
            "error": str(e)
        }))
        sys.exit(1)
    finally:
        if vehicle:
            vehicle.close()


if __name__ == "__main__":
    main()
