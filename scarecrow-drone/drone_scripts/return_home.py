#!/usr/bin/env python
"""
return_home.py - Return to Launch (RTL) Command
Runs on Intel Aero drone, commands the drone to return to its launch position
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

        # Set mode to RTL (Return to Launch)
        vehicle.mode = VehicleMode("RTL")

        # Wait for mode change
        timeout = 10
        while vehicle.mode.name != "RTL" and timeout > 0:
            time.sleep(0.5)
            timeout -= 0.5

        if vehicle.mode.name == "RTL":
            print(json.dumps({
                "success": True,
                "message": "Return to Launch initiated",
                "mode": vehicle.mode.name
            }))
        else:
            print(json.dumps({
                "success": False,
                "error": "Failed to set RTL mode, current mode: " + vehicle.mode.name
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
